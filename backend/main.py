from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from models import GenerateTimetableRequest, TimetableResponse
from timetable_generator import TimetableGenerator, validate_timetable
from pdf_generator import generate_pdf
import logging
import os
import time
from typing import Dict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Timetable Randomizer API",
    description="Generate randomized, conflict-free class timetables",
    version="2.0.0"
)

# Configure CORS with more specific settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
    max_age=3600,  # Cache preflight requests for 1 hour
)

# Request tracking for basic rate limiting
request_tracker: Dict[str, list] = {}
MAX_REQUESTS_PER_MINUTE = 30


def check_rate_limit(client_ip: str) -> bool:
    """Simple in-memory rate limiting"""
    current_time = time.time()
    if client_ip not in request_tracker:
        request_tracker[client_ip] = []

    # Remove old requests (older than 1 minute)
    request_tracker[client_ip] = [
        req_time for req_time in request_tracker[client_ip]
        if current_time - req_time < 60
    ]

    # Check if limit exceeded
    if len(request_tracker[client_ip]) >= MAX_REQUESTS_PER_MINUTE:
        return False

    request_tracker[client_ip].append(current_time)
    return True


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Custom handler for validation errors"""
    logger.warning(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "message": "Invalid input data",
            "errors": exc.errors()
        }
    )


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Custom handler for value errors from Pydantic validators"""
    logger.warning(f"Value error: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "success": False,
            "message": str(exc)
        }
    )


@app.get("/")
def read_root():
    """API information endpoint"""
    return {
        "message": "Timetable Randomizer API",
        "version": "2.0.0",
        "endpoints": {
            "generate": "/api/generate",
            "export_pdf": "/api/export-pdf",
            "health": "/health"
        },
        "docs": "/docs"
    }


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": time.time()
    }


@app.post("/api/generate", response_model=TimetableResponse)
async def generate_timetable(request: GenerateTimetableRequest, req: Request):
    """
    Generate a randomized timetable based on classes and constraints.

    This endpoint validates input, generates a conflict-free timetable,
    and returns the scheduled classes.
    """
    client_ip = req.client.host if req.client else "unknown"

    # Rate limiting
    if not check_rate_limit(client_ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests. Please wait before trying again."
        )

    try:
        logger.info(f"Generating timetable for {len(request.classes)} classes from {client_ip}")

        # Assign random colors to classes if not provided
        colors = [
            "#FF6B6B", "#4ECDC4", "#45B7D1", "#FFA07A", "#98D8C8",
            "#F7DC6F", "#BB8FCE", "#85C1E2", "#F8B739", "#52B788",
            "#E74C3C", "#3498DB", "#2ECC71", "#F39C12", "#9B59B6"
        ]

        for i, cls in enumerate(request.classes):
            if not cls.color:
                cls.color = colors[i % len(colors)]

        # Generate timetable
        generator = TimetableGenerator(request.classes, request.constraints)
        schedule, success, message = generator.generate()

        if not success:
            logger.warning(f"Timetable generation failed: {message}")
            return TimetableResponse(
                schedule=[],
                success=False,
                message=message
            )

        # Validate the generated timetable
        is_valid, validation_message = validate_timetable(schedule)

        if not is_valid:
            logger.error(f"Generated invalid timetable: {validation_message}")
            return TimetableResponse(
                schedule=[],
                success=False,
                message=f"Generated timetable is invalid: {validation_message}"
            )

        logger.info(f"Successfully generated timetable with {len(schedule)} classes")
        return TimetableResponse(
            schedule=schedule,
            success=True,
            message=message
        )

    except ValidationError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again."
        )


@app.post("/api/export-pdf")
async def export_pdf(request: GenerateTimetableRequest, req: Request):
    """
    Generate and return a PDF of the timetable.

    This endpoint generates a timetable and exports it as a PDF file.
    """
    client_ip = req.client.host if req.client else "unknown"

    # Rate limiting
    if not check_rate_limit(client_ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests. Please wait before trying again."
        )

    pdf_path = None
    try:
        logger.info(f"Generating PDF for {len(request.classes)} classes from {client_ip}")

        # Generate timetable first
        generator = TimetableGenerator(request.classes, request.constraints)
        schedule, success, message = generator.generate()

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message
            )

        # Generate PDF
        pdf_path = generate_pdf(schedule, request.constraints)

        if not os.path.exists(pdf_path):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate PDF file"
            )

        logger.info(f"Successfully generated PDF: {pdf_path}")

        # Return file with cleanup
        return FileResponse(
            pdf_path,
            media_type="application/pdf",
            filename="my_timetable.pdf",
            background=None  # Let FastAPI handle cleanup
        )

    except HTTPException:
        # Cleanup temp file if exists
        if pdf_path and os.path.exists(pdf_path):
            try:
                os.unlink(pdf_path)
            except Exception as cleanup_error:
                logger.error(f"Failed to cleanup PDF: {cleanup_error}")
        raise
    except Exception as e:
        # Cleanup temp file if exists
        if pdf_path and os.path.exists(pdf_path):
            try:
                os.unlink(pdf_path)
            except Exception as cleanup_error:
                logger.error(f"Failed to cleanup PDF: {cleanup_error}")

        logger.error(f"Error generating PDF: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate PDF. Please try again."
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
