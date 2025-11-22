import { useState } from 'react';
import { Plus, Trash2, Sparkles, ArrowLeft, Loader } from 'lucide-react';
import axios from 'axios';
import { ClassInput, TimetableConstraints, Day, TimeSlot } from '../types';

interface ClassFormProps {
  onSubmit: (classes: ClassInput[]) => void;
  onScheduleGenerated: (schedule: TimeSlot[]) => void;
  onBack: () => void;
}

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

  const addClass = () => {
    const newId = (classes.length + 1).toString();
    setClasses([...classes, {
      id: newId,
      name: '',
      teacher: '',
      periods_per_week: 5,
      duration: 1
    }]);
  };

  const removeClass = (id: string) => {
    setClasses(classes.filter(c => c.id !== id));
  };

  const updateClass = (id: string, field: keyof ClassInput, value: string | number) => {
    setClasses(classes.map(c =>
      c.id === id ? { ...c, [field]: value } : c
    ));
  };

  const handleGenerate = async () => {
    setError(null);

    // Validate
    const emptyClasses = classes.filter(c => !c.name || !c.teacher);
    if (emptyClasses.length > 0) {
      setError('Please fill in all class names and teachers');
      return;
    }

    setLoading(true);
    onSubmit(classes);

    try {
      const response = await axios.post('http://localhost:8000/api/generate', {
        classes: classes,
        constraints: constraints
      });

      if (response.data.success) {
        onScheduleGenerated(response.data.schedule);
      } else {
        setError(response.data.message);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to generate timetable. Please try again.');
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
            <p className="text-red-700">{error}</p>
          </div>
        )}

        <div className="card mb-6">
          <h2 className="text-xl font-semibold mb-4">Your Classes</h2>

          <div className="space-y-4">
            {classes.map((cls, index) => (
              <div key={cls.id} className="flex gap-3 items-start p-4 bg-gray-50 rounded-lg">
                <div className="flex-1 grid grid-cols-1 md:grid-cols-3 gap-3">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Class Name
                    </label>
                    <input
                      type="text"
                      placeholder="e.g., Mathematics"
                      value={cls.name}
                      onChange={(e) => updateClass(cls.id, 'name', e.target.value)}
                      className="input-field"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Teacher Name
                    </label>
                    <input
                      type="text"
                      placeholder="e.g., Mr. Smith"
                      value={cls.teacher}
                      onChange={(e) => updateClass(cls.id, 'teacher', e.target.value)}
                      className="input-field"
                    />
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
                      onChange={(e) => updateClass(cls.id, 'periods_per_week', parseInt(e.target.value))}
                      className="input-field"
                    />
                  </div>
                </div>

                {classes.length > 1 && (
                  <button
                    onClick={() => removeClass(cls.id)}
                    className="mt-7 p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                  >
                    <Trash2 className="w-5 h-5" />
                  </button>
                )}
              </div>
            ))}
          </div>

          <button
            onClick={addClass}
            className="mt-4 flex items-center gap-2 text-blue-600 hover:text-blue-700 font-medium"
          >
            <Plus className="w-5 h-5" />
            Add Another Class
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
                onChange={(e) => setConstraints({...constraints, periods_per_day: parseInt(e.target.value)})}
                className="input-field"
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
                onChange={(e) => setConstraints({
                  ...constraints,
                  lunch_break_period: parseInt(e.target.value) || null
                })}
                className="input-field"
              />
              <p className="text-xs text-gray-500 mt-1">Set to 0 for no lunch break</p>
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
              />
              <span className="text-sm text-gray-700">Prefer afternoon classes</span>
            </label>
          </div>
        </div>

        <div className="flex justify-center">
          <button
            onClick={handleGenerate}
            disabled={loading}
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
