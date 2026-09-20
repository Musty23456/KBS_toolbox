from collections import Counter
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.dependencies import require_roles
from app.models.question import Question
from app.models.submission import Submission, SubmissionStatus
from app.models.survey import Survey, SurveyStatus, SurveyVersion
from app.models.user import RoleName, User

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


def _date_key(value: str | None) -> str:
    if not value:
        return "Unknown"
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).date().isoformat()
    except ValueError:
        return "Unknown"


def _filtered_query(db: Session, survey_id: str | None, date_from: str | None, date_to: str | None):
    query = db.query(Submission).options(joinedload(Submission.answers)).order_by(Submission.created_at.asc())
    if survey_id:
        query = query.filter(Submission.survey_id == survey_id)
    if date_from:
        query = query.filter(Submission.collected_at >= date_from)
    if date_to:
        query = query.filter(Submission.collected_at <= f"{date_to}T23:59:59")
    return query


@router.get("/overview")
def overview(
    survey_id: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RoleName.ADMINISTRATOR, RoleName.SUPERVISOR)),
):
    submissions = _filtered_query(db, survey_id, date_from, date_to).all()
    status_counts = Counter(s.status.value for s in submissions)
    review_counts = Counter(s.review_status.value for s in submissions)
    by_date = Counter(_date_key(s.collected_at or s.created_at) for s in submissions)
    by_enumerator = Counter(s.submitted_by_id for s in submissions)

    surveys = db.query(Survey).filter(Survey.status != SurveyStatus.ARCHIVED).all()
    survey_counts = Counter(s.survey_id for s in submissions)
    survey_rows = []
    for survey in surveys:
        survey_rows.append({"survey_id": survey.id, "title": survey.title, "submissions": survey_counts.get(survey.id, 0)})
    survey_rows.sort(key=lambda x: x["submissions"], reverse=True)

    users = {u.id: u.full_name for u in db.query(User).all()}
    enumerator_rows = [
        {"user_id": uid, "name": users.get(uid, "Unknown"), "submissions": count}
        for uid, count in by_enumerator.items()
    ]
    enumerator_rows.sort(key=lambda x: x["submissions"], reverse=True)

    return {
        "total_submissions": len(submissions),
        "synced_submissions": sum(s.status in (SubmissionStatus.SYNCED, SubmissionStatus.UPLOADED) for s in submissions),
        "failed_submissions": status_counts.get(SubmissionStatus.FAILED.value, 0),
        "unique_enumerators": len(by_enumerator),
        "active_days": len([k for k in by_date if k != "Unknown"]),
        "submissions_over_time": [
            {"date": date, "count": count}
            for date, count in sorted(by_date.items())
        ],
        "status_distribution": [{"name": name, "value": value} for name, value in sorted(status_counts.items())],
        "review_distribution": [{"name": name, "value": value} for name, value in sorted(review_counts.items())],
        "enumerator_performance": enumerator_rows,
        "survey_comparison": survey_rows,
    }


@router.get("/questions")
def question_statistics(
    survey_id: str,
    question_id: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RoleName.ADMINISTRATOR, RoleName.SUPERVISOR)),
):
    # Question belongs to a survey VERSION, not directly to a survey, so we
    # go through the survey's current version to find its live questions.
    current_version = (
        db.query(SurveyVersion)
        .filter(SurveyVersion.survey_id == survey_id, SurveyVersion.is_current.is_(True))
        .first()
    )
    questions = (
        db.query(Question)
        .filter(Question.survey_version_id == current_version.id)
        .order_by(Question.order_index.asc())
        .all()
        if current_version
        else []
    )
    submissions = _filtered_query(db, survey_id, None, None).all()
    answer_map = {s.id: {a.question_id: a for a in s.answers} for s in submissions}
    selected = [q for q in questions if not question_id or q.id == question_id]
    results = []
    for q in selected:
        answered = 0
        counts = Counter()
        for sid, answers in answer_map.items():
            answer = answers.get(q.id)
            if not answer or not answer.value_text:
                continue
            answered += 1
            raw = answer.value_text
            try:
                import json
                parsed = json.loads(raw)
                values = parsed if isinstance(parsed, list) else [raw]
            except Exception:
                values = [raw]
            for value in values:
                counts[str(value)] += 1
        choice_labels = {c.value: c.label for c in q.choices}
        distribution = [{"name": choice_labels.get(value, value), "value": count} for value, count in counts.most_common()]
        results.append({
            "question_id": q.id,
            "code": q.code,
            "label": q.label,
            "type": q.type.value if hasattr(q.type, "value") else str(q.type),
            "response_count": answered,
            "missing_count": len(submissions) - answered,
            "distribution": distribution,
        })
    return results
