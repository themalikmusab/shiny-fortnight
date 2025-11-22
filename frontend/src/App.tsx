import { useState } from 'react';
import LandingPage from './components/LandingPage';
import ClassForm from './components/ClassForm';
import TimetableView from './components/TimetableView';
import { ClassInput, TimeSlot } from './types';

type View = 'landing' | 'form' | 'timetable';

function App() {
  const [currentView, setCurrentView] = useState<View>('landing');
  const [classes, setClasses] = useState<ClassInput[]>([]);
  const [schedule, setSchedule] = useState<TimeSlot[]>([]);

  const handleStartManual = () => {
    setCurrentView('form');
  };

  const handleClassesSubmit = (submittedClasses: ClassInput[]) => {
    setClasses(submittedClasses);
  };

  const handleScheduleGenerated = (generatedSchedule: TimeSlot[]) => {
    setSchedule(generatedSchedule);
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
          onRegenerate={handleBackToForm}
          onReset={handleReset}
        />
      )}
    </div>
  );
}

export default App;
