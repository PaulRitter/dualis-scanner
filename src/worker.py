from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver import Chrome
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from argparse import ArgumentParser
from .models import Exam, Course
from typing import List
from .models.course import CourseCompletion
from logging import basicConfig, info, exception, error, INFO, WARN
from datetime import datetime
from time import time, sleep
from enum import Enum
from json import dumps


class STATUSCODE(Enum):
    OK = 0
    INVALID_LOGIN = -1
    CRASH = -2


def get_parser() -> ArgumentParser:
    parser = ArgumentParser("dualis-scanner-worker")
    parser.add_argument("uname", nargs=1, help="Username for dualis login.")
    parser.add_argument("pwd", nargs=1, type=str, help="Password for dualis login.")
    parser.add_argument("--driver", type=str, help="The dir to find the chromedriver executable at.")
    parser.add_argument("--logDir", type=str, help="The dir to which logs are written.")
    parser.add_argument("-v", action="store_true", help="Set to enable verbose logging.")
    parser.add_argument("--dry", action="store_true", help="Set if you dont want to return any data.")
    parser.add_argument("--windowTimeout", type=int, default=10, help="How much time you'd like for the scanner to wait for a window to open on each attempt.")
    parser.add_argument("--windowTries", type=int, default=3, help="How many times you'd like for the scanner to retry opening a window.")
    parser.add_argument("--windowCheckWait", type=float, default=0.25, help = "Amount of seconds the scanner should wait until trying to check for an open window again. Cannot be bigger than the windowtimeout value.")
    parser.add_argument("--url", type=str, default="https://dualis.dhbw.de/", help="The dualis url to open.")
    return parser


def main():
    argParser = get_parser()
    args = argParser.parse_args()

    if args.windowCheckWait > args.windowTimeout:
        error("windowCheckWait is larger than windowTimeout.")
        exit(STATUSCODE.CRASH.value)

    if args.v:
        level = INFO
    else:
        level = WARN

    if args.logDir is not None:
        #todo logfolder should contain useruid at some point
        basicConfig(level=level, filename=f"{args.logDir}/{datetime.now().strftime('%Y%m%d-%H%M%S')}.log")
    else:
        basicConfig(level=level)

    try:
        data = get_courses(args)
        if not args.dry:
            print(dumps([x.toDict() for x in data]))
    except NoSuchElementException as nse:
        exception(nse)
        exit(STATUSCODE.CRASH.value)

    exit(STATUSCODE.OK.value)


def get_grade(string: str) -> float:
    grade = -1
    try:
        grade = float(string)
    except ValueError:
        pass
    return grade


def get_courses(args) -> List[Course]:
    info("Getting courses")
    options = Options()
    options.headless = True

    driver_dir = "/usr/local/bin/chromedriver"
    if args.driver is not None:
        driver_dir = args.driver
    info(f"Using driverdir: {driver_dir}")
    driver = Chrome(executable_path=driver_dir, options=options)
    driver.implicitly_wait(1)

    i = 0
    pageOpened = False
    while i < args.windowTries:
        info(f"Starting attempt {i} of opening the main page.")
        driver.get(args.url)

        timeout = time()+args.windowTimeout
        while time() < timeout:
            try:
                driver.find_element(By.ID, "field_user").send_keys(args.uname[0])
                pageOpened = True
                break
            except NoSuchElementException:
                sleep(args.windowCheckWait)

        i += 1
        if pageOpened:
            break

    if not pageOpened:
        error(f"Dualis main page didn't open in {args.windowTimeout} seconds during {args.windowTries} attempts.")
        exit(STATUSCODE.CRASH.value)

    driver.find_element(By.ID, "field_pass").send_keys(args.pwd[0])
    driver.find_element(By.ID, "logIn_btn").click()

    try:
        if driver.find_element(By.XPATH, "/html/body/div[3]/div[3]/div[2]/div[2]/h1").text == "Benutzername oder Passwort falsch":
            error("Login failed.")
            exit(STATUSCODE.INVALID_LOGIN.value)
    except NoSuchElementException:
        pass

    info("Logged in.")
    driver.find_element(By.ID, "link000307").click()
    main_window = driver.window_handles[0]

    courses = list()
    semester_len = len(driver.find_element(By.ID, "semester").find_elements(By.TAG_NAME, "option"))

    for semester_idx in range(semester_len):
        semester = driver.find_element(By.ID, "semester").find_elements(By.TAG_NAME, "option")[semester_idx]
        info(f"Selecting semester {semester.text}.")
        semester.click()

        for course in driver.find_elements(By.XPATH, "/html/body/div[3]/div[3]/div[2]/div[2]/div/table/tbody/tr")[:-1]:
            course_data = course.find_elements(By.TAG_NAME, "td")
            completion = CourseCompletion.Unknown
            if course_data[4].text != "":
                if course_data[4].text == "bestanden":
                    completion = CourseCompletion.Passed
                else:
                    completion = CourseCompletion.Failed
            course = Course(course_data[0].text, course_data[1].text, get_grade(course_data[2].text), get_grade(course_data[3].text), completion, [])
            info(f"Parsing course {course_data[0].text}")

            i = 0
            while i < args.windowTries and len(driver.window_handles) == 1:
                info(f"Starting attempt {i} on opening window for course {course.ID}.")
                course_data[5].click()

                timeout = time()+args.windowTimeout
                while time() < timeout and len(driver.window_handles) == 1:
                    sleep(args.windowCheckWait)
                i += 1
                if len(driver.window_handles) != 1:
                    break

            if len(driver.window_handles) == 1:
                error(f"Window for course {course.ID} did not open after {args.windowTimeout} seconds over {args.windowTries} attempts.")
                continue

            driver.switch_to.window(driver.window_handles[1])

            info("Parsing exams.")
            exams = list()
            for exam in driver.find_elements(By.XPATH, "/html/body/div/form/table[1]/tbody/tr[count(./td) = 6]")[:-1]:
                exam_data = exam.find_elements(By.TAG_NAME, "td")

                #todo attemptnum
                exams.append(Exam(1, exam_data[0].text, exam_data[1].text, exam_data[2].text, get_grade(exam_data[3].text)))

            course.Exams = exams
            courses.append(course)

            info("Finished course. Closing window.")
            driver.close()
            driver.switch_to.window(main_window)

    info("Successfully parsed all exams. Shutting down driver.")

    driver.close()
    driver.quit()

    return courses


if __name__ == "__main__":
    main()