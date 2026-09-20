from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.dependencies import get_current_user, require_roles
from app.models.question import Choice, Question
from app.models.group import QuestionGroup
from app.models.survey import Survey, SurveySection, SurveyStatus, SurveyVersion
from app.models.user import RoleName, User
from app.schemas.survey import (
    SurveyCreate,
    SurveyDetailOut,
    SurveySummaryOut,
    SurveyUpdate,
    SectionOut,
)
from app.services.audit import log_action

router = APIRouter(prefix="/api/surveys", tags=["surveys"])


def _current_version(survey: Survey) -> SurveyVersion | None:
    for version in survey.versions:
        if version.is_current:
            return version
    return survey.versions[-1] if survey.versions else None


def _to_detail(survey: Survey) -> SurveyDetailOut:
    version = _current_version(survey)
    return SurveyDetailOut(
        id=survey.id,
        title=survey.title,
        description=survey.description,
        status=survey.status,
        created_at=survey.created_at,
        current_version_number=version.version_number if version else None,
        current_version_id=version.id if version else None,
        sections=version.sections if version else [],
        groups=version.groups if version else [],
        questions=version.questions if version else [],
        assigned_enumerator_ids=[u.id for u in survey.assigned_enumerators],
    )


def _to_summary(survey: Survey) -> SurveySummaryOut:
    version = _current_version(survey)
    return SurveySummaryOut(
        id=survey.id,
        title=survey.title,
        description=survey.description,
        status=survey.status,
        created_at=survey.created_at,
        current_version_number=version.version_number if version else None,
        current_version_id=version.id if version else None,
        assigned_enumerator_ids=[u.id for u in survey.assigned_enumerators],
    )


def _load_survey_or_404(db: Session, survey_id: str) -> Survey:
    survey = (
        db.query(Survey)
        .options(
            joinedload(Survey.versions).joinedload(SurveyVersion.questions).joinedload(Question.choices),
            joinedload(Survey.versions).joinedload(SurveyVersion.sections),
            joinedload(Survey.versions).joinedload(SurveyVersion.groups),
            joinedload(Survey.assigned_enumerators),
        )
        .filter(Survey.id == survey_id)
        .first()
    )
    if not survey:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Survey not found")
    return survey


def _apply_assignments(db: Session, survey: Survey, enumerator_ids: list[str]) -> None:
    if enumerator_ids:
        users = db.query(User).filter(User.id.in_(enumerator_ids)).all()
        survey.assigned_enumerators = users
    else:
        survey.assigned_enumerators = []


def _write_version_sections(db: Session, version: SurveyVersion, sections_in):
    mapping = {}
    for s_in in sections_in:
        section = SurveySection(survey_version_id=version.id, title=s_in.title, description=s_in.description, order_index=s_in.order_index)
        db.add(section); db.flush(); mapping[s_in.order_index] = section.id
        mapping[f"local-{s_in.order_index - 1}"] = section.id
    return mapping


def _write_version_groups(db: Session, version: SurveyVersion, groups_in, section_map=None):
    mapping = {}
    for g_in in groups_in:
        group = QuestionGroup(
            survey_version_id=version.id,
            section_id=g_in.section_id if not section_map else section_map.get(g_in.section_id, g_in.section_id),
            title=g_in.title,
            description=g_in.description,
            order_index=g_in.order_index,
            repeatable=g_in.repeatable,
            min_repeats=g_in.min_repeats,
            max_repeats=g_in.max_repeats,
        )
        db.add(group); db.flush()
        mapping[g_in.order_index] = group.id
        mapping[f"local-{g_in.order_index - 1}"] = group.id
    return mapping

def _write_version_questions(db: Session, version: SurveyVersion, questions_in, section_map=None, group_map=None) -> None:
    for q_in in questions_in:
        question = Question(
            survey_version_id=version.id,
            code=q_in.code,
            label=q_in.label,
            hint=q_in.hint,
            type=q_in.type,
            order_index=q_in.order_index,
            is_required=q_in.is_required,
            min_value=q_in.min_value,
            max_value=q_in.max_value,
            min_length=q_in.min_length,
            max_length=q_in.max_length,
            regex_pattern=q_in.regex_pattern,
            relevance_expression=q_in.relevance_expression,
            calculation_expression=q_in.calculation_expression,
            default_value=q_in.default_value,
            cascade_parent_question_id=q_in.cascade_parent_question_id,
            section_id=q_in.section_id if not section_map else section_map.get(q_in.section_id, q_in.section_id),
            group_id=q_in.group_id if not group_map else group_map.get(q_in.group_id, q_in.group_id),
        )
        db.add(question)
        db.flush()  # get question.id for its choices
        for c_in in q_in.choices:
            db.add(
                Choice(
                    question_id=question.id,
                    value=c_in.value,
                    label=c_in.label,
                    order_index=c_in.order_index,
                    cascade_parent_value=c_in.cascade_parent_value,
                )
            )


