"""Who may see / edit / archive a survey.

Rules
-----
* GLOBAL surveys are created by administrators. Enumerators see them subject
  to the existing assignment restriction (no assignments = open to everyone).
* PERSONAL surveys belong to whoever created them. The owner always sees them.
  People the owner has shared a PUBLISHED personal survey with can see and fill
  it (fill-only): they cannot edit, publish, share or archive it.
"""

from app.models.survey import Survey, SurveyScope, SurveyStatus
from app.models.user import RoleName, User


def is_owner(user: User, survey: Survey) -> bool:
    return survey.created_by_id == user.id


def is_shared_with(user: User, survey: Survey) -> bool:
    """True when a *published* personal survey has been shared with this user."""
    return (
        survey.scope == SurveyScope.PERSONAL.value
        and survey.status == SurveyStatus.PUBLISHED
        and user.id in {u.id for u in survey.shared_with}
    )


def can_share(user: User, survey: Survey) -> bool:
    """Only the owner shares, and only personal surveys (global ones use assignments)."""
    return survey.scope == SurveyScope.PERSONAL.value and is_owner(user, survey)


def can_create_global(user: User) -> bool:
    return user.role == RoleName.ADMINISTRATOR


def can_view(user: User, survey: Survey) -> bool:
    """Direct access by id (open, review submissions, fill)."""
    if user.role == RoleName.ADMINISTRATOR or is_owner(user, survey):
        return True
    if survey.scope == SurveyScope.PERSONAL.value:
        return is_shared_with(user, survey)
    if user.role == RoleName.ENUMERATOR:
        assigned = {u.id for u in survey.assigned_enumerators}
        return not assigned or user.id in assigned
    return True  # supervisors see every global survey


def is_listed(user: User, survey: Survey) -> bool:
    """What appears in a user's survey list and in sync/download.

    Stricter than ``can_view`` for administrators: they see global surveys and
    their own personal ones, not everyone else's personal drafts.
    """
    if survey.scope == SurveyScope.PERSONAL.value:
        return is_owner(user, survey) or is_shared_with(user, survey)
    return can_view(user, survey)


def can_edit(user: User, survey: Survey) -> bool:
    if survey.scope == SurveyScope.PERSONAL.value:
        return is_owner(user, survey)
    return user.role in (RoleName.ADMINISTRATOR, RoleName.SUPERVISOR)


def can_archive(user: User, survey: Survey) -> bool:
    if survey.scope == SurveyScope.PERSONAL.value:
        return is_owner(user, survey) or user.role == RoleName.ADMINISTRATOR
    return user.role == RoleName.ADMINISTRATOR


def is_staff(user: User) -> bool:
    return user.role in (RoleName.ADMINISTRATOR, RoleName.SUPERVISOR)


def owns_personal_survey(user: User, survey: Survey | None) -> bool:
    return bool(survey) and survey.scope == SurveyScope.PERSONAL.value and is_owner(user, survey)


def can_view_results(user: User, survey: Survey | None) -> bool:
    """Submissions / analytics / exports for a survey.

    Staff see results of every survey (unchanged). The owner of a personal
    survey sees all submissions to it, including those collected by the people
    it was shared with. Everyone else sees nothing.
    """
    if survey is None:
        return False
    return is_staff(user) or owns_personal_survey(user, survey)
