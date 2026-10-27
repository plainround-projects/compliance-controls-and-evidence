import pytest

from notes_evidence.domain.roles import Role
from notes_evidence.interfaces.http_app import create_app
from tests.conftest import Rig


@pytest.fixture
def rig() -> Rig:
    rig = Rig()
    rig.add_user("ada", Role.ADMIN, "admin-password-1")
    rig.add_user("bruno", Role.MEMBER, "member-password-1")
    rig.add_user("chen", Role.MEMBER, "member-password-2")
    return rig


@pytest.fixture
def client(rig):
    healthy = {"up": True}
    app = create_app(rig.service, lambda: healthy["up"])
    app.testing = False
    test_client = app.test_client()
    test_client.healthy = healthy  # type: ignore[attr-defined]
    return test_client


def token(client, name, password):
    return client.post("/login", json={"username": name, "password": password}).get_json()["token"]


def auth(client, name="bruno", password="member-password-1"):
    return {"Authorization": f"Bearer {token(client, name, password)}"}


def test_health_reports_the_database(client):
    response = client.get("/healthz")
    assert (response.status_code, response.get_json()) == (200, {"status": "ok"})
    client.healthy["up"] = False
    assert client.get("/healthz").status_code == 503


def test_login_returns_a_token_and_a_wrong_password_is_401(client):
    assert client.post("/login", json={"username": "bruno", "password": "member-password-1"}).status_code == 200
    bad = client.post("/login", json={"username": "bruno", "password": "nope"})
    assert (bad.status_code, bad.get_json()) == (401, {"error": "invalid username or password"})


def test_a_login_that_is_not_json_is_400(client):
    assert client.post("/login", data="x", content_type="text/plain").status_code == 400


def test_the_notes_lifecycle_over_http(client):
    headers = auth(client)
    created = client.post("/notes", json={"title": "First", "body": "text"}, headers=headers)
    assert created.status_code == 201
    note_id = created.get_json()["id"]
    assert client.get(f"/notes/{note_id}", headers=headers).get_json()["title"] == "First"
    assert [n["id"] for n in client.get("/notes", headers=headers).get_json()["notes"]] == [note_id]
    updated = client.put(f"/notes/{note_id}", json={"title": "Second", "body": "more"}, headers=headers)
    assert updated.get_json()["title"] == "Second"
    assert client.delete(f"/notes/{note_id}", headers=headers).status_code == 204
    assert client.get(f"/notes/{note_id}", headers=headers).status_code == 404


def test_requests_without_a_valid_token_are_401(client):
    assert client.get("/notes").status_code == 401
    assert client.get("/notes", headers={"Authorization": "Basic abc"}).status_code == 401
    assert client.get("/notes", headers={"Authorization": "Bearer nonsense"}).status_code == 401


def test_validation_errors_are_400_with_the_field(client):
    response = client.post("/notes", json={"title": "", "body": "x"}, headers=auth(client))
    assert response.status_code == 400
    assert response.get_json()["error"].startswith("title:")
    assert client.post("/notes", data="[]", content_type="application/json", headers=auth(client)).status_code == 400


def test_another_members_note_is_404_and_a_wrong_role_is_403(client):
    note_id = client.post(
        "/notes", json={"title": "Private", "body": "x"}, headers=auth(client, "chen", "member-password-2")
    ).get_json()["id"]
    assert client.get(f"/notes/{note_id}", headers=auth(client)).status_code == 404
    assert client.put("/users/chen/role", json={"role": "admin"}, headers=auth(client)).status_code == 403


def test_an_admin_grants_a_role(client, rig):
    response = client.put("/users/chen/role", json={"role": "admin"}, headers=auth(client, "ada", "admin-password-1"))
    assert (response.status_code, response.get_json()) == (200, {"role": "admin", "username": "chen"})
    assert rig.audit.events[-1].detail == {"role": "admin", "target": "chen"}
    bad = client.put("/users/chen/role", json={"role": "root"}, headers=auth(client, "ada", "admin-password-1"))
    assert bad.status_code == 400
    assert (
        client.put(
            "/users/nobody/role", json={"role": "member"}, headers=auth(client, "ada", "admin-password-1")
        ).status_code
        == 404
    )


def test_unknown_routes_and_oversized_bodies_get_json_errors(client):
    assert client.get("/nope").get_json() == {"error": "not found"}
    assert client.post("/login", data="x" * 70_000, content_type="application/json").status_code == 413


def test_responses_are_not_cached_and_not_sniffed(client):
    response = client.get("/healthz")
    assert response.headers["Cache-Control"] == "no-store"
    assert response.headers["X-Content-Type-Options"] == "nosniff"


def test_an_unexpected_error_is_a_generic_500_without_details(rig):
    def boom():
        raise RuntimeError("database password is hunter2")

    app = create_app(rig.service, boom)
    app.testing = False
    response = app.test_client().get("/healthz")
    assert response.status_code == 500
    assert response.get_json() == {"error": "internal error"}
