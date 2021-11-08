from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver import Chrome
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from .constants import DUALIS_URL, STATUSCODE
from argparse import ArgumentParser
from .models import Exam, Course
from typing import List
from .utils import print_error, print_data


def get_parser() -> ArgumentParser:
    parser = ArgumentParser("dualis-scanner-worker")
    parser.add_argument("uname", nargs=1, help="Dualis username.")
    parser.add_argument("pwd", nargs=1, type=str, help="Dualis password.")
    parser.add_argument("--driver", type=str, help="chromedriver dir")
    return parser


def main():
    try:
        argParser = get_parser()
        args = argParser.parse_args()

        print_data(get_courses(args.uname[0], args.pwd[0], args.driver[0]))
    except NoSuchElementException as nse:
        print_error(nse.msg)
        exit(STATUSCODE.CRASH)


def get_grade(string: str) -> float:
    grade = -1
    try:
        grade = float(string)
    except ValueError:
        pass
    return grade


def get_courses(uname: str, pwd: str, driver_dir: str = None) -> List[Course]:
    options = Options()
    options.headless = True

    if driver_dir is None:
        driver_dir = "/usr/local/bin/chromedriver"
    driver = Chrome(executable_path=driver_dir, options=options)
    driver.implicitly_wait(1)
    driver.get(DUALIS_URL)

    driver.find_element(By.ID, "field_user").send_keys(uname)
    driver.find_element(By.ID, "field_pass").send_keys(pwd)
    driver.find_element(By.ID, "logIn_btn").click()

    try:
        if driver.find_element(By.XPATH, "/html/body/div[3]/div[3]/div[2]/div[2]/h1").text == "Benutzername oder Passwort falsch":
            print("ERR: Invalid Login.")
            exit(-1)
    except NoSuchElementException:
        pass

    driver.find_element(By.ID, "link000307").click()

    main_window = driver.window_handles[0]

    courses = list()
    for semester in driver.find_element(By.ID, "semester").find_elements(By.TAG_NAME, "option"):
        semester.click()

        for course in driver.find_elements(By.XPATH, "/html/body/div[3]/div[3]/div[2]/div[2]/div/table/tbody/tr")[0:-1]:
            course_data = course.find_elements(By.TAG_NAME, "td")
            course_data[5].click()

            if len(driver.window_handles) == 1:
                pass #todo error, window didn't open in time. maybe wait some more?

            driver.switch_to.window(driver.window_handles[1])

            exams = list()
            for exam in driver.find_elements(By.XPATH, "/html/body/div/form/table[1]/tbody/tr[count(./td) = 6]"):
                exam_data = exam.find_elements(By.TAG_NAME, "td")

                #todo attemptnum
                exams.append(Exam(1, exam_data[0].text, exam_data[1].text, exam_data[2].text, get_grade(exam_data[3].text)))

            courses.append(Course(course_data[0].text, course_data[1].text, get_grade(course_data[2].text), get_grade(course_data[3].text), exams))

            driver.close()
            driver.switch_to.window(main_window)

    driver.close()
    driver.quit()

    return courses
