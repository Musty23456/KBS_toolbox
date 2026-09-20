"""
Seeds demo data so the platform can be tried out immediately:
- One user per role (administrator, supervisor, enumerator)
- Three published demo surveys with realistic questions and conditional logic:
    1. Household Survey 2026 (skip logic on gender/age, cascading location)
    2. Business Survey 2026
    3. Population Survey 2026

Run with:  python -m app.seed
"""
from app.config import get_settings
from app.database import Base, SessionLocal, engine
from app.models.location import Location
from app.models.question import Choice, Question, QuestionType
from app.models.survey import Survey, SurveyStatus, SurveyVersion
from app.models.user import RoleName, User
from app.security import hash_password

settings = get_settings()


def _get_or_create_user(db, full_name, email, password, role):
    user = db.query(User).filter(User.email == email).first()
    if user:
        return user
    user = User(full_name=full_name, email=email, hashed_password=hash_password(password), role=role)
    db.add(user)
    db.flush()
    return user


def _get_or_create_survey(db, title, description, created_by_id):
    survey = db.query(Survey).filter(Survey.title == title).first()
    if survey:
        return survey, False
    survey = Survey(title=title, description=description, created_by_id=created_by_id, status=SurveyStatus.PUBLISHED)
    db.add(survey)
    db.flush()
    return survey, True


def seed_locations(db):
    if db.query(Location).first():
        return
    states = {
        "Lagos": ["Ikeja", "Eti-Osa", "Alimosho"],
        "Kano": ["Nassarawa", "Fagge", "Dala"],
        "Rivers": ["Port Harcourt", "Obio-Akpor", "Eleme"],
    }
    for state_name, lgas in states.items():
        state = Location(name=state_name, level=0)
        db.add(state)
        db.flush()
        for lga_name in lgas:
            db.add(Location(name=lga_name, level=1, parent_id=state.id))
    db.flush()


def seed_household_survey(db, created_by_id):
    survey, created = _get_or_create_survey(
        db, "Household Survey 2026", "National household demographic and welfare survey.", created_by_id
    )
    if not created:
        return survey

    version = SurveyVersion(survey_id=survey.id, version_number=1, is_current=True)
    db.add(version)
    db.flush()

    q_name = Question(survey_version_id=version.id, code="full_name", label="Full Name",
                       type=QuestionType.SHORT_TEXT, order_index=1, is_required=True, min_length=2, max_length=120)
    q_age = Question(survey_version_id=version.id, code="age_years", label="Age (years)",
                      type=QuestionType.INTEGER, order_index=2, is_required=True, min_value=0, max_value=120)
    q_gender = Question(survey_version_id=version.id, code="gender", label="Gender",
                         type=QuestionType.SINGLE_CHOICE, order_index=3, is_required=True)
    q_state = Question(survey_version_id=version.id, code="state", label="State",
                        type=QuestionType.DROPDOWN, order_index=4, is_required=True)
    q_lga = Question(survey_version_id=version.id, code="lga", label="LGA",
                      type=QuestionType.DROPDOWN, order_index=5, is_required=True,
                      cascade_parent_question_id=None)  # linked below once q_state has an id
    q_gps = Question(survey_version_id=version.id, code="gps_location", label="GPS Location",
                      type=QuestionType.GPS, order_index=6, is_required=True)
    q_household_size = Question(survey_version_id=version.id, code="household_size", label="Household Size",
                                 type=QuestionType.INTEGER, order_index=7, is_required=True, min_value=1, max_value=50)
    q_is_pregnant = Question(
        survey_version_id=version.id, code="is_pregnant", label="Is currently pregnant?",
        type=QuestionType.YES_NO, order_index=8,
        relevance_expression="gender == 'FEMALE' and age_years >= 12 and age_years <= 55",
    )
    q_adult_consent = Question(
        survey_version_id=version.id, code="adult_consent", label="Consent to further adult questions",
        type=QuestionType.YES_NO, order_index=9,
        relevance_expression="age_years >= 18",
    )
    q_photo = Question(survey_version_id=version.id, code="dwelling_photo", label="Photo of Dwelling",
                        type=QuestionType.PHOTO, order_index=10)
    q_signature = Question(survey_version_id=version.id, code="respondent_signature", label="Respondent Signature",
                            type=QuestionType.SIGNATURE, order_index=11, is_required=True)

    db.add_all([q_name, q_age, q_gender, q_state, q_lga, q_gps, q_household_size,
                q_is_pregnant, q_adult_consent, q_photo, q_signature])
    db.flush()

    q_lga.cascade_parent_question_id = q_state.id

    db.add_all([
        Choice(question_id=q_gender.id, value="MALE", label="Male", order_index=1),
        Choice(question_id=q_gender.id, value="FEMALE", label="Female", order_index=2),
    ])
    for state_name in ("Lagos", "Kano", "Rivers"):
        db.add(Choice(question_id=q_state.id, value=state_name.upper(), label=state_name))
    lga_map = {
        "LAGOS": ["Ikeja", "Eti-Osa", "Alimosho"],
        "KANO": ["Nassarawa", "Fagge", "Dala"],
        "RIVERS": ["Port Harcourt", "Obio-Akpor", "Eleme"],
    }
    for state_value, lgas in lga_map.items():
        for lga_name in lgas:
            db.add(Choice(question_id=q_lga.id, value=lga_name.upper().replace(" ", "_"),
                          label=lga_name, cascade_parent_value=state_value))

    db.commit()
    return survey


