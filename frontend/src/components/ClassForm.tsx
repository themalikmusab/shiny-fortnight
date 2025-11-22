import { useState, useEffect } from 'react';
import { Plus, Trash2, Sparkles, ArrowLeft, Loader, AlertCircle } from 'lucide-react';
import axios from 'axios';
import { ClassInput, TimetableConstraints, Day, TimeSlot } from '../types';

interface ClassFormProps {
  onSubmit: (classes: ClassInput[], constraints: TimetableConstraints) => void;
  onScheduleGenerated: (schedule: TimeSlot[], constraints: TimetableConstraints) => void;
  onBack: () => void;
}

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function ClassForm({ onSubmit, onScheduleGenerated, onBack }: ClassFormProps) {
  const [classes, setClasses] = useState<ClassInput[]>([
    { id: '1', name: '', teacher: '', periods_per_week: 5, duration: 1 }
  ]);

  const [constraints, setConstraints] = useState<TimetableConstraints>({
    max_classes_per_day: 8,
    periods_per_day: 8,
    days_per_week: [Day.MONDAY, Day.TUESDAY, Day.WEDNESDAY, Day.THURSDAY, Day.FRIDAY],
    lunch_break_period: 4,
    prefer_morning: false,
    prefer_afternoon: false,
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({});

  // Calculate availability stats
  const totalPeriodsNeeded = classes.reduce((sum, cls) => {
    const periodsPerWeek = cls.periods_per_week || 0;
    const duration = cls.duration || 1;
    return sum + (periodsPerWeek * duration);
  }, 0);

  const totalPeriodsAvailable = constraints.days_per_week.length * constraints.periods_per_day -
    (constraints.lunch_break_period ? constraints.days_per_week.length : 0);

  const utilizationRate = totalPeriodsAvailable > 0
    ? Math.round((totalPeriodsNeeded / totalPeriodsAvailable) * 100)
    : 0;

  useEffect(() => {
    // Clear error when user makes changes
    if (error) {
      setError(null);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [classes, constraints]);

  const addClass = () => {
    const newId = Date.now().toString(); // Use timestamp for unique ID
    setClasses([...classes, {
      id: newId,
      name: '',
      teacher: '',
      periods_per_week: 5,
      duration: 1
    }]);
  };

  const removeClass = (id: string) => {
    if (classes.length > 1) {
      setClasses(classes.filter(c => c.id !== id));
      // Clear validation errors for this class
      const newErrors = { ...validationErrors };
      delete newErrors[`class-${id}-name`];
      delete newErrors[`class-${id}-teacher`];
      setValidationErrors(newErrors);
    }
  };

  const updateClass = (id: string, field: keyof ClassInput, value: string | number) => {
    setClasses(classes.map(c => {
      if (c.id === id) {
        const updated = { ...c, [field]: value };
        // Auto-trim strings
        if (field === 'name' || field === 'teacher') {
          updated[field] = (value as string).trimStart();
        }
        return updated;
      }
      return c;
    }));

    // Clear validation error for this field
    if (validationErrors[`class-${id}-${field}`]) {
      const newErrors = { ...validationErrors };
      delete newErrors[`class-${id}-${field}`];
      setValidationErrors(newErrors);
    }
  };

  const validateInputs = (): boolean => {
    const errors: Record<string, string> = {};

    // Validate each class
    classes.forEach(cls => {
      if (!cls.name || !cls.name.trim()) {
        errors[`class-${cls.id}-name`] = 'Class name is required';
      } else if (cls.name.trim().length > 100) {
        errors[`class-${cls.id}-name`] = 'Class name too long (max 100 chars)';
      }

      if (!cls.teacher || !cls.teacher.trim()) {
        errors[`class-${cls.id}-teacher`] = 'Teacher name is required';
      } else if (cls.teacher.trim().length > 100) {
        errors[`class-${cls.id}-teacher`] = 'Teacher name too long (max 100 chars)';
      }

      if (cls.periods_per_week < 1 || cls.periods_per_week > 40) {
        errors[`class-${cls.id}-periods`] = 'Periods must be between 1-40';
      }

      if (cls.duration < 1 || cls.duration > 4) {
        errors[`class-${cls.id}-duration`] = 'Duration must be between 1-4';
      }

      if (cls.duration > constraints.periods_per_day) {
        errors[`class-${cls.id}-duration`] = `Duration cannot exceed periods per day (${constraints.periods_per_day})`;
      }
    });

    // Check for duplicate class IDs (shouldn't happen but safety check)
    const ids = classes.map(c => c.id);
    if (new Set(ids).size !== ids.length) {
      errors.general = 'Duplicate class IDs detected. Please refresh the page.';
    }

    // Validate constraints
    if (constraints.lunch_break_period && constraints.lunch_break_period > constraints.periods_per_day) {
      errors.lunch = `Lunch break period (${constraints.lunch_break_period}) cannot exceed periods per day (${constraints.periods_per_day})`;
    }

    // Check capacity
    if (totalPeriodsNeeded > totalPeriodsAvailable) {
      errors.capacity = `Not enough time slots! Need ${totalPeriodsNeeded} but only ${totalPeriodsAvailable} available.`;
    }

    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleGenerate = async () => {
    setError(null);

    // Validate inputs
    if (!validateInputs()) {
      setError('Please fix the validation errors above');
      return;
    }

    setLoading(true);

    // Trim all string fields before submitting
    const trimmedClasses = classes.map(cls => ({
      ...cls,
      name: cls.name.trim(),
      teacher: cls.teacher.trim()
    }));

    onSubmit(trimmedClasses, constraints);

    try {
      const response = await axios.post(`${API_BASE_URL}/api/generate`, {
        classes: trimmedClasses,
        constraints: constraints
      }, {
        timeout: 30000, // 30 second timeout
      });

      if (response.data.success) {
        onScheduleGenerated(response.data.schedule, constraints);
      } else {
        setError(response.data.message || 'Failed to generate timetable');
      }
    } catch (err: any) {
      if (err.code === 'ECONNABORTED') {
        setError('Request timed out. The server might be busy. Please try again.');
      } else if (err.response?.status === 429) {
        setError('Too many requests. Please wait a moment and try again.');
      } else if (err.response?.data?.message) {
        setError(err.response.data.message);
      } else if (err.response?.data?.detail) {
        setError(err.response.data.detail);
      } else if (err.message) {
        setError(`Network error: ${err.message}. Please check your connection.`);
      } else {
        setError('Failed to generate timetable. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen p-4 py-12">
      <div className="max-w-4xl mx-auto">
        <button
          onClick={onBack}
          className="mb-6 flex items-center gap-2 text-white hover:text-white/80 transition-colors"
          disabled={loading}
        >
          <ArrowLeft className="w-5 h-5" />
          Back
        </button>

        <div className="card mb-6">
          <h1 className="text-3xl font-bold text-gray-800 mb-2">
            Build Your Timetable
          </h1>
          <p className="text-gray-600">
            Add your classes and we'll create a randomized schedule for you
          </p>
        </div>

        {error && (
          <div className="card mb-6 bg-red-50 border-2 border-red-200">
            <div className="flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
              <p className="text-red-700 flex-1">{error}</p>
            </div>
          </div>
        )}

        {validationErrors.general && (
          <div className="card mb-6 bg-yellow-50 border-2 border-yellow-200">
            <p className="text-yellow-800">{validationErrors.general}</p>
          </div>
        )}

        {validationErrors.capacity && (
          <div className="card mb-6 bg-orange-50 border-2 border-orange-200">
            <p className="text-orange-800">{validationErrors.capacity}</p>
          </div>
        )}

        <div className="card mb-6">
          <h2 className="text-xl font-semibold mb-4">Your Classes</h2>

          <div className="space-y-4">
            {classes.map((cls) => (
              <div key={cls.id} className="p-4 bg-gray-50 rounded-lg border-2 border-gray-200">
                <div className="flex gap-3 items-start">
                  <div className="flex-1 grid grid-cols-1 md:grid-cols-4 gap-3">
                    <div className="md:col-span-2">
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Class Name <span className="text-red-500">*</span>
                      </label>
                      <input
                        type="text"
                        placeholder="e.g., Mathematics"
                        value={cls.name}
                        onChange={(e) => updateClass(cls.id, 'name', e.target.value)}
                        className={`input-field ${validationErrors[`class-${cls.id}-name`] ? 'border-red-500' : ''}`}
                        maxLength={100}
                        disabled={loading}
                      />
                      {validationErrors[`class-${cls.id}-name`] && (
                        <p className="text-red-500 text-xs mt-1">{validationErrors[`class-${cls.id}-name`]}</p>
                      )}
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Teacher Name <span className="text-red-500">*</span>
                      </label>
                      <input
                        type="text"
                        placeholder="e.g., Mr. Smith"
                        value={cls.teacher}
                        onChange={(e) => updateClass(cls.id, 'teacher', e.target.value)}
                        className={`input-field ${validationErrors[`class-${cls.id}-teacher`] ? 'border-red-500' : ''}`}
                        maxLength={100}
                        disabled={loading}
                      />
                      {validationErrors[`class-${cls.id}-teacher`] && (
                        <p className="text-red-500 text-xs mt-1">{validationErrors[`class-${cls.id}-teacher`]}</p>
                      )}
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Periods/Week
                      </label>
                      <input
                        type="number"
                        min="1"
                        max="40"
                        value={cls.periods_per_week}
                        onChange={(e) => {
                          const val = parseInt(e.target.value);
                          updateClass(cls.id, 'periods_per_week', isNaN(val) ? 1 : Math.max(1, Math.min(40, val)));
                        }}
                        className="input-field"
                        disabled={loading}
                      />
                    </div>
                  </div>

                  {classes.length > 1 && (
                    <button
                      onClick={() => removeClass(cls.id)}
                      className="mt-7 p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors disabled:opacity-50"
                      disabled={loading}
                      title="Remove class"
                    >
                      <Trash2 className="w-5 h-5" />
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>

          <button
            onClick={addClass}
            className="mt-4 flex items-center gap-2 text-blue-600 hover:text-blue-700 font-medium disabled:opacity-50"
            disabled={loading || classes.length >= 20}
          >
            <Plus className="w-5 h-5" />
            Add Another Class {classes.length >= 20 && '(Maximum reached)'}
          </button>
        </div>

        <div className="card mb-6">
          <h2 className="text-xl font-semibold mb-4">Settings</h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Periods Per Day
              </label>
              <input
                type="number"
                min="4"
                max="12"
                value={constraints.periods_per_day}
                onChange={(e) => {
                  const val = parseInt(e.target.value);
                  setConstraints({
                    ...constraints,
                    periods_per_day: isNaN(val) ? 8 : Math.max(4, Math.min(12, val))
                  });
                }}
                className="input-field"
                disabled={loading}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Lunch Break (Period #)
              </label>
              <input
                type="number"
                min="0"
                max={constraints.periods_per_day}
                value={constraints.lunch_break_period || 0}
                onChange={(e) => {
                  const val = parseInt(e.target.value);
                  setConstraints({
                    ...constraints,
                    lunch_break_period: val === 0 ? null : Math.max(0, Math.min(constraints.periods_per_day, val))
                  });
                }}
                className={`input-field ${validationErrors.lunch ? 'border-red-500' : ''}`}
                disabled={loading}
              />
              <p className="text-xs text-gray-500 mt-1">Set to 0 for no lunch break</p>
              {validationErrors.lunch && (
                <p className="text-red-500 text-xs mt-1">{validationErrors.lunch}</p>
              )}
            </div>
          </div>

          <div className="mt-4 space-y-2">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={constraints.prefer_morning}
                onChange={(e) => setConstraints({
                  ...constraints,
                  prefer_morning: e.target.checked,
                  prefer_afternoon: false
                })}
                className="w-4 h-4 text-blue-600 rounded"
                disabled={loading}
              />
              <span className="text-sm text-gray-700">Prefer morning classes</span>
            </label>

            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={constraints.prefer_afternoon}
                onChange={(e) => setConstraints({
                  ...constraints,
                  prefer_afternoon: e.target.checked,
                  prefer_morning: false
                })}
                className="w-4 h-4 text-blue-600 rounded"
                disabled={loading}
              />
              <span className="text-sm text-gray-700">Prefer afternoon classes</span>
            </label>
          </div>

          {/* Capacity indicator */}
          <div className="mt-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-700">Schedule Capacity</span>
              <span className={`text-sm font-semibold ${
                utilizationRate > 90 ? 'text-red-600' :
                utilizationRate > 75 ? 'text-orange-600' :
                'text-green-600'
              }`}>
                {utilizationRate}%
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className={`h-2 rounded-full transition-all ${
                  utilizationRate > 90 ? 'bg-red-500' :
                  utilizationRate > 75 ? 'bg-orange-500' :
                  'bg-green-500'
                }`}
                style={{ width: `${Math.min(100, utilizationRate)}%` }}
              />
            </div>
            <p className="text-xs text-gray-600 mt-2">
              Using {totalPeriodsNeeded} of {totalPeriodsAvailable} available periods
            </p>
          </div>
        </div>

        <div className="flex justify-center">
          <button
            onClick={handleGenerate}
            disabled={loading || classes.length === 0}
            className="btn-primary text-lg px-12 py-4 flex items-center gap-3 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <>
                <Loader className="w-6 h-6 animate-spin" />
                Generating...
              </>
            ) : (
              <>
                <Sparkles className="w-6 h-6" />
                Generate Timetable
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
