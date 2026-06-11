from app.core.security import get_password_hash
from app.db.session import get_db
from app.models import User
from tests.conftest import auth_headers, create_user


def test_recruiter_posts_job_and_candidate_applies(client):
    create_user(client, "recruiter@example.com", "recruiter")
    create_user(client, "candidate@example.com", "candidate")
    recruiter_headers = auth_headers(client, "recruiter@example.com")
    candidate_headers = auth_headers(client, "candidate@example.com")

    company = client.post("/recruiter/companies", json={"name": "Acme"}, headers=recruiter_headers)
    assert company.status_code == 201

    job = client.post(
        "/recruiter/jobs",
        json={
            "title": "Backend Engineer",
            "description": "Build APIs",
            "location": "Remote",
            "company_id": company.json()["id"],
            "skills": ["Python", "FastAPI"],
        },
        headers=recruiter_headers,
    )
    assert job.status_code == 201

    search = client.get("/jobs", params={"keyword": "backend", "skills": "python"})
    assert search.status_code == 200
    assert len(search.json()) == 1

    application = client.post(
        f"/candidate/jobs/{job.json()['id']}/apply",
        json={"cover_letter": "Hello"},
        headers=candidate_headers,
    )
    assert application.status_code == 201

    applicants = client.get(f"/recruiter/jobs/{job.json()['id']}/applicants", headers=recruiter_headers)
    assert applicants.status_code == 200
    assert len(applicants.json()) == 1


def test_admin_analytics(client):
    db = next(client.app.dependency_overrides[get_db]())
    admin = User(
        email="admin@example.com",
        full_name="Admin",
        role="admin",
        hashed_password=get_password_hash("password123"),
        is_active=True,
        is_verified=True,
    )
    db.add(admin)
    db.commit()
    db.close()

    response = client.get("/admin/analytics", headers=auth_headers(client, "admin@example.com"))
    assert response.status_code == 200
    assert response.json()["total_users"] == 1