def seed_business_survey(db, created_by_id):
    survey, created = _get_or_create_survey(
        db, "Business Survey 2026", "Micro/small business registration and activity survey.", created_by_id
    )
    if not created:
        return survey

    version = SurveyVersion(survey_id=survey.id, version_number=1, is_current=True)
    db.add(version)
    db.flush()

    q_business_name = Question(survey_version_id=version.id, code="business_name", label="Business Name",
                                type=QuestionType.SHORT_TEXT, order_index=1, is_required=True, max_length=200)
    q_sector = Question(survey_version_id=version.id, code="sector", label="Business Sector",
                         type=QuestionType.SINGLE_CHOICE, order_index=2, is_required=True)
    q_employees = Question(survey_version_id=version.id, code="employee_count", label="Number of Employees",
                            type=QuestionType.INTEGER, order_index=3, is_required=True, min_value=0, max_value=10000)
    q_registered = Question(survey_version_id=version.id, code="is_registered", label="Is the business formally registered?",
                             type=QuestionType.YES_NO, order_index=4, is_required=True)
    q_reg_number = Question(
        survey_version_id=version.id, code="registration_number", label="Registration Number",
        type=QuestionType.SHORT_TEXT, order_index=5,
        relevance_expression="is_registered == 'YES'", regex_pattern=r"^[A-Z0-9\-]{4,20}$",
    )
    q_barcode = Question(survey_version_id=version.id, code="asset_tag", label="Scan Asset Barcode/QR",
                          type=QuestionType.BARCODE, order_index=6)
    q_gps = Question(survey_version_id=version.id, code="business_location", label="Business GPS Location",
                      type=QuestionType.GPS, order_index=7, is_required=True)
    q_notes = Question(survey_version_id=version.id, code="field_notes", label="Enumerator Notes",
                        type=QuestionType.LONG_TEXT, order_index=8, max_length=2000)

    db.add_all([q_business_name, q_sector, q_employees, q_registered, q_reg_number, q_barcode, q_gps, q_notes])
    db.flush()

    for i, sector in enumerate(["Retail/Trade", "Agriculture", "Manufacturing", "Services", "Technology"], start=1):
        db.add(Choice(question_id=q_sector.id, value=sector.upper().replace("/", "_"), label=sector, order_index=i))

    db.commit()
    return survey


