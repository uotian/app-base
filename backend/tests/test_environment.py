import pytest
from pydantic import ValidationError

from config.environment import Environment


def test_environment_reads_existing_names_and_masks_secrets(monkeypatch):
    monkeypatch.setenv("DJANGO_SECRET_KEY", "test-secret")
    monkeypatch.setenv("DESKTOP_TOKEN", "test-token")
    monkeypatch.setenv("DJANGO_ALLOWED_HOSTS", "localhost,example.test")
    monkeypatch.setenv("DJANGO_DB_PATH", ":memory:")
    environment = Environment()
    assert environment.DJANGO_SECRET_KEY.get_secret_value() == "test-secret"
    assert environment.DESKTOP_TOKEN.get_secret_value() == "test-token"
    assert environment.DJANGO_ALLOWED_HOSTS.split(",") == ["localhost", "example.test"]
    assert environment.DJANGO_DB_PATH == ":memory:"
    assert "test-secret" not in repr(environment)
    assert "test-token" not in repr(environment)


def test_environment_defaults_without_dotenv_loading(monkeypatch, tmp_path):
    for name in Environment.model_fields:
        monkeypatch.delenv(name, raising=False)
    (tmp_path / ".env").write_text("DESKTOP_TOKEN=unrequested-token\n")
    monkeypatch.chdir(tmp_path)
    environment = Environment()
    assert environment.DESKTOP_TOKEN.get_secret_value() == ""
    assert environment.DJANGO_SECRET_KEY.get_secret_value() == ""
    assert environment.DJANGO_ALLOWED_HOSTS == "127.0.0.1,localhost"
    assert environment.DJANGO_DB_PATH.endswith("/db.sqlite3")


def test_empty_database_path_fails_at_startup(monkeypatch):
    monkeypatch.setenv("DJANGO_DB_PATH", "")
    with pytest.raises(ValidationError, match="DJANGO_DB_PATH"):
        Environment()
