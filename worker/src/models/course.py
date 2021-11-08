from typing import List
from .exam import Exam


class Course:
    def __init__(self, id: str, name: str, grade: float, credits: float, passed: bool, exams: List[Exam]):
        self.ID = id
        self.Name = name
        self.Grade = grade
        self.Credits = credits
        self.Passed = passed
        self.Exams = exams
