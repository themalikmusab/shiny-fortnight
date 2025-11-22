from pydantic import BaseModel, Field, field_validator, model_validator
from typing import List, Optional
from enum import Enum


class Day(str, Enum):
    """Enum representing days of the week"""
    MONDAY = "Monday"
    TUESDAY = "Tuesday"
    WEDNESDAY = "Wednesday"
    THURSDAY = "Thursday"
    FRIDAY = "Friday"


class ClassInput(BaseModel):
    """Model for class input with comprehensive validation"""
    id: str = Field(..., min_length=1, description="Unique identifier for the class")
    name: str = Field(..., min_length=1, max_length=100, description="Name of the class")
    teacher: str = Field(..., min_length=1, max_length=100, description="Name of the teacher")
    periods_per_week: int = Field(..., ge=1, le=40, description="Number of periods per week (1-40)")
    duration: int = Field(default=1, ge=1, le=4, description="Duration in consecutive periods (1-4)")
    color: Optional[str] = Field(default=None, pattern="^#[0-9A-Fa-f]{6}$", description="Hex color code")

    @field_validator('name', 'teacher')
    @classmethod
    def validate_not_empty(cls, v: str) -> str:
        """Ensure name and teacher are not just whitespace"""
        if not v or not v.strip():
            raise ValueError('Field cannot be empty or whitespace')
        return v.strip()

    @field_validator('id')
    @classmethod
    def validate_id(cls, v: str) -> str:
        """Ensure ID is valid"""
        if not v or not v.strip():
            raise ValueError('ID cannot be empty')
        return v.strip()


class TimetableConstraints(BaseModel):
    """Model for timetable constraints with validation"""
    max_classes_per_day: int = Field(default=8, ge=1, le=12, description="Maximum classes per day")
    periods_per_day: int = Field(default=8, ge=4, le=12, description="Number of periods per day (4-12)")
    days_per_week: List[Day] = Field(
        default=[Day.MONDAY, Day.TUESDAY, Day.WEDNESDAY, Day.THURSDAY, Day.FRIDAY],
        min_length=1,
        max_length=7,
        description="Days of the week to schedule"
    )
    lunch_break_period: Optional[int] = Field(default=4, ge=1, le=12, description="Period number for lunch break")
    prefer_morning: bool = Field(default=False, description="Prefer morning time slots")
    prefer_afternoon: bool = Field(default=False, description="Prefer afternoon time slots")

    @model_validator(mode='after')
    def validate_constraints(self):
        """Cross-field validation"""
        # Ensure lunch break is within periods_per_day
        if self.lunch_break_period is not None:
            if self.lunch_break_period > self.periods_per_day:
                raise ValueError(
                    f'Lunch break period ({self.lunch_break_period}) cannot exceed periods per day ({self.periods_per_day})'
                )
            if self.lunch_break_period < 1:
                raise ValueError('Lunch break period must be at least 1')

        # Ensure max_classes_per_day doesn't exceed periods_per_day
        if self.max_classes_per_day > self.periods_per_day:
            # Adjust to periods_per_day if lunch break exists
            periods_available = self.periods_per_day - (1 if self.lunch_break_period else 0)
            self.max_classes_per_day = min(self.max_classes_per_day, periods_available)

        # Ensure preferences are mutually exclusive (both can be False)
        if self.prefer_morning and self.prefer_afternoon:
            raise ValueError('Cannot prefer both morning and afternoon - choose one or neither')

        return self


class TimeSlot(BaseModel):
    """Model for a scheduled time slot"""
    day: Day
    period: int = Field(..., ge=1, description="Period number")
    class_id: str = Field(..., min_length=1)
    class_name: str = Field(..., min_length=1)
    teacher: str = Field(..., min_length=1)
    color: Optional[str] = Field(default=None, pattern="^#[0-9A-Fa-f]{6}$")


class GenerateTimetableRequest(BaseModel):
    """Request model for timetable generation"""
    classes: List[ClassInput] = Field(..., min_length=1, description="List of classes to schedule")
    constraints: TimetableConstraints

    @model_validator(mode='after')
    def validate_request(self):
        """Validate the entire request"""
        # Check for duplicate class IDs
        ids = [c.id for c in self.classes]
        if len(ids) != len(set(ids)):
            raise ValueError('Duplicate class IDs detected. Each class must have a unique ID')

        # Ensure class names are unique per teacher
        teacher_classes = {}
        for cls in self.classes:
            if cls.teacher not in teacher_classes:
                teacher_classes[cls.teacher] = []
            teacher_classes[cls.teacher].append(cls.name)

        # Check each class duration doesn't exceed periods_per_day
        for cls in self.classes:
            if cls.duration > self.constraints.periods_per_day:
                raise ValueError(
                    f"Class '{cls.name}' duration ({cls.duration}) exceeds periods per day ({self.constraints.periods_per_day})"
                )

        # Calculate total periods needed
        total_needed = sum(c.periods_per_week for c in self.classes)
        total_available = len(self.constraints.days_per_week) * self.constraints.periods_per_day
        if self.constraints.lunch_break_period:
            total_available -= len(self.constraints.days_per_week)

        if total_needed > total_available:
            raise ValueError(
                f'Not enough time slots: need {total_needed} periods but only {total_available} available. '
                f'Reduce periods per week or increase days/periods per day.'
            )

        return self


class TimetableResponse(BaseModel):
    """Response model for timetable generation"""
    schedule: List[TimeSlot]
    success: bool
    message: str
