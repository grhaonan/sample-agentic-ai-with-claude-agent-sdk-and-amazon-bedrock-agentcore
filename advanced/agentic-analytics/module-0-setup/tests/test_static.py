"""FAST — static checks on the setup script + notebook. No AWS, no creds."""
from __future__ import annotations

import ast

import nbformat
import pytest

from conftest import MODULE_DIR, NOTEBOOK, SCRIPTS_DIR

SETUP_SCRIPT = SCRIPTS_DIR / "setup_infrastructure.py"


def test_setup_script_parses():
    """The infra script is valid Python."""
    ast.parse(SETUP_SCRIPT.read_text())


def test_setup_script_exposes_setup_and_verify():
    """Both the participant entrypoint (setup) and the reusable check (verify) exist."""
    tree = ast.parse(SETUP_SCRIPT.read_text())
    funcs = {n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
    assert {"setup", "verify"} <= funcs


def test_setup_is_idempotent_by_design():
    """Guards the idempotency intent: skip-if-present checks are in the source."""
    src = SETUP_SCRIPT.read_text()
    assert "head_bucket" in src          # bucket existence check
    assert "head_object" in src          # per-file upload skip
    assert "IF NOT EXISTS" in src        # database + tables


def test_no_manual_iam_role_creation():
    """Module 0 must NOT create the deploy-time IAM role (that's Module 2 / CDK)."""
    src = SETUP_SCRIPT.read_text()
    assert "create_role" not in src
    assert "StudentAnalyticsAgentCoreRole" not in src


def test_demo_data_present():
    """The two demo CSVs ship with the module."""
    data = MODULE_DIR / "data"
    assert (data / "student_enrollment_analytics.csv").exists()
    assert (data / "financial_summary_by_student.csv").exists()


@pytest.mark.skipif(not NOTEBOOK.exists(), reason="notebook not created yet")
def test_notebook_code_cells_parse():
    """Every code cell parses as Python (skipping !/% shell+magic lines)."""
    nb = nbformat.read(NOTEBOOK, as_version=4)
    for i, cell in enumerate(nb.cells):
        if cell.cell_type != "code":
            continue
        code = "\n".join(
            "" if line.lstrip().startswith(("!", "%")) else line
            for line in cell.source.splitlines()
        )
        try:
            ast.parse(code)
        except SyntaxError as e:
            pytest.fail(f"cell {i} failed to parse: {e}")
