from pathlib import Path

import yaml

ROOT = Path(__file__).parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "ci.yml"


def workflow():
    # PyYAML interprets an unquoted YAML 1.1 "on" key as Boolean true.
    return yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))


def all_run_commands(document):
    return "\n".join(
        str(step.get("run", ""))
        for job in document["jobs"].values()
        for step in job["steps"]
    )


def test_ci_is_least_privilege_and_uses_no_secrets_or_evidence():
    document = workflow()
    assert document["permissions"] == {"contents": "read"}
    text = WORKFLOW.read_text(encoding="utf-8").lower()
    assert "secrets." not in text
    assert "dev-evidence" not in text
    assert "legacy_app" not in text
    assert "deploy" not in text
    assert "git push" not in text


def test_ci_uses_locked_python_environment():
    document = workflow()
    steps = document["jobs"]["backend"]["steps"]
    setup = next(step for step in steps if step.get("uses", "").startswith("actions/setup-python"))
    assert setup["with"]["python-version"] == "3.12.13"
    commands = all_run_commands(document)
    assert "pip install --requirement backend/requirements.lock" in commands
    assert "pip install --no-deps --no-build-isolation ./backend" in commands
    assert "backend/scripts/verify_lock.py" in commands
    assert "python -m pip check" in commands


def test_ci_runs_required_regression_and_architecture_gates():
    commands = all_run_commands(workflow())
    for required in (
        "python -m compileall -q backend/app backend/scripts",
        "alembic heads",
        "alembic history",
        "alembic upgrade head --sql",
        'python -m pytest backend --basetemp "${{ runner.temp }}/pytest"',
        "python -m unittest discover -s tests",
    ):
        assert required in commands
