import random
from typing import List, Dict, Tuple, Set, Optional
from models import ClassInput, TimetableConstraints, TimeSlot, Day
from constraint import Problem, AllDifferentConstraint


class TimetableGenerator:
    def __init__(self, classes: List[ClassInput], constraints: TimetableConstraints):
        self.classes = classes
        self.constraints = constraints
        self.days = constraints.days_per_week
        self.periods_per_day = constraints.periods_per_day

    def generate(self) -> Tuple[List[TimeSlot], bool, str]:
        """
        Generate a randomized timetable using Constraint Satisfaction Problem approach.
        Returns: (schedule, success, message)
        """
        try:
            # Calculate total periods needed
            total_periods_needed = sum(c.periods_per_week for c in self.classes)
            total_periods_available = len(self.days) * self.periods_per_day

            # Account for lunch break
            if self.constraints.lunch_break_period:
                total_periods_available -= len(self.days)

            if total_periods_needed > total_periods_available:
                return [], False, f"Not enough time slots! Need {total_periods_needed} but only have {total_periods_available} available."

            # Try multiple times with random ordering
            max_attempts = 50
            for attempt in range(max_attempts):
                schedule = self._generate_with_backtracking()
                if schedule:
                    return schedule, True, "Timetable generated successfully!"

            return [], False, "Could not generate a valid timetable. Try adjusting constraints or reducing classes."

        except Exception as e:
            return [], False, f"Error generating timetable: {str(e)}"

    def _generate_with_backtracking(self) -> Optional[List[TimeSlot]]:
        """
        Use backtracking algorithm to generate schedule.
        This ensures no teacher conflicts and distributes classes across the week.
        """
        schedule: List[TimeSlot] = []
        teacher_schedule: Dict[str, Set[Tuple[Day, int]]] = {}  # teacher -> set of (day, period)

        # Create list of all class instances to schedule
        class_instances = []
        for cls in self.classes:
            for i in range(cls.periods_per_week):
                class_instances.append(cls)

        # Shuffle for randomization
        random.shuffle(class_instances)

        # Get all available time slots
        available_slots = []
        for day in self.days:
            for period in range(1, self.periods_per_day + 1):
                # Skip lunch break
                if self.constraints.lunch_break_period and period == self.constraints.lunch_break_period:
                    continue
                available_slots.append((day, period))

        # Shuffle slots for randomization
        random.shuffle(available_slots)

        # Try to assign each class instance
        used_slots = set()

        for cls in class_instances:
            assigned = False

            # Try each available slot
            for day, period in available_slots:
                slot = (day, period)

                # Check if slot is already used
                if slot in used_slots:
                    continue

                # Check teacher conflict
                if cls.teacher in teacher_schedule:
                    if slot in teacher_schedule[cls.teacher]:
                        continue

                # Check duration (if class needs 2 periods)
                if cls.duration > 1:
                    # Check if next period is available
                    next_period = period + 1
                    if next_period > self.periods_per_day:
                        continue
                    if (day, next_period) in used_slots:
                        continue
                    if self.constraints.lunch_break_period and next_period == self.constraints.lunch_break_period:
                        continue

                # Assign the slot
                schedule.append(TimeSlot(
                    day=day,
                    period=period,
                    class_id=cls.id,
                    class_name=cls.name,
                    teacher=cls.teacher,
                    color=cls.color
                ))

                used_slots.add(slot)

                # Mark teacher as busy
                if cls.teacher not in teacher_schedule:
                    teacher_schedule[cls.teacher] = set()
                teacher_schedule[cls.teacher].add(slot)

                # If duration > 1, mark additional slots
                if cls.duration > 1:
                    for extra_period in range(1, cls.duration):
                        extra_slot = (day, period + extra_period)
                        used_slots.add(extra_slot)
                        teacher_schedule[cls.teacher].add(extra_slot)

                assigned = True
                break

            if not assigned:
                # Backtracking failed - return None to retry
                return None

        return schedule

    def _apply_preferences(self, slots: List[Tuple[Day, int]]) -> List[Tuple[Day, int]]:
        """
        Sort slots based on user preferences (morning/afternoon).
        """
        if self.constraints.prefer_morning:
            # Prioritize earlier periods
            slots.sort(key=lambda x: (self.days.index(x[0]), x[1]))
        elif self.constraints.prefer_afternoon:
            # Prioritize later periods
            slots.sort(key=lambda x: (self.days.index(x[0]), -x[1]))

        return slots


def validate_timetable(schedule: List[TimeSlot]) -> Tuple[bool, str]:
    """
    Validate that the generated timetable has no conflicts.
    """
    # Check for teacher conflicts
    teacher_slots: Dict[str, Set[Tuple[Day, int]]] = {}

    for slot in schedule:
        key = (slot.day, slot.period)

        if slot.teacher not in teacher_slots:
            teacher_slots[slot.teacher] = set()

        if key in teacher_slots[slot.teacher]:
            return False, f"Teacher {slot.teacher} has conflicting classes at {slot.day} period {slot.period}"

        teacher_slots[slot.teacher].add(key)

    return True, "Timetable is valid!"
