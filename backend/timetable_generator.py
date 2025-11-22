import random
from typing import List, Dict, Tuple, Set, Optional
from models import ClassInput, TimetableConstraints, TimeSlot, Day
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TimetableGenerator:
    """
    Advanced timetable generator using Constraint Satisfaction Problem (CSP) approach.
    Ensures conflict-free scheduling with teacher availability and preference support.
    """

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
            # Pre-validation (belt and suspenders - Pydantic should catch these)
            if not self.classes:
                return [], False, "No classes provided. Please add at least one class."

            # Additional runtime validations
            for cls in self.classes:
                if cls.duration <= 0:
                    return [], False, f"Class '{cls.name}' has invalid duration {cls.duration}. Duration must be at least 1."
                if cls.duration > self.periods_per_day:
                    return [], False, f"Class '{cls.name}' duration ({cls.duration}) exceeds periods per day ({self.periods_per_day})."
                if cls.periods_per_week <= 0:
                    return [], False, f"Class '{cls.name}' must have at least 1 period per week."

            # Calculate total periods needed
            total_periods_needed = sum(c.periods_per_week * c.duration for c in self.classes)
            total_periods_available = len(self.days) * self.periods_per_day

            # Account for lunch break
            if self.constraints.lunch_break_period:
                total_periods_available -= len(self.days)

            if total_periods_needed > total_periods_available:
                return [], False, (
                    f"Not enough time slots! Need {total_periods_needed} periods "
                    f"but only have {total_periods_available} available. "
                    f"Reduce class durations or periods per week."
                )

            # Try multiple times with random ordering for better success rate
            max_attempts = 100  # Increased from 50
            best_schedule = None
            best_fill_rate = 0

            for attempt in range(max_attempts):
                schedule = self._generate_with_backtracking()
                if schedule:
                    # Calculate fill rate
                    fill_rate = len(schedule) / len(self.classes)
                    if fill_rate > best_fill_rate:
                        best_schedule = schedule
                        best_fill_rate = fill_rate

                    # If we got a complete schedule, return immediately
                    if fill_rate == 1.0:
                        logger.info(f"Generated complete timetable on attempt {attempt + 1}")
                        return schedule, True, "Timetable generated successfully!"

            # Return best attempt even if not complete
            if best_schedule:
                missing = len(self.classes) - len(best_schedule)
                return best_schedule, True, (
                    f"Timetable generated with {len(best_schedule)} classes. "
                    f"Could not schedule {missing} classes due to constraints."
                )

            return [], False, (
                "Could not generate a valid timetable after 100 attempts. "
                "Try adjusting constraints, reducing class durations, or reducing periods per week."
            )

        except Exception as e:
            logger.error(f"Error generating timetable: {str(e)}", exc_info=True)
            return [], False, f"Error generating timetable: {str(e)}"

    def _generate_with_backtracking(self) -> Optional[List[TimeSlot]]:
        """
        Use backtracking algorithm to generate schedule.
        This ensures no teacher conflicts and distributes classes across the week.
        """
        schedule: List[TimeSlot] = []
        teacher_schedule: Dict[str, Set[Tuple[Day, int]]] = {}  # teacher -> set of (day, period)
        slot_usage: Dict[Tuple[Day, int], str] = {}  # (day, period) -> class_id (for debugging)

        # Create list of all class instances to schedule
        class_instances = []
        for cls in self.classes:
            for i in range(cls.periods_per_week):
                class_instances.append(cls)

        # Sort by duration (longest first) for better packing
        class_instances.sort(key=lambda x: x.duration, reverse=True)

        # Shuffle classes with same duration for randomization
        current_duration = None
        start_idx = 0
        for i, cls in enumerate(class_instances):
            if cls.duration != current_duration:
                if start_idx < i:
                    # Shuffle the previous duration group
                    random.shuffle(class_instances[start_idx:i])
                current_duration = cls.duration
                start_idx = i
        # Shuffle the last group
        if start_idx < len(class_instances):
            random.shuffle(class_instances[start_idx:])

        # Get all available time slots
        available_slots = []
        for day in self.days:
            for period in range(1, self.periods_per_day + 1):
                # Skip lunch break
                if self.constraints.lunch_break_period and period == self.constraints.lunch_break_period:
                    continue
                available_slots.append((day, period))

        # Apply preferences before shuffling
        available_slots = self._apply_preferences(available_slots)

        # Shuffle slots for randomization (but preferences are already sorted)
        if not self.constraints.prefer_morning and not self.constraints.prefer_afternoon:
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

                # Check duration (if class needs multiple consecutive periods)
                if cls.duration > 1:
                    # Check if ALL required consecutive periods are available
                    all_periods_available = True
                    periods_to_check = []

                    for extra in range(cls.duration):
                        check_period = period + extra
                        check_slot = (day, check_period)

                        # Boundary check
                        if check_period > self.periods_per_day:
                            all_periods_available = False
                            break

                        # Check if already used
                        if check_slot in used_slots:
                            all_periods_available = False
                            break

                        # Check lunch break conflict
                        if self.constraints.lunch_break_period and check_period == self.constraints.lunch_break_period:
                            all_periods_available = False
                            break

                        # Check teacher availability for all periods
                        if cls.teacher in teacher_schedule and check_slot in teacher_schedule[cls.teacher]:
                            all_periods_available = False
                            break

                        periods_to_check.append(check_slot)

                    if not all_periods_available:
                        continue

                # All checks passed - assign the slot
                schedule.append(TimeSlot(
                    day=day,
                    period=period,
                    class_id=cls.id,
                    class_name=cls.name,
                    teacher=cls.teacher,
                    color=cls.color
                ))

                # Mark teacher as busy and slots as used
                if cls.teacher not in teacher_schedule:
                    teacher_schedule[cls.teacher] = set()

                # Mark all periods for this class
                for extra in range(cls.duration):
                    extra_slot = (day, period + extra)
                    used_slots.add(extra_slot)
                    teacher_schedule[cls.teacher].add(extra_slot)
                    slot_usage[extra_slot] = cls.id

                assigned = True
                break

            if not assigned:
                # Backtracking failed - return None to retry with different ordering
                logger.debug(f"Failed to assign class {cls.name} ({cls.teacher})")
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
    Returns: (is_valid, message)
    """
    if not schedule:
        return True, "Empty schedule (valid but not useful)"

    # Check for teacher conflicts
    teacher_slots: Dict[str, Set[Tuple[Day, int]]] = {}

    for slot in schedule:
        key = (slot.day, slot.period)

        if slot.teacher not in teacher_slots:
            teacher_slots[slot.teacher] = set()

        if key in teacher_slots[slot.teacher]:
            return False, (
                f"Teacher {slot.teacher} has conflicting classes at "
                f"{slot.day} period {slot.period}: {slot.class_name}"
            )

        teacher_slots[slot.teacher].add(key)

    # Check for duplicate slots
    slot_map: Dict[Tuple[Day, int], List[str]] = {}
    for slot in schedule:
        key = (slot.day, slot.period)
        if key not in slot_map:
            slot_map[key] = []
        slot_map[key].append(f"{slot.class_name} ({slot.teacher})")

    duplicates = {k: v for k, v in slot_map.items() if len(v) > 1}
    if duplicates:
        conflicts = []
        for (day, period), classes in duplicates.items():
            conflicts.append(f"{day} Period {period}: {', '.join(classes)}")
        return False, "Scheduling conflicts found:\n" + "\n".join(conflicts)

    return True, f"Timetable is valid! {len(schedule)} classes scheduled successfully."
