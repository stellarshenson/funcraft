"""The Swagger explorer and its schema: the docs endpoints are public and the schema names the auth schemes."""
import app
from fastapi.testclient import TestClient

PATHS = ["/", "/health", "/login", "/logout", "/session", "/tokens", "/tokens/{name}", "/settings",
         "/settings/hf-token", "/voices", "/voices/{name}", "/speak"]


def test_docs_and_redoc_are_public_html():
    """GET /docs serves the Swagger UI and GET /redoc the ReDoc page, both as HTML without a login."""
    client = TestClient(app.app)
    docs = client.get("/docs")
    assert docs.status_code == 200
    assert docs.headers["content-type"].startswith("text/html")
    assert "swagger-ui" in docs.text
    redoc = client.get("/redoc")
    assert redoc.status_code == 200
    assert redoc.headers["content-type"].startswith("text/html")


def test_the_schema_lists_every_endpoint():
    """GET /openapi.json is public and its paths cover the whole API."""
    response = TestClient(app.app).get("/openapi.json")
    assert response.status_code == 200
    assert set(PATHS) <= set(response.json()["paths"])


def test_the_schema_declares_the_bearer_and_cookie_schemes():
    """The schema names the Bearer token and the `sid` session cookie, so Swagger's Authorize button can use them."""
    schemes = TestClient(app.app).get("/openapi.json").json()["components"]["securitySchemes"]
    assert (schemes["HTTPBearer"]["type"], schemes["HTTPBearer"]["scheme"]) == ("http", "bearer")
    assert (schemes["APIKeyCookie"]["type"], schemes["APIKeyCookie"]["in"],
            schemes["APIKeyCookie"]["name"]) == ("apiKey", "cookie", "sid")


def test_the_schema_marks_the_auth_of_speak_tokens_and_health():
    """/speak needs the Bearer token, /tokens the session cookie, and /health is public."""
    paths = TestClient(app.app).get("/openapi.json").json()["paths"]
    assert paths["/speak"]["post"]["security"] == [{"HTTPBearer": []}]
    assert paths["/tokens"]["get"]["security"] == [{"APIKeyCookie": []}]
    assert "security" not in paths["/health"]["get"]
