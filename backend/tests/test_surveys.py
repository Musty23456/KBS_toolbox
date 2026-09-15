from tests.conftest import register_and_login


def _sample_survey_payload():
    return {
        "title": "Household Survey 2026",
        "description": "Test survey",
        "questions": [
            {
                "code": "full_name",
                "label": "Full Name",
                "type": "SHORT_TEXT",
                "order_index": 1,
                "is_required": True,
                "min_length": 2,
                "max_length": 100,
            },
            {
                "code": "age_years",
                "label": "Age",
                "type": "INTEGER",
                "order_index": 2,
                "is_required": True,
                "min_value": 0,
                "max_value": 120,
            },
            {
                "code": "gender",
                "label": "Gender",
                "type": "SINGLE_CHOICE",
                "order_index": 3,
                "is_required": True,
                "choices": [
                    {"value": "MALE", "label": "Male", "order_index": 1},
                    {"value": "FEMALE", "label": "Female", "order_index": 2},
                ],
            },
            {
                "code": "is_pregnant",
                "label": "Currently pregnant?",
                "type": "YES_NO",
                "order_index": 4,
                "relevance_expression": "gender == 'FEMALE'",
            },
        ],
    }


def test_enumerator_cannot_create_survey(client):
    headers = register_and_login(client, email="enum@test.local", role="ENUMERATOR")
    resp = client.post("/api/surveys", json=_sample_survey_payload(), headers=headers)
    assert resp.status_code == 403


def test_administrator_can_create_and_publish_survey(client):
    headers = register_and_login(client, email="admin2@test.local", role="ADMINISTRATOR")
    resp = client.post("/api/surveys", json=_sample_survey_payload(), headers=headers)
    assert resp.status_code == 201
    survey = resp.json()
    assert survey["status"] == "DRAFT"
    assert len(survey["questions"]) == 4

    publish_resp = client.post(f"/api/surveys/{survey['id']}/publish", headers=headers)
    assert publish_resp.status_code == 200
    assert publish_resp.json()["status"] == "PUBLISHED"


def test_updating_questions_creates_new_version(client):
    headers = register_and_login(client, email="admin3@test.local", role="ADMINISTRATOR")
    survey = client.post("/api/surveys", json=_sample_survey_payload(), headers=headers).json()
    assert survey["current_version_number"] == 1

    updated_payload = _sample_survey_payload()
    updated_payload["questions"].append(
        {"code": "notes", "label": "Notes", "type": "LONG_TEXT", "order_index": 5}
    )
    resp = client.put(f"/api/surveys/{survey['id']}", json=updated_payload, headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["current_version_number"] == 2
    assert len(body["questions"]) == 5


def test_list_surveys_requires_authentication(client):
    resp = client.get("/api/surveys")
    assert resp.status_code == 401
