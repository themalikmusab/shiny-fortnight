import { useState } from 'react';
import LandingPage from './components/LandingPage';
import ClassForm from './components/ClassForm';
import TimetableView from './components/TimetableView';
import { ClassInput, TimeSlot, TimetableConstraints, Day } from './types';

type View = 'landing' | 'form' | 'timetable';

function App() {
  const [currentView, setCurrentView] = useState<View>('landing');
  const [classes, setClasses] = useState<ClassInput[]>([]);
  const [schedule, setSchedule] = useState<TimeSlot[]>([]);
  const [constraints, setConstraints] = useState<TimetableConstraints>({
    max_classes_per_day: 8,
    periods_per_day: 8,
    days_per_week: [Day.MONDAY, Day.TUESDAY, Day.WEDNESDAY, Day.THURSDAY, Day.FRIDAY],
    lunch_break_period: 4,
    prefer_morning: false,
    prefer_afternoon: false,
  });

  const handleStartManual = () => {
    setCurrentView('form');
  };

  const handleClassesSubmit = (submittedClasses: ClassInput[], submittedConstraints: TimetableConstraints) => {
    setClasses(submittedClasses);
    setConstraints(submittedConstraints);
  };

  const handleScheduleGenerated = (generatedSchedule: TimeSlot[], submittedConstraints: TimetableConstraints) => {
    setSchedule(generatedSchedule);
    setConstraints(submittedConstraints);
    setCurrentView('timetable');
  };

  const handleReset = () => {
    setCurrentView('landing');
    setClasses([]);
    setSchedule([]);
  };

  const handleBackToForm = () => {
    setCurrentView('form');
  };

  return (
    <div className="min-h-screen">
      {currentView === 'landing' && (
        <LandingPage onStartManual={handleStartManual} />
      )}

      {currentView === 'form' && (
        <ClassForm
          onSubmit={handleClassesSubmit}
          onScheduleGenerated={handleScheduleGenerated}
          onBack={handleReset}
        />
      )}

      {currentView === 'timetable' && (
        <TimetableView
          schedule={schedule}
          classes={classes}
          constraints={constraints}
          onRegenerate={handleBackToForm}
          onReset={handleReset}
        />
      )}
    </div>
  );
}

export default App;
