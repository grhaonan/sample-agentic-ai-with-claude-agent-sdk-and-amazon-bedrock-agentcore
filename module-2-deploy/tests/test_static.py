"""FAST — notebook hygiene for module-2-deploy.ipynb."""
from __future__ import annotations

import ast

import nbformat
import pytest

from conftest import NOTEBOOK


@pytest.fixture(scope="module")
def nb():
    return nbformat.read(NOTEBOOK, as_version=4)


def test_notebook_valid(nb):
    nbformat.validate(nb)


def test_code_cells_parse(nb):
    for i, c in enumerate(nb.cells):
        if c.cell_type != "code":
            continue
        wrapped = "async def _():\n" + "\n".join("    " + ln for ln in c.source.splitlines())
        try:
            ast.parse(wrapped)
        except SyntaxError:
            ast.parse(c.source)


def test_teaches_deploy_flow(nb):
    md = "\n".join(c.source for c in nb.cells if c.cell_type == "markdown")
    for needle in ["agentcore deploy", "agentcore invoke", "agentcore dev",
                   "remove agent", "Container", "stateless", "Module 3"]:
        assert needle in md, f"notebook should mention {needle!r}"


def test_reuse_is_explained(nb):
    md = "\n".join(c.source for c in nb.cells if c.cell_type == "markdown")
    assert "build_agent_options" in md
    assert "one source of truth" in md.lower() or "source of truth" in md.lower()


def test_observability_groundwork_mentioned(nb):
    md = "\n".join(c.source for c in nb.cells if c.cell_type == "markdown")
    assert "Module 4" in md and ("CloudWatch" in md or "trace" in md.lower())
