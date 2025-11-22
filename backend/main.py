from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from models import GenerateTimetableRequest, TimetableResponse
from timetable_generator import TimetableGenerator, validate_timetable
from pdf_generator import generate_pdf
import random
import string

app = FastAPI(title="Timetable Randomizer API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {
        "message": "Timetable Randomizer API",
        "version": "1.0.0",
        "endpoints": {
            "generate": "/api/generate",
            "health": "/health"
        }
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.post("/api/generate", response_model=TimetableResponse)
def generate_timetable(request: GenerateTimetableRequest):
    """
    Generate a randomized timetable based on classes and constraints.
    """
    try:
        # Assign random colors to classes if not provided
        colors = ["#FF6B6B", "#4ECDC4", "#45B7D1", "#FFA07A", "#98D8C8",
                  "#F7DC6F", "#BB8FCE", "#85C1E2", "#F8B739", "#52B788"]

        for i, cls in enumerate(request.classes):
            if not cls.color:
                cls.color = colors[i % len(colors)]

        # Generate timetable
        generator = TimetableGenerator(request.classes, request.constraints)
        schedule, success, message = generator.generate()

        if not success:
            return TimetableResponse(
                schedule=[],
                success=False,
                message=message
            )

        # Validate the generated timetable
        is_valid, validation_message = validate_timetable(schedule)

        if not is_valid:
            return TimetableResponse(
                schedule=[],
                success=False,
                message=f"Generated timetable is invalid: {validation_message}"
            )

        return TimetableResponse(
            schedule=schedule,
            success=True,
            message=message
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/export-pdf")
async def export_pdf(request: GenerateTimetableRequest):
    """
    Generate and return a PDF of the timetable.
    """
    try:
        # Generate timetable first
        generator = TimetableGenerator(request.classes, request.constraints)
        schedule, success, message = generator.generate()

        if not success:
            raise HTTPException(status_code=400, detail=message)

        # Generate PDF
        pdf_path = generate_pdf(schedule, request.constraints)

        return FileResponse(
            pdf_path,
            media_type="application/pdf",
            filename="my_timetable.pdf"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
