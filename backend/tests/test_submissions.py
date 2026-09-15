from tests.conftest import register_and_login


def _create_published_survey(client, headers):
    payload = {
        "title": "Business Survey 2026",
        "description": "Test",
        "questions": [
            {
                "code": "business_name",
                "label": "Business Name",
                "type": "SHORT_TEXT",
                "order_index": 1,
                "is_required": True,
                "min_length": 2,
                "max_length": 100,
            },
            {
                "code": "employee_count",
                "label": "Employees",
                "type": "INTEGER",
                "order_index": 2,
                "is_required": True,
                "min_value": 0,
                "max_value": 1000,
            },
            {
                "code": "is_registered",
                "label": "Registered?",
                "type": "YES_NO",
                "order_index": 3,
                "is_required": True,
            },
            {
                "code": "registration_number",
                "label": "Registration Number",
                "type": "SHORT_TEXT",
                "order_index": 4,
                "relevance_expression": "is_registered == 'YES'",
                "regex_pattern": r"^[A-Z0-9\-]{4,20}$",
            },
        ],
    }
    survey = client.post("/api/surveys", json=payload, headers=headers).json()
    publish_resp = client.post(f"/api/surveys/{survey['id']}/publish", headers=headers)
    return publish_resp.json()


def _question_id(survey, code):
    return next(q["id"] for q in survey["questions"] if q["code"] == code)


def test_submission_happy_path(client):
    headers = register_and_login(client, email="admin@subtest.local", role="ADMINISTRATOR")
    survey = _create_published_survey(client, headers)

    payload = {
        "client_submission_uuid": "11111111-1111-1111-1111-111111111111",
        "survey_id": survey["id"],
        "survey_version_id": survey["current_version_id"],
        "answers": [
            {"question_id": _question_id(survey, "business_name"), "value_text": "Acme Traders"},
            {"question_id": _question_id(survey, "employee_count"), "value_text": "12"},
            {"question_id": _question_id(survey, "is_registered"), "value_text": "NO"},
        ],
    }
    resp = client.post("/api/submissions", json=payload, headers=headers)
    assert resp.status_code == 201
    body = resp.json()
    assert body["status"] == "SYNCED"
    assert len(body["answers"]) == 3


def test_submission_missing_required_field_rejected(client):
    headers = register_and_login(client, email="admin2@subtest.local", role="ADMINISTRATOR")
    survey = _create_published_survey(client, headers)

    payload = {
        "client_submission_uuid": "22222222-2222-2222-2222-222222222222",
        "survey_id": survey["id"],
        "survey_version_id": survey["current_version_id"],
        "answers": [
            {"question_id": _question_id(survey, "employee_count"), "value_text": "12"},
        ],
    }
    resp = client.post("/api/submissions", json=payload, headers=headers)
    assert resp.status_code == 422


def test_submission_relevance_skips_validation_of_hidden_field(client):
    """registration_number is only relevant when is_registered == YES; leaving
    it blank while NO must still pass validation."""
    headers = register_and_login(client, email="admin3@subtest.local", role="ADMINISTRATOR")
    survey = _create_published_survey(client, headers)

    payload = {
        "client_submission_uuid": "33333333-3333-3333-3333-333333333333",
        "survey_id": survey["id"],
        "survey_version_id": survey["current_version_id"],
        "answers": [
            {"question_id": _question_id(survey, "business_name"), "value_text": "Acme"},
            {"question_id": _question_id(survey, "employee_count"), "value_text": "5"},
            {"question_id": _question_id(survey, "is_registered"), "value_text": "NO"},
        ],
    }
    resp = client.post("/api/submissions", json=payload, headers=headers)
    assert resp.status_code == 201


def test_submission_regex_validation_enforced_when_relevant(client):
    headers = register_and_login(client, email="admin5@subtest.local", role="ADMINISTRATOR")
    survey = _create_published_survey(client, headers)

    payload = {
        "client_submission_uuid": "55555555-5555-5555-5555-555555555555",
        "survey_id": survey["id"],
        "survey_version_id": survey["current_version_id"],
        "answers": [
            {"question_id": _question_id(survey, "business_name"), "value_text": "Acme"},
            {"question_id": _question_id(survey, "employee_count"), "value_text": "5"},
            {"question_id": _question_id(survey, "is_registered"), "value_text": "YES"},
            {"question_id": _question_id(survey, "registration_number"), "value_text": "not-valid!!"},
        ],
    }
    resp = client.post("/api/submissions", json=payload, headers=headers)
    assert resp.status_code == 422


def test_submission_is_idempotent_on_client_uuid(client):
    headers = register_and_login(client, email="admin4@subtest.local", role="ADMINISTRATOR")
    survey = _create_published_survey(client, headers)

    payload = {
        "client_submission_uuid": "44444444-4444-4444-4444-444444444444",
        "survey_id": survey["id"],
        "survey_version_id": survey["current_version_id"],
        "answers": [
            {"question_id": _question_id(survey, "business_name"), "value_text": "Acme"},
            {"question_id": _question_id(survey, "employee_count"), "value_text": "5"},
            {"question_id": _question_id(survey, "is_registered"), "value_text": "NO"},
        ],
    }
    first = client.post("/api/submissions", json=payload, headers=headers)
    second = client.post("/api/submissions", json=payload, headers=headers)
    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["id"] == second.json()["id"]

    listing = client.get("/api/submissions", headers=headers).json()
    matching = [s for s in listing if s["client_submission_uuid"] == payload["client_submission_uuid"]]
    assert len(matching) == 1


def test_enumerator_cannot_list_all_submissions(client):
    admin_headers = register_and_login(client, email="admin6@subtest.local", role="ADMINISTRATOR")
    enum_headers = register_and_login(client, email="enum2@subtest.local", role="ENUMERATOR")
    _create_published_survey(client, admin_headers)

    resp = client.get("/api/submissions", headers=enum_headers)
    assert resp.status_code == 403
