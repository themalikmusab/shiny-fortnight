# 🎓 Timetable Randomizer

Make your class schedule interesting every week! A full-stack application that generates randomized, conflict-free timetables using Constraint Satisfaction Problem (CSP) algorithms.

## ✨ Features

- **Smart Randomization**: Uses CSP algorithms to ensure no teacher conflicts
- **Student-Friendly**: Simple interface for students to create their schedules
- **Conflict-Free**: Automatically handles teacher availability across multiple classes
- **Customizable**: Set preferences like lunch breaks, morning/afternoon classes
- **PDF Export**: Download your timetable as a beautiful PDF
- **Weekly Variety**: Generate unlimited variations for a fresh schedule every week

## 🚀 Tech Stack

### Backend
- **Python 3.8+** with FastAPI
- **python-constraint** for CSP algorithm
- **ReportLab** for PDF generation
- **Pydantic** for data validation

### Frontend
- **React 18** with TypeScript
- **Vite** for fast development
- **TailwindCSS** for styling
- **Axios** for API calls
- **jsPDF** for client-side PDF export

## 📦 Installation

### Prerequisites
- Python 3.8 or higher
- Node.js 16 or higher
- npm or yarn

### Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install
```

## 🏃 Running the Application

### Start Backend Server

```bash
# From backend directory
cd backend

# Activate virtual environment if not already activated
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Run the server
python main.py
```

Backend will be available at: `http://localhost:8000`

### Start Frontend Development Server

```bash
# From frontend directory (in a new terminal)
cd frontend

# Start dev server
npm run dev
```

Frontend will be available at: `http://localhost:3000`

## 📖 How to Use

1. **Landing Page**: Click "Get Started" to begin
2. **Add Classes**:
   - Enter your class names (e.g., Mathematics, English)
   - Add teacher names
   - Specify periods per week for each class
3. **Configure Settings**:
   - Set periods per day (default: 8)
   - Set lunch break period (default: Period 4)
   - Choose morning/afternoon preferences (optional)
4. **Generate**: Click "Generate Timetable" to see the magic!
5. **Export**: Download your timetable as PDF or regenerate for a different schedule

## 🎯 How It Works

### Constraint Satisfaction Problem (CSP) Algorithm

The timetable generator uses a backtracking algorithm with the following constraints:

1. **Teacher Conflicts**: A teacher cannot be in two classes simultaneously
2. **Time Slots**: Each class is assigned to available time slots (day + period)
3. **Lunch Breaks**: Respects designated lunch break periods
4. **Duration**: Handles classes that need multiple consecutive periods (e.g., labs)

### Generation Process

```python
1. Calculate total periods needed vs. available
2. Create list of all class instances to schedule
3. Shuffle for randomization
4. Use backtracking to assign each class to a slot:
   - Check if slot is available
   - Check if teacher is free
   - Check duration requirements
   - Assign and mark slot as used
5. Validate final schedule for conflicts
```

## 🏗️ Project Structure

```
shiny-fortnight/
├── backend/
│   ├── main.py                 # FastAPI application
│   ├── models.py               # Pydantic models
│   ├── timetable_generator.py  # CSP algorithm
│   ├── pdf_generator.py        # PDF export
│   └── requirements.txt        # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── LandingPage.tsx
│   │   │   ├── ClassForm.tsx
│   │   │   └── TimetableView.tsx
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   ├── types.ts
│   │   └── index.css
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   └── tailwind.config.js
└── README.md
```

## 🔧 API Endpoints

### `POST /api/generate`
Generate a randomized timetable

**Request Body:**
```json
{
  "classes": [
    {
      "id": "1",
      "name": "Mathematics",
      "teacher": "Mr. Smith",
      "periods_per_week": 5,
      "duration": 1,
      "color": "#FF6B6B"
    }
  ],
  "constraints": {
    "max_classes_per_day": 8,
    "periods_per_day": 8,
    "days_per_week": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
    "lunch_break_period": 4,
    "prefer_morning": false,
    "prefer_afternoon": false
  }
}
```

**Response:**
```json
{
  "schedule": [
    {
      "day": "Monday",
      "period": 1,
      "class_id": "1",
      "class_name": "Mathematics",
      "teacher": "Mr. Smith",
      "color": "#FF6B6B"
    }
  ],
  "success": true,
  "message": "Timetable generated successfully!"
}
```

## 🎨 Customization

### Adding More Constraints

Edit `backend/timetable_generator.py` to add custom constraints:

```python
# Example: Prefer specific classes in morning
if cls.name == "Mathematics" and period > 4:
    continue  # Skip afternoon slots for Math
```

### Styling

Modify `frontend/tailwind.config.js` for custom colors and themes.

## 🐛 Troubleshooting

### Backend Issues

- **Port 8000 already in use**: Change port in `main.py`:
  ```python
  uvicorn.run(app, host="0.0.0.0", port=8001)
  ```

- **Module not found**: Ensure virtual environment is activated and dependencies are installed

### Frontend Issues

- **CORS errors**: Backend CORS is configured for `*`. In production, update to specific origin
- **Build errors**: Delete `node_modules` and reinstall: `rm -rf node_modules && npm install`

## 📝 Future Enhancements

- [ ] Image/PDF upload with OCR to extract timetable data
- [ ] Save schedules to database for history
- [ ] Share timetables via unique links
- [ ] Mobile app version
- [ ] Multi-language support
- [ ] Class room assignments
- [ ] Weekly schedule rotation presets

## 🤝 Contributing

Contributions are welcome! Feel free to:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

MIT License - feel free to use this project for personal or educational purposes!

## 🙏 Acknowledgments

- Built with ❤️ for students who want variety in their schedules
- Uses Constraint Satisfaction Problem algorithms for intelligent scheduling
- Inspired by the need to make learning more engaging through schedule variety

---

**Happy Scheduling! ✨**