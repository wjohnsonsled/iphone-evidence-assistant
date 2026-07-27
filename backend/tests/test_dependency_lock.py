from pathlib import Path

from scripts.verify_lock import validate

BACKEND = Path(__file__).parents[1]


def test_dependency_lock_is_exact_and_covers_declared_dependencies():
    assert validate(BACKEND / "pyproject.toml", BACKEND / "requirements.lock") == []


def test_lock_validator_rejects_ranges_duplicates_and_missing_direct_dependencies(tmp_path):
    project = tmp_path / "pyproject.toml"
    project.write_text(
        '[project]\ndependencies=["alpha>=1"]\n'
        '[project.optional-dependencies]\ndev=["beta>=1"]\n',
        encoding="utf-8",
    )
    lock = tmp_path / "requirements.lock"
    lock.write_text("alpha>=1\nalpha==1\nalpha==1\n", encoding="utf-8")
    errors = validate(project, lock)
    assert any("not an exact" in error for error in errors)
    assert any("duplicate" in error for error in errors)
    assert any("beta" in error for error in errors)


def test_docker_uses_locked_noneditable_install():
    dockerfile = (BACKEND / "Dockerfile").read_text(encoding="utf-8")
    assert "requirements.lock" in dockerfile
    assert "pip install --no-cache-dir --requirement requirements.lock" in dockerfile
    assert "pip install --no-cache-dir --no-deps --no-build-isolation ." in dockerfile
    assert '-e ".[dev]"' not in dockerfile
