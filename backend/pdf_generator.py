from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from typing import List
from models import TimeSlot, TimetableConstraints, Day
import tempfile
import logging

logger = logging.getLogger(__name__)


def generate_pdf(schedule: List[TimeSlot], constraints: TimetableConstraints) -> str:
    """
    Generate a PDF of the timetable with enhanced error handling.
    Returns the path to the generated PDF file.

    Args:
        schedule: List of scheduled time slots
        constraints: Timetable constraints

    Returns:
        Path to generated PDF file

    Raises:
        Exception: If PDF generation fails
    """
    try:
        # Validate inputs
        if not schedule:
            logger.warning("Generating PDF for empty schedule")

        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        pdf_path = temp_file.name
        temp_file.close()

        logger.info(f"Generating PDF at: {pdf_path}")

        # Create PDF document
        doc = SimpleDocTemplate(
            pdf_path,
            pagesize=A4,
            rightMargin=30,
            leftMargin=30,
            topMargin=30,
            bottomMargin=30
        )
        elements = []

        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#2C3E50'),
            spaceAfter=30,
            alignment=1  # Center
        )

        subtitle_style = ParagraphStyle(
            'Subtitle',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#7F8C8D'),
            spaceAfter=20,
            alignment=1
        )

        # Add title
        title = Paragraph("My Randomized Timetable", title_style)
        elements.append(title)

        # Add generation info
        from datetime import datetime
        gen_info = Paragraph(
            f"Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}",
            subtitle_style
        )
        elements.append(gen_info)
        elements.append(Spacer(1, 0.2 * inch))

        # Organize schedule into grid
        days = constraints.days_per_week
        periods_per_day = constraints.periods_per_day

        # Create schedule dictionary for easy lookup
        schedule_dict = {}
        for slot in schedule:
            key = (slot.day, slot.period)
            if key in schedule_dict:
                logger.warning(f"Duplicate slot found: {key}")
            schedule_dict[key] = slot

        # Build table data
        table_data = []

        # Header row
        header_row = ['Period'] + [day.value for day in days]
        table_data.append(header_row)

        # Data rows
        for period in range(1, periods_per_day + 1):
            row = [f'Period {period}']

            for day in days:
                key = (day, period)
                if key in schedule_dict:
                    slot = schedule_dict[key]
                    # Truncate long names if necessary
                    class_name = slot.class_name[:15] + "..." if len(slot.class_name) > 15 else slot.class_name
                    teacher_name = slot.teacher[:12] + "..." if len(slot.teacher) > 12 else slot.teacher
                    cell_text = f"{class_name}\n{teacher_name}"
                    row.append(cell_text)
                elif constraints.lunch_break_period and period == constraints.lunch_break_period:
                    row.append("LUNCH\nBREAK")
                else:
                    row.append("-")

            table_data.append(row)

        # Calculate appropriate column widths
        available_width = A4[0] - 60  # Page width minus margins
        period_col_width = 0.8 * inch
        day_col_width = (available_width - period_col_width) / len(days)

        # Create table
        table = Table(
            table_data,
            colWidths=[period_col_width] + [day_col_width] * len(days),
            repeatRows=1  # Repeat header on each page if multi-page
        )

        # Style the table
        table_style = TableStyle([
            # Header styling
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495E')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),

            # First column (periods)
            ('BACKGROUND', (0, 1), (0, -1), colors.HexColor('#ECF0F1')),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 1), (0, -1), 10),

            # Body styling
            ('FONTNAME', (1, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (1, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#BDC3C7')),
            ('ROWBACKGROUNDS', (1, 1), (-1, -1), [colors.white, colors.HexColor('#F8F9FA')]),

            # Lunch break styling
            ('BACKGROUND', (1, constraints.lunch_break_period), (-1, constraints.lunch_break_period),
             colors.HexColor('#FFF3CD')) if constraints.lunch_break_period else ('BACKGROUND', (0, 0), (0, 0), colors.white),

            # Padding
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ])

        table.setStyle(table_style)
        elements.append(table)

        # Add legend/footer
        elements.append(Spacer(1, 0.4 * inch))

        # Summary information
        summary_style = ParagraphStyle(
            'Summary',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#34495E'),
            spaceBefore=10
        )

        total_classes = len(schedule)
        unique_teachers = len(set(slot.teacher for slot in schedule))

        summary_text = f"<b>Schedule Summary:</b> {total_classes} classes scheduled across {len(days)} days with {unique_teachers} teacher(s)"
        summary = Paragraph(summary_text, summary_style)
        elements.append(summary)

        # Footer
        elements.append(Spacer(1, 0.3 * inch))
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.HexColor('#7F8C8D'),
            alignment=1
        )
        footer = Paragraph(
            "Generated by Timetable Randomizer • A new schedule every week!",
            footer_style
        )
        elements.append(footer)

        # Build PDF
        doc.build(elements)
        logger.info(f"Successfully generated PDF with {total_classes} classes")

        return pdf_path

    except Exception as e:
        logger.error(f"Failed to generate PDF: {str(e)}", exc_info=True)
        raise Exception(f"PDF generation failed: {str(e)}")
