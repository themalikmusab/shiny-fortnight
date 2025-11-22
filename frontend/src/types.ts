export enum Day {
  MONDAY = "Monday",
  TUESDAY = "Tuesday",
  WEDNESDAY = "Wednesday",
  THURSDAY = "Thursday",
  FRIDAY = "Friday"
}

export interface ClassInput {
  id: string;
  name: string;
  teacher: string;
  periods_per_week: number;
  duration: number;
  color?: string;
}

export interface TimetableConstraints {
  max_classes_per_day: number;
  periods_per_day: number;
  days_per_week: Day[];
  lunch_break_period: number | null;
  prefer_morning: boolean;
  prefer_afternoon: boolean;
}

export interface TimeSlot {
  day: Day;
  period: number;
  class_id: string;
  class_name: string;
  teacher: string;
  color?: string;
}

export interface TimetableResponse {
  schedule: TimeSlot[];
  success: boolean;
  message: string;
}