@router.get("", response_model=list[SurveySummaryOut])
def list_surveys(
    status_filter: SurveyStatus | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Survey).options(joinedload(Survey.versions), joinedload(Survey.assigned_enumerators))
    if status_filter:
        query = query.filter(Survey.status == status_filter)
    surveys = query.order_by(Survey.created_at.desc()).all()

    if current_user.role == RoleName.ENUMERATOR:
        # An unassigned survey (no one restricted it) stays open to every
        # enumerator; an assigned survey only shows for the enumerators
        # picked for it.
        surveys = [
            s
            for s in surveys
            if not s.assigned_enumerators or current_user.id in {u.id for u in s.assigned_enumerators}
        ]

    return [_to_summary(s) for s in surveys]


@router.get("/{survey_id}", response_model=SurveyDetailOut)
def get_survey(survey_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    survey = _load_survey_or_404(db, survey_id)
    return _to_detail(survey)


@router.post("", response_model=SurveyDetailOut, status_code=status.HTTP_201_CREATED)
def create_survey(
    payload: SurveyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RoleName.ADMINISTRATOR, RoleName.SUPERVISOR)),
):
    survey = Survey(title=payload.title, description=payload.description, created_by_id=current_user.id)
    db.add(survey)
    db.flush()

    _apply_assignments(db, survey, payload.assigned_enumerator_ids)

    version = SurveyVersion(survey_id=survey.id, version_number=1, is_current=True)
    db.add(version)
    db.flush()

    section_map = _write_version_sections(db, version, payload.sections)
    group_map = _write_version_groups(db, version, payload.groups, section_map)
    _write_version_questions(db, version, payload.questions, section_map, group_map)

    db.commit()
    survey = _load_survey_or_404(db, survey.id)
    log_action(db, current_user.id, "SURVEY_CREATED", "Survey", survey.id)
    return _to_detail(survey)


@router.put("/{survey_id}", response_model=SurveyDetailOut)
def update_survey(
    survey_id: str,
    payload: SurveyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RoleName.ADMINISTRATOR, RoleName.SUPERVISOR)),
):
    """
    Editing title/description only patches the survey. Editing the question
    set creates a NEW immutable version (bumping version_number) so that
    historical submissions still point at the exact form they were
    collected against.
    """
    survey = _load_survey_or_404(db, survey_id)

    if payload.title is not None:
        survey.title = payload.title
    if payload.description is not None:
        survey.description = payload.description

    if payload.assigned_enumerator_ids is not None:
        _apply_assignments(db, survey, payload.assigned_enumerator_ids)

    if payload.questions is not None:
        current = _current_version(survey)
        for v in survey.versions:
            v.is_current = False
        new_version = SurveyVersion(
            survey_id=survey.id,
            version_number=(current.version_number + 1) if current else 1,
            is_current=True,
        )
        db.add(new_version)
        db.flush()
        section_map = _write_version_sections(db, new_version, payload.sections or [])
        group_map = _write_version_groups(db, new_version, payload.groups or [], section_map)
        _write_version_questions(db, new_version, payload.questions, section_map, group_map)

    db.commit()
    survey = _load_survey_or_404(db, survey.id)
    log_action(db, current_user.id, "SURVEY_UPDATED", "Survey", survey.id)
    return _to_detail(survey)


@router.post("/{survey_id}/publish", response_model=SurveyDetailOut)
def publish_survey(
    survey_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RoleName.ADMINISTRATOR, RoleName.SUPERVISOR)),
):
    survey = _load_survey_or_404(db, survey_id)
    if not survey.versions:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Add at least one question before publishing")
    survey.status = SurveyStatus.PUBLISHED
    db.commit()
    log_action(db, current_user.id, "SURVEY_PUBLISHED", "Survey", survey.id)
    return _to_detail(_load_survey_or_404(db, survey_id))


@router.post("/{survey_id}/unpublish", response_model=SurveyDetailOut)
def unpublish_survey(
    survey_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RoleName.ADMINISTRATOR, RoleName.SUPERVISOR)),
):
    survey = _load_survey_or_404(db, survey_id)
    survey.status = SurveyStatus.DRAFT
    db.commit()
    log_action(db, current_user.id, "SURVEY_UNPUBLISHED", "Survey", survey.id)
    return _to_detail(_load_survey_or_404(db, survey_id))


@router.delete("/{survey_id}", status_code=status.HTTP_204_NO_CONTENT)
def archive_survey(
    survey_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RoleName.ADMINISTRATOR)),
):
    """Archives rather than hard-deletes, preserving submission history."""
    survey = _load_survey_or_404(db, survey_id)
    survey.status = SurveyStatus.ARCHIVED
    db.commit()
    log_action(db, current_user.id, "SURVEY_ARCHIVED", "Survey", survey.id)
    return None
