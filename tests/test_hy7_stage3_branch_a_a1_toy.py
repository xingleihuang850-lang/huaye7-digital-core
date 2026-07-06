import importlib.util
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "hy7_stage3_branch_a_a1_toy", ROOT / "src" / "hy7_stage3_branch_a_a1_toy.py"
)
assert SPEC is not None
mod = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(mod)


def test_known_answer_phantoms_exercise_3d_metrics():
    phantoms = mod.known_answer_phantoms(size=8)

    solid = mod.compute_3d_metrics(phantoms["all_solid"])
    assert solid["porosity_phi_3d"]["value"] == 0.0
    assert solid["percolation_flags_3d"]["value"] == {"x": False, "y": False, "z": False}
    assert solid["largest_connected_component_fraction_3d"]["value"]["pore_voxel_basis"] == 0.0

    pore = mod.compute_3d_metrics(phantoms["all_pore"])
    assert pore["porosity_phi_3d"]["value"] == 1.0
    assert pore["percolation_flags_3d"]["value"] == {"x": True, "y": True, "z": True}
    assert pore["connected_porosity_ratio_3d"]["value"]["pore_voxel_basis"] == 1.0
    assert pore["s2_two_point_correlation_3d"]["value"]["lag_1_valid_pairs"] == {
        "x": 1.0,
        "y": 1.0,
        "z": 1.0,
    }

    channel = mod.compute_3d_metrics(phantoms["x_channel"])
    assert channel["porosity_phi_3d"]["value"] == 1 / 64
    assert channel["percolation_flags_3d"]["value"] == {"x": True, "y": False, "z": False}
    assert channel["largest_connected_component_fraction_3d"]["value"]["pore_voxel_basis"] == 1.0

    isolated = mod.compute_3d_metrics(phantoms["isolated_voxel"])
    assert isolated["porosity_phi_3d"]["value"] == 1 / 512
    assert isolated["percolation_flags_3d"]["value"] == {"x": False, "y": False, "z": False}
    assert isolated["largest_connected_component_fraction_3d"]["value"]["pore_voxel_basis"] == 1.0
    assert isolated["euler_characteristic_or_minkowski_3d"]["status"] == "NOT_IMPLEMENTED_FAIL_CLOSED"


def test_validate_known_answer_phantoms_is_fail_closed_for_wrong_percolation():
    phantoms = mod.known_answer_phantoms(size=8)
    report = mod.validate_known_answer_phantoms(phantoms)
    assert report["passed"] is True
    assert report["errors"] == []

    bad = dict(phantoms)
    bad["x_channel"] = np.eye(8, dtype=np.uint8).reshape(8, 8, 1).repeat(8, axis=2)
    bad_report = mod.validate_known_answer_phantoms(bad)
    assert bad_report["passed"] is False
    assert any("x_channel percolation" in err for err in bad_report["errors"])


def test_write_a1_package_creates_required_artifacts_without_committing_volume(tmp_path):
    out = tmp_path / "a1"
    outputs = mod.write_a1_package(out_dir=out, size=8, seed=20260706)

    expected = {
        "branch_a_a1_manifest",
        "branch_a_a1_readme",
        "metrics_3d_toy",
        "connectivity_semantics",
        "forbidden_claims",
        "hashes",
    }
    assert set(outputs) == expected
    for path in outputs.values():
        assert Path(path).exists()

    assert not (out / "toy_volume.npy").exists()
    assert not (out / "toy_volume_path.txt").exists()

    manifest = json.loads((out / "branch_a_a1_manifest.json").read_text())
    assert manifest["workflow_node"] == "HY7-stage3-branch-A-A1-toy-metric-plumbing"
    assert manifest["verdict"] == "ALLOW_A1_WITH_CONSTRAINTS"
    assert manifest["input_type"] == "synthetic_toy"
    assert manifest["scientific_status"] == "not_evidence"
    assert manifest["route_label"] == "synthetic_toy_plumbing"
    assert manifest["volume_committed_to_git"] is False
    assert manifest["execution_boundary"]["no_training"] is True
    assert manifest["execution_boundary"]["no_new_sampling_from_model"] is True
    assert manifest["execution_boundary"]["no_checkpoint"] is True

    metrics = json.loads((out / "metrics_3d_toy.json").read_text())
    assert metrics["scientific_status"] == "not_evidence"
    assert metrics["known_answer_phantom_suite"]["passed"] is True
    assert metrics["toy_metrics"]["all_pore"]["percolation_flags_3d"]["value"] == {
        "x": True,
        "y": True,
        "z": True,
    }
    assert metrics["toy_metrics"]["x_channel"]["percolation_flags_3d"]["value"] == {
        "x": True,
        "y": False,
        "z": False,
    }

    readme = (out / "branch_a_a1_readme.md").read_text()
    assert "not HY7 scientific evidence" in readme
    assert "Known-answer phantom suite" in readme
    assert "No toy volume is committed" in readme

    connectivity = (out / "connectivity_semantics.md").read_text()
    assert "pore-phase connectivity: 6-neighborhood" in connectivity
    assert "complementary solid connectivity: 26-neighborhood" in connectivity
    assert "single pore-phase connected component touches both opposing faces" in connectivity

    forbidden = (out / "forbidden_claims.txt").read_text()
    assert "B2-min final pass claim" in forbidden
    assert "Stage 3 planning promotion authorizes actual 3D generation" in forbidden

    hashes = (out / "hashes.txt").read_text()
    assert "branch_a_a1_manifest.json" in hashes
    assert "metrics_3d_toy.json" in hashes
    assert "toy_volume" not in hashes
