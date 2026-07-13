import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("hy7_report_provenance", ROOT / "src" / "hy7_report_provenance.py")
assert SPEC is not None and SPEC.loader is not None
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


def _valid_declaration():
    digest = "b" * 64
    return {
        "status": "REPORT_PROVENANCE_DRAFT_NOT_ACTIVE",
        "render_authorized": False,
        "report_type": "ppt",
        "generator_path": "src/hy7_make_ppt.py",
        "generator_sha256": digest,
        "stats_input": {"path": "experiments/hy7_stats.json", "sha256": digest},
        "as_of": "2026-07-12",
        "evidence": [{"path": "experiments/INDEX.md", "sha256": digest, "grade": "diagnostic"}],
        "allowed_conclusion_ids": ["HY7-stage1-internal-baseline"],
        "outputs": ["deliverables/花页7/report.pptx"],
    }


def test_complete_declaration_is_only_ready_for_contract_review():
    result = mod.validate_report_declaration(_valid_declaration())
    assert result["passed"] is True
    assert result["verdict"] == "READY_FOR_CONTRACT_REVIEW_ONLY"
    assert result["render_authorized"] is False


def test_missing_evidence_grade_or_unsafe_output_fails_closed():
    declaration = _valid_declaration()
    declaration["evidence"][0].pop("grade")
    declaration["outputs"] = ["../outside.pptx"]
    result = mod.validate_report_declaration(declaration)
    assert result["passed"] is False
    assert any("evidence item" in error for error in result["errors"])
    assert any("outputs" in error for error in result["errors"])
