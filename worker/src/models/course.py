from typing import List
from .exam import Exam
from enum import Enum


class CourseCompletion(Enum):
    Failed = -1,
    Unknown = 0,
    Passed = 1


class Course:
    def __init__(self, id: str, name: str, grade: float, credits: float, passed: CourseCompletion, exams: List[Exam]):
        self.ID = id
        self.Name = name
        self.Grade = grade
        self.Credits = credits
        self.Passed = passed
        self.Exams = exams
