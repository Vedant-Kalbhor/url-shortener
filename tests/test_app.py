from pathlib import Path
from runpy import run_path
from shutil import rmtree
from uuid import uuid4


APP_PATH = Path(__file__).resolve().parents[1] / "url-shorter-app.py"
APP_GLOBALS = run_path(str(APP_PATH), run_name="test_app")
app = APP_GLOBALS["app"]


def configure_db():
    temp_dir = Path(__file__).resolve().parents[1] / ".test-data" / uuid4().hex
    temp_dir.mkdir(parents=True, exist_ok=False)
    db_file = str(temp_dir / "data.json")
    APP_GLOBALS["DB_FILE"] = db_file
    APP_GLOBALS["load_db"].__globals__["DB_FILE"] = db_file
    APP_GLOBALS["save_db"].__globals__["DB_FILE"] = db_file
    return temp_dir


def test_home_page_returns_form():
    temp_dir = configure_db()
    try:
        client = app.test_client()
        response = client.get("/")

        assert response.status_code == 200
        body = response.get_data(as_text=True)
        assert "URL Shortener" in body
        assert '<form method="POST" action="/shorten">' in body
    finally:
        rmtree(temp_dir, ignore_errors=True)


def test_shorten_creates_code_and_redirects():
    temp_dir = configure_db()
    try:
        client = app.test_client()
        response = client.post("/shorten", json={"url": "https://example.com"})

        assert response.status_code == 200
        payload = response.get_json()
        assert payload["short_url"] == f'/{payload["code"]}'

        redirect_response = client.get(payload["short_url"], follow_redirects=False)
        assert redirect_response.status_code == 302
        assert redirect_response.headers["Location"] == "https://example.com"
    finally:
        rmtree(temp_dir, ignore_errors=True)


def test_expired_link_returns_410():
    temp_dir = configure_db()
    try:
        code = "abc123"
        APP_GLOBALS["save_db"](
            {code: {"url": "https://example.com", "expiry": 1}}
        )

        client = app.test_client()
        response = client.get(f"/{code}")

        assert response.status_code == 410
        assert "expired" in response.get_data(as_text=True).lower()
    finally:
        rmtree(temp_dir, ignore_errors=True)
