import csv
import json
from datetime import datetime
from io import BytesIO, StringIO

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response, StreamingResponse
from openpyxl import Workbook
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.dependencies import require_roles
from app.models.submission import Submission, SubmissionAnswer, SubmissionStatus
from app.models.user import RoleName, User

router = APIRouter(prefix="/api/exports", tags=["exports"])


def _query_submissions(
    db: Session,
    survey_id: str | None,
    status_filter: SubmissionStatus | None,
    submitted_by_id: str | None,
    date_from: str | None,
    date_to: str | None,
):
    query = (
        db.query(Submission)
        .options(
            joinedload(Submission.answers).joinedload(SubmissionAnswer.question),
            joinedload(Submission.survey),
            joinedload(Submission.submitted_by),
        )
    )
    if survey_id:
        query = query.filter(Submission.survey_id == survey_id)
    if status_filter:
        query = query.filter(Submission.status == status_filter)
    if submitted_by_id:
        query = query.filter(Submission.submitted_by_id == submitted_by_id)
    if date_from:
        query = query.filter(Submission.collected_at >= date_from)
    if date_to:
        query = query.filter(Submission.collected_at <= date_to + "T23:59:59")
    return query.order_by(Submission.created_at.desc()).all()


def _flat_rows(submissions):
    question_labels: dict[str, str] = {}
    for s in submissions:
        for a in s.answers:
            question_labels.setdefault(a.question_id, a.question.code if a.question else a.question_id)
    labels = list(question_labels.items())
    rows = []
    for s in submissions:
        row = {
            "submission_id": s.id,
            "survey": s.survey.title if s.survey else s.survey_id,
            "survey_version_id": s.survey_version_id,
            "enumerator": s.submitted_by.full_name if s.submitted_by else s.submitted_by_id,
            "status": s.status.value if hasattr(s.status, "value") else str(s.status),
            "review_status": s.review_status.value if hasattr(s.review_status, "value") else str(s.review_status),
            "latitude": s.gps_latitude,
            "longitude": s.gps_longitude,
            "collected_at": s.collected_at,
            "synced_at": s.synced_at,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        }
        answer_map = {}
        for a in s.answers:
            key = question_labels[a.question_id]
            answer_map[key] = a.value_text or a.media_reference or ""
        for qid, label in labels:
            row[label] = answer_map.get(label, "")
        rows.append(row)
    return rows


@router.get("/json")
def export_json(
    survey_id: str | None = None,
    status_filter: SubmissionStatus | None = Query(default=None, alias="status"),
    submitted_by_id: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RoleName.ADMINISTRATOR, RoleName.SUPERVISOR)),
):
    submissions = _query_submissions(db, survey_id, status_filter, submitted_by_id, date_from, date_to)
    payload = []
    for s in submissions:
        payload.append({
            "submission_id": s.id,
            "survey_id": s.survey_id,
            "survey": s.survey.title if s.survey else None,
            "survey_version_id": s.survey_version_id,
            "submitted_by_id": s.submitted_by_id,
            "enumerator": s.submitted_by.full_name if s.submitted_by else None,
            "status": s.status.value if hasattr(s.status, "value") else str(s.status),
            "review_status": s.review_status.value if hasattr(s.review_status, "value") else str(s.review_status),
            "gps": {"latitude": s.gps_latitude, "longitude": s.gps_longitude},
            "collected_at": s.collected_at,
            "synced_at": s.synced_at,
            "answers": [
                {
                    "question_id": a.question_id,
                    "question_code": a.question.code if a.question else None,
                    "value": a.value_text,
                    "media_reference": a.media_reference,
                    "group_instance_index": a.group_instance_index,
                }
                for a in s.answers
            ],
        })
    content = json.dumps({"count": len(payload), "generated_at": datetime.utcnow().isoformat() + "Z", "submissions": payload}, ensure_ascii=False, indent=2)
    return Response(content=content, media_type="application/json", headers={"Content-Disposition": "attachment; filename=kbs-submissions.json"})


@router.get("/csv")
def export_csv(
    survey_id: str | None = None,
    status_filter: SubmissionStatus | None = Query(default=None, alias="status"),
    submitted_by_id: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RoleName.ADMINISTRATOR, RoleName.SUPERVISOR)),
):
    rows = _flat_rows(_query_submissions(db, survey_id, status_filter, submitted_by_id, date_from, date_to))
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=list(rows[0].keys()) if rows else ["submission_id", "survey", "status"])
    writer.writeheader()
    writer.writerows(rows)
    return StreamingResponse(iter([output.getvalue().encode("utf-8-sig")]), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=kbs-submissions.csv"})


@router.get("/xlsx")
def export_xlsx(
    survey_id: str | None = None,
    status_filter: SubmissionStatus | None = Query(default=None, alias="status"),
    submitted_by_id: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RoleName.ADMINISTRATOR, RoleName.SUPERVISOR)),
):
    rows = _flat_rows(_query_submissions(db, survey_id, status_filter, submitted_by_id, date_from, date_to))
    wb = Workbook()
    ws = wb.active
    ws.title = "Submissions"
    headers = list(rows[0].keys()) if rows else ["submission_id", "survey", "status"]
    ws.append(headers)
    for cell in ws[1]:
        cell.font = cell.font.copy(bold=True)
    for row in rows:
        ws.append([row.get(h, "") for h in headers])
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = ws.dimensions
    for column_cells in ws.columns:
        width = min(max(len(str(c.value or "")) for c in column_cells) + 2, 45)
        ws.column_dimensions[column_cells[0].column_letter].width = width
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    return StreamingResponse(iter([output.getvalue()]), media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": "attachment; filename=kbs-submissions.xlsx"})


@router.get("/pdf")
def export_pdf(
    survey_id: str | None = None,
    status_filter: SubmissionStatus | None = Query(default=None, alias="status"),
    submitted_by_id: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RoleName.ADMINISTRATOR, RoleName.SUPERVISOR)),
):
    submissions = _query_submissions(db, survey_id, status_filter, submitted_by_id, date_from, date_to)
    styles = getSampleStyleSheet()
    output = BytesIO()
    doc = SimpleDocTemplate(output, pagesize=landscape(A4), rightMargin=24, leftMargin=24, topMargin=24, bottomMargin=24)
    story = [Paragraph("KBS Toolbox — Submission Export", styles["Title"]), Spacer(1, 10), Paragraph(f"Records: {len(submissions)}", styles["Normal"]), Spacer(1, 10)]
    data = [["Survey", "Enumerator", "Status", "Review", "Collected", "Latitude", "Longitude"]]
    for s in submissions:
        data.append([
            (s.survey.title if s.survey else s.survey_id)[:35],
            (s.submitted_by.full_name if s.submitted_by else s.submitted_by_id)[:25],
            str(s.status.value if hasattr(s.status, "value") else s.status),
            str(s.review_status.value if hasattr(s.review_status, "value") else s.review_status),
            s.collected_at or "",
            str(s.gps_latitude or ""),
            str(s.gps_longitude or ""),
        ])
    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f2937")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("FONTSIZE", (0, 0), (-1, -1), 7),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(table)
    doc.build(story)
    output.seek(0)
    return StreamingResponse(iter([output.getvalue()]), media_type="application/pdf", headers={"Content-Disposition": "attachment; filename=kbs-submissions.pdf"})
