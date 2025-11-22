import { Sparkles, Calendar, RefreshCw } from 'lucide-react';

interface LandingPageProps {
  onStartManual: () => void;
}

export default function LandingPage({ onStartManual }: LandingPageProps) {
  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <div className="max-w-4xl w-full">
        <div className="text-center mb-12">
          <div className="flex justify-center mb-6">
            <div className="bg-white p-4 rounded-full shadow-lg">
              <Sparkles className="w-16 h-16 text-purple-600" />
            </div>
          </div>

          <h1 className="text-5xl md:text-6xl font-bold text-white mb-4">
            Timetable Randomizer
          </h1>

          <p className="text-xl text-white/90 mb-8">
            Make your class schedule interesting every week!
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-6 mb-12">
          <div className="card text-center">
            <Calendar className="w-12 h-12 text-blue-600 mx-auto mb-4" />
            <h3 className="text-lg font-semibold mb-2">Add Your Classes</h3>
            <p className="text-gray-600 text-sm">
              Enter your subjects and teachers
            </p>
          </div>

          <div className="card text-center">
            <RefreshCw className="w-12 h-12 text-purple-600 mx-auto mb-4" />
            <h3 className="text-lg font-semibold mb-2">Generate Schedule</h3>
            <p className="text-gray-600 text-sm">
              AI creates a conflict-free timetable
            </p>
          </div>

          <div className="card text-center">
            <Sparkles className="w-12 h-12 text-pink-600 mx-auto mb-4" />
            <h3 className="text-lg font-semibold mb-2">See the Magic</h3>
            <p className="text-gray-600 text-sm">
              Get a new schedule every week
            </p>
          </div>
        </div>

        <div className="flex justify-center gap-4">
          <button
            onClick={onStartManual}
            className="btn-primary text-lg px-8 py-4"
          >
            Get Started
          </button>
        </div>

        <div className="mt-12 text-center">
          <div className="card inline-block">
            <h4 className="font-semibold mb-2">Why Randomize?</h4>
            <ul className="text-sm text-gray-600 space-y-1 text-left">
              <li>✨ Keeps classes fresh and interesting</li>
              <li>🧠 Different daily patterns boost engagement</li>
              <li>🎯 No more boring Monday blues with the same schedule</li>
              <li>⚡ Smart algorithm handles teacher conflicts automatically</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
