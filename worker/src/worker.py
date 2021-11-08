from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver import Chrome
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from .constants import DUALIS_URL, STATUSCODE, WINDOWOPEN_TIMEOUT
from argparse import ArgumentParser
from .models import Exam, Course
from typing import List
from .models.course import CourseCompletion
from logging import basicConfig, debug, exception, error, warn, DEBUG, WARN
from datetime import datetime
from time import time, sleep


def get_parser() -> ArgumentParser:
    parser = ArgumentParser("dualis-scanner-worker")
    parser.add_argument("uname", nargs=1, help="Dualis username.")
    parser.add_argument("pwd", nargs=1, type=str, help="Dualis password.")
    parser.add_argument("--driver", type=str, help="chromedriver dir")
    parser.add_argument("--logdir", type=str, help="log dir")
    parser.add_argument("-v", action="store_true", help="verbose logging")
    parser.add_argument("--dry", action="store_true", help="set if you dont want to return any data")
    return parser


def main():
    argParser = get_parser()
    args = argParser.parse_args()

    if args.v:
        level = DEBUG
    else:
        level = WARN

    if args.logdir is not None:
        #todo logfolder should contain useruid at some point
        basicConfig(level=level, filename=f"{args.logdir}/{datetime.now().strftime('%Y%m%d-%H%M%S')}.log")
    else:
        basicConfig(level=level)

    try:
        data = get_courses(args.uname[0], args.pwd[0], args.driver)
        if not args.dry:
            print([x.toDict() for x in data])
    except NoSuchElementException as nse:
        exception(nse)
        exit(STATUSCODE.CRASH)


def get_grade(string: str) -> float:
    grade = -1
    try:
        grade = float(string)
    except ValueError:
        pass
    return grade


def get_courses(uname: str, pwd: str, driver_dir: str = None) -> List[Course]:
    debug("Getting courses")
    options = Options()
    options.headless = True

    if driver_dir is None:
        driver_dir = "/usr/local/bin/chromedriver"
    debug(f"Using driverdir: {driver_dir}")
    driver = Chrome(executable_path=driver_dir, options=options)
    driver.implicitly_wait(1)
    driver.get(DUALIS_URL)

    debug("Logging in...")
    timeout = time() + WINDOWOPEN_TIMEOUT
    pageOpened = False
    while time() < timeout:
        try:
            driver.find_element(By.ID, "field_user").send_keys(uname)
            pageOpened = True
            break
        except NoSuchElementException:
            sleep(0.25)

    if not pageOpened:
        error(f"Dualis main page didn't open in {WINDOWOPEN_TIMEOUT} seconds.")
        exit(STATUSCODE.CRASH)
    else:
        debug(f"Took dualis {WINDOWOPEN_TIMEOUT - timeout - time()} seconds to open... yeez.")

    driver.find_element(By.ID, "field_pass").send_keys(pwd)
    driver.find_element(By.ID, "logIn_btn").click()

    try:
        if driver.find_element(By.XPATH, "/html/body/div[3]/div[3]/div[2]/div[2]/h1").text == "Benutzername oder Passwort falsch":
            error("Login failed.")
            exit(STATUSCODE.INVALID_LOGIN)
    except NoSuchElementException:
        pass

    debug("Logged in.")
    driver.find_element(By.ID, "link000307").click()
    main_window = driver.window_handles[0]

    courses = list()
    semester_len = len(driver.find_element(By.ID, "semester").find_elements(By.TAG_NAME, "option"))

    for semester_idx in range(semester_len):
        semester = driver.find_element(By.ID, "semester").find_elements(By.TAG_NAME, "option")[semester_idx]
        debug(f"Selecting semester {semester.text}.")
        semester.click()

        for course in driver.find_elements(By.XPATH, "/html/body/div[3]/div[3]/div[2]/div[2]/div/table/tbody/tr")[0:-1]:
            course_data = course.find_elements(By.TAG_NAME, "td")
            completion = CourseCompletion.Unknown
            if course_data[4].text != "":
                if course_data[4].text == "bestanden":
                    completion = CourseCompletion.Passed
                else:
                    completion = CourseCompletion.Failed
            course = Course(course_data[0].text, course_data[1].text, get_grade(course_data[2].text), get_grade(course_data[3].text), completion, [])
            debug(f"Parsing course {course_data[0].text}")
            course_data[5].click()

            timeout = time()+WINDOWOPEN_TIMEOUT
            while time() < timeout and len(driver.window_handles) == 1:
                sleep(0.25)

            if len(driver.window_handles) == 1:
                error(f"Window for course {course_data[0].text} did not open after {WINDOWOPEN_TIMEOUT} seconds.")
                continue

            driver.switch_to.window(driver.window_handles[1])

            debug("Parsing exams.")
            exams = list()
            for exam in driver.find_elements(By.XPATH, "/html/body/div/form/table[1]/tbody/tr[count(./td) = 6]"):
                exam_data = exam.find_elements(By.TAG_NAME, "td")

                #todo attemptnum
                exams.append(Exam(1, exam_data[0].text, exam_data[1].text, exam_data[2].text, get_grade(exam_data[3].text)))

            course.Exams = exams
            courses.append(course)

            debug("Finished course. Closing window.")
            driver.close()
            driver.switch_to.window(main_window)

    debug("Successfully parsed all exams. Shutting down driver.")

    driver.close()
    driver.quit()

    return courses