def seed_population_survey(db, created_by_id):
    survey, created = _get_or_create_survey(
        db, "Population Survey 2026", "General population census-style enumeration survey.", created_by_id
    )
    if not created:
        return survey

    version = SurveyVersion(survey_id=survey.id, version_number=1, is_current=True)
    db.add(version)
    db.flush()

    q_full_name = Question(survey_version_id=version.id, code="full_name", label="Full Name",
                            type=QuestionType.SHORT_TEXT, order_index=1, is_required=True, max_length=120)
    q_dob = Question(survey_version_id=version.id, code="date_of_birth", label="Date of Birth",
                      type=QuestionType.DATE, order_index=2, is_required=True)
    q_marital_status = Question(survey_version_id=version.id, code="marital_status", label="Marital Status",
                                 type=QuestionType.DROPDOWN, order_index=3, is_required=True)
    q_education = Question(survey_version_id=version.id, code="education_level", label="Highest Education Level",
                            type=QuestionType.DROPDOWN, order_index=4, is_required=True)
    q_occupation = Question(survey_version_id=version.id, code="occupation", label="Occupation",
                             type=QuestionType.SHORT_TEXT, order_index=5, max_length=150)
    q_disability = Question(survey_version_id=version.id, code="has_disability", label="Living with a disability?",
                             type=QuestionType.YES_NO, order_index=6)
    q_disability_type = Question(
        survey_version_id=version.id, code="disability_type", label="Type of disability",
        type=QuestionType.MULTIPLE_CHOICE, order_index=7,
        relevance_expression="has_disability == 'YES'",
    )
    q_interview_time = Question(survey_version_id=version.id, code="interview_datetime", label="Interview Date & Time",
                                 type=QuestionType.DATETIME, order_index=8, is_required=True)
    q_audio = Question(survey_version_id=version.id, code="interview_audio", label="Interview Audio Recording (optional)",
                        type=QuestionType.AUDIO, order_index=9)

    db.add_all([q_full_name, q_dob, q_marital_status, q_education, q_occupation,
                q_disability, q_disability_type, q_interview_time, q_audio])
    db.flush()

    for i, status_ in enumerate(["Single", "Married", "Divorced", "Widowed"], start=1):
        db.add(Choice(question_id=q_marital_status.id, value=status_.upper(), label=status_, order_index=i))
    for i, level in enumerate(["None", "Primary", "Secondary", "Tertiary", "Postgraduate"], start=1):
        db.add(Choice(question_id=q_education.id, value=level.upper(), label=level, order_index=i))
    for i, d_type in enumerate(["Visual", "Hearing", "Mobility", "Cognitive", "Other"], start=1):
        db.add(Choice(question_id=q_disability_type.id, value=d_type.upper(), label=d_type, order_index=i))

    db.commit()
    return survey


def run():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        admin = _get_or_create_user(db, "System Administrator", settings.DEMO_ADMIN_EMAIL,
                                     settings.DEMO_ADMIN_PASSWORD, RoleName.ADMINISTRATOR)
        _get_or_create_user(db, "Demo Supervisor", "supervisor@kbstoolbox.app", "ChangeMe123!", RoleName.SUPERVISOR)
        _get_or_create_user(db, "Demo Enumerator", "enumerator@kbstoolbox.app", "ChangeMe123!", RoleName.ENUMERATOR)
        db.commit()

        seed_locations(db)
        seed_household_survey(db, admin.id)
        seed_business_survey(db, admin.id)
        seed_population_survey(db, admin.id)

        print("Seed complete.")
        print(f"  Admin login:      {settings.DEMO_ADMIN_EMAIL} / {settings.DEMO_ADMIN_PASSWORD}")
        print("  Supervisor login: supervisor@kbstoolbox.app / ChangeMe123!")
        print("  Enumerator login: enumerator@kbstoolbox.app / ChangeMe123!")
    finally:
        db.close()


if __name__ == "__main__":
    run()
