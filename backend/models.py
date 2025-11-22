from pydantic import BaseModel
from typing import List, Dict, Optional
from enum import Enum


class Day(str, Enum):
    MONDAY = "Monday"
    TUESDAY = "Tuesday"
    WEDNESDAY = "Wednesday"
    THURSDAY = "Thursday"
    FRIDAY = "Friday"


class ClassInput(BaseModel):
    id: str
    name: str
    teacher: str
    periods_per_week: int
    duration: int = 1  # Number of consecutive periods (1 for regular, 2 for labs)
    color: Optional[str] = None  # Hex color for UI


class TimetableConstraints(BaseModel):
    max_classes_per_day: int = 8
    periods_per_day: int = 8
    days_per_week: List[Day] = [Day.MONDAY, Day.TUESDAY, Day.WEDNESDAY, Day.THURSDAY, Day.FRIDAY]
    lunch_break_period: Optional[int] = 4  # Period number for lunch (None if no fixed lunch)
    prefer_morning: bool = False
    prefer_afternoon: bool = False


class TimeSlot(BaseModel):
    day: Day
    period: int
    class_id: str
    class_name: str
    teacher: str
    color: Optional[str] = None


class GenerateTimetableRequest(BaseModel):
    classes: List[ClassInput]
    constraints: TimetableConstraints


class TimetableResponse(BaseModel):
    schedule: List[TimeSlot]
    success: bool
    message: str
