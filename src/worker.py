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
from time import sleep
from enum import Enum
from json import dumps
from sys import stderr
from os import mkdir
from os.path import isdir


UNAME_VAR_NAME = "uname"
PWD_VAR_NAME = "pwd"


class STATUSCODE(Enum):
    OK = 0
    INVALID_LOGIN = -1
    CRASH = -2


def doErrorExit(code: STATUSCODE, msg: str = None):
    res = {
        "exitCode": code.value
    }
    if msg is not None:
        res["message"] = msg
    print(dumps(res), file=stderr)
    exit(code.value)


def get_parser() -> ArgumentParser:
    parser = ArgumentParser("dualis-scanner-worker")
    parser.add_argument(UNAME_VAR_NAME, nargs=1, help="Username for dualis login.")
    parser.add_argument(PWD_VAR_NAME, nargs=1, type=str, help="Password for dualis login.")
    parser.add_argument("--driver", type=str, help="The dir to find the chromedriver executable at.")
    parser.add_argument("--logDir", type=str, help="The dir to which logs are written.")
    parser.add_argument("-v", action="store_true", help="Set to enable verbose logging.")
    parser.add_argument("--dry", action="store_true", help="Set if you dont want to return any data.")
    parser.add_argument("--windowTries", type=int, default=3, help="How many times you'd like for the scanner to retry opening a window.")
    parser.add_argument("--windowCheckWait", type=float, default=1, help = "Amount of seconds the scanner should wait until trying to a open window again.")
    parser.add_argument("--url", type=str, default="https://dualis.dhbw.de/", help="The dualis url to open.")
    parser.add_argument("--implicitWait", type=float, default=0.1, help="How long the driver should wait for contents to appear.")
    return parser


def main():
    argParser = get_parser()
    args = argParser.parse_args()

    if args.v:
        level = INFO
    else:
        level = WARN

    if args.logDir is not None:
        if not isdir(args.logDir):
            mkdir(args.logDir)

        #todo logfolder should contain useruid at some point
        basicConfig(level=level, filename=f"{args.logDir}/{datetime.now().strftime('%Y%m%d-%H%M%S')}.log")
    else:
        basicConfig(level=level)

    args_dict = dict(vars(args))
    del args_dict[UNAME_VAR_NAME]
    del args_dict[PWD_VAR_NAME]
    info(f"Using args: {args_dict}")

    try:
        data = get_courses(args)
        if not args.dry:
            print(dumps([x.toDict() for x in data]))
    except NoSuchElementException as nse:
        exception(nse)
        doErrorExit(STATUSCODE.CRASH)

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
    driver.implicitly_wait(args.implicitWait)

    i = 0
    pageOpened = False
    while i < args.windowTries:
        info(f"Starting attempt {i} of opening the main page.")
        driver.get(args.url)
        sleep(args.windowCheckWait)

        try:
            driver.find_element(By.ID, "field_user").send_keys(args.uname[0])
            pageOpened = True
            break
        except NoSuchElementException:
            pass

        i += 1
    retries = i
    failures = 0

    if not pageOpened:
        msg = f"Dualis main page didn't open in {args.windowCheckWait} seconds during {args.windowTries} attempts."
        error(msg)
        doErrorExit(STATUSCODE.CRASH, msg)

    driver.find_element(By.ID, "field_pass").send_keys(args.pwd[0])
    driver.find_element(By.ID, "logIn_btn").click()

    try:
        if driver.find_element(By.XPATH, "/html/body/div[3]/div[3]/div[2]/div[2]/h1").text == "Benutzername oder Passwort falsch":
            error("Login failed.")
            doErrorExit(STATUSCODE.INVALID_LOGIN)
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
                sleep(args.windowCheckWait)

                i += 1
                if len(driver.window_handles) != 1:
                    break

            retries += i

            if len(driver.window_handles) == 1:
                error(f"Window for course {course.ID} did not open after {args.WindowCheckWait} seconds over {args.windowTries} attempts.")
                failures += 1
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
    info(f"Retries: {retries}")
    info(f"Failures: {failures}")

    driver.close()
    driver.quit()

    return courses


if __name__ == "__main__":
    main()