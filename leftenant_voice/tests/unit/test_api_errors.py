"""The API's error paths, with stub engines, no model and a logged-in client."""
import app
from engine import EngineError


def post(client, **body):
    """POST /speak with the grimaldus voice and the given body fields."""
    return client.post("/speak", json={"voice": "grimaldus", **body})


def test_empty_text_is_422_with_a_message(client):
    response = post(client, text="")
    assert response.status_code == 422
    assert "text is empty" in response.text


def test_whitespace_text_is_422_with_a_message(client):
    response = post(client, text="   \n ")
    assert response.status_code == 422
    assert "text is empty" in response.text


def test_missing_text_is_422(client):
    assert client.post("/speak", json={"voice": "grimaldus"}).status_code == 422


def test_too_long_text_is_422_and_names_the_limit(client, monkeypatch):
    monkeypatch.setattr(app, "MAX_TEXT_CHARS", 10)
    response = post(client, text="x" * 11)
    assert response.status_code == 422
    assert "limit is 10" in response.text


def test_unknown_voice_is_404_and_names_the_available_ones(client):
    response = post(client, text="hello", voice="nobody")
    assert response.status_code == 404
    assert "grimaldus" in response.text


def test_value_error_from_the_engine_is_422(client, engines):
    engines["alpha"].fail = ValueError("the text has no words to speak")
    response = post(client, text="hello")
    assert response.status_code == 422
    assert "no words" in response.text


def test_engine_error_is_500(client, engines):
    engines["alpha"].fail = EngineError("the model could not load")
    response = post(client, text="hello")
    assert response.status_code == 500
    assert "could not load" in response.text


def test_engine_error_unloads_the_engine_and_the_next_request_reloads(client, engines):
    engines["alpha"].fail = EngineError("the model could not speak")
    assert post(client, text="hello").status_code == 500
    assert engines["alpha"].unloads == 1
    assert app.loaded_engine is None
    engines["alpha"].fail = None
    assert post(client, text="hello").status_code == 200
    assert engines["alpha"].loads == 2
