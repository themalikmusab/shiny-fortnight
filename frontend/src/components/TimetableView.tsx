import { Download, RefreshCw, Home } from 'lucide-react';
import { TimeSlot, ClassInput, Day, TimetableConstraints } from '../types';
import jsPDF from 'jspdf';
import html2canvas from 'html2canvas';

interface TimetableViewProps {
  schedule: TimeSlot[];
  classes: ClassInput[];
  constraints: TimetableConstraints;
  onRegenerate: () => void;
  onReset: () => void;
}

export default function TimetableView({ schedule, classes, constraints, onRegenerate, onReset }: TimetableViewProps) {
  const days = constraints.days_per_week;
  const periodsPerDay = constraints.periods_per_day;

  const getSlot = (day: Day, period: number): TimeSlot | undefined => {
    return schedule.find(s => s.day === day && s.period === period);
  };

  const handleDownloadPDF = async () => {
    const element = document.getElementById('timetable-grid');
    if (!element) return;

    try {
      const canvas = await html2canvas(element, {
        scale: 2,
        backgroundColor: '#ffffff',
      });

      const imgData = canvas.toDataURL('image/png');
      const pdf = new jsPDF({
        orientation: 'landscape',
        unit: 'mm',
        format: 'a4'
      });

      const imgWidth = 280;
      const imgHeight = (canvas.height * imgWidth) / canvas.width;

      pdf.addImage(imgData, 'PNG', 10, 10, imgWidth, imgHeight);
      pdf.save('my-timetable.pdf');
    } catch (error) {
      console.error('Error generating PDF:', error);
    }
  };

  return (
    <div className="min-h-screen p-4 py-12">
      <div className="max-w-7xl mx-auto">
        <div className="card mb-6">
          <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
            <div>
              <h1 className="text-3xl font-bold text-gray-800 mb-2">
                Your Randomized Timetable
              </h1>
              <p className="text-gray-600">
                A unique schedule just for you!
              </p>
            </div>

            <div className="flex gap-3 flex-wrap">
              <button
                onClick={onRegenerate}
                className="btn-secondary flex items-center gap-2"
              >
                <RefreshCw className="w-5 h-5" />
                Regenerate
              </button>

              <button
                onClick={handleDownloadPDF}
                className="btn-primary flex items-center gap-2"
              >
                <Download className="w-5 h-5" />
                Download PDF
              </button>

              <button
                onClick={onReset}
                className="btn-outline flex items-center gap-2"
              >
                <Home className="w-5 h-5" />
                Start Over
              </button>
            </div>
          </div>
        </div>

        <div id="timetable-grid" className="card overflow-x-auto">
          <table className="w-full border-collapse">
            <thead>
              <tr className="bg-gradient-to-r from-blue-600 to-purple-600 text-white">
                <th className="border-2 border-gray-300 p-4 font-semibold text-left">
                  Period
                </th>
                {days.map(day => (
                  <th key={day} className="border-2 border-gray-300 p-4 font-semibold">
                    {day}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {Array.from({ length: periodsPerDay }, (_, i) => i + 1).map(period => (
                <tr key={period} className="hover:bg-gray-50 transition-colors">
                  <td className="border-2 border-gray-300 p-4 font-semibold bg-gray-100">
                    Period {period}
                  </td>
                  {days.map(day => {
                    const slot = getSlot(day, period);

                    if (slot) {
                      return (
                        <td
                          key={`${day}-${period}`}
                          className="border-2 border-gray-300 p-4"
                          style={{
                            backgroundColor: slot.color ? `${slot.color}20` : '#f3f4f6',
                            borderLeft: `4px solid ${slot.color || '#6b7280'}`
                          }}
                        >
                          <div className="font-semibold text-gray-800">
                            {slot.class_name}
                          </div>
                          <div className="text-sm text-gray-600 mt-1">
                            {slot.teacher}
                          </div>
                        </td>
                      );
                    } else if (constraints.lunch_break_period && period === constraints.lunch_break_period) {
                      return (
                        <td
                          key={`${day}-${period}`}
                          className="border-2 border-gray-300 p-4 bg-yellow-50 text-center"
                        >
                          <div className="font-semibold text-yellow-800">
                            LUNCH BREAK
                          </div>
                        </td>
                      );
                    } else {
                      return (
                        <td
                          key={`${day}-${period}`}
                          className="border-2 border-gray-300 p-4 bg-gray-50 text-center text-gray-400"
                        >
                          -
                        </td>
                      );
                    }
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="card mt-6">
          <h3 className="font-semibold text-lg mb-3">Your Classes</h3>
          <div className="flex flex-wrap gap-3">
            {classes.map((cls) => (
              <div
                key={cls.id}
                className="px-4 py-2 rounded-lg border-2"
                style={{
                  backgroundColor: cls.color ? `${cls.color}20` : '#f3f4f6',
                  borderColor: cls.color || '#6b7280'
                }}
              >
                <div className="font-semibold text-sm">{cls.name}</div>
                <div className="text-xs text-gray-600">{cls.teacher}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
