import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("hy7_spatial_split_contract", ROOT / "src" / "hy7_spatial_split_contract.py")
assert SPEC is not None and SPEC.loader is not None
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


def manifest_with_crops(crops):
    manifest = mod.build_manifest(
        "ct28_sus",
        "微米CT精细扫描-2p8um/处理图像/sus.raw",
        "a" * 64,
        (100, 20, 20),
        (2.8, 2.8, 2.8),
        "z",
        0.1,
        0.2,
        5,
        42,
    )
    manifest["status"] = mod.COMPLETED_STATUS
    manifest["crops"] = crops
    manifest["run"] = {
        "command": "python src/hy7_planb_make_nnunet.py ...",
        "code_sha": "b" * 40,
        "environment": "nnunet_t28",
    }
    manifest["artifacts"] = {
        "case_mapping": "case_coordinates.json",
        "splits_final_json": "splits_final.json",
    }
    for crop in crops:
        crop.setdefault("artifact_id", crop["id"])
    return manifest


def test_axis_regions_reserve_two_buffers_and_are_half_open():
    regions = mod.make_axis_regions((100, 20, 20), "z", 0.1, 0.2, 5)
    assert regions == {"train": (0, 60), "val": (65, 75), "test": (80, 100)}


def test_validator_accepts_disjoint_crops_inside_declared_regions():
    result = mod.validate_split_manifest(
        manifest_with_crops([
            {"id": "tr_000", "split": "train", "bounds_zyx": [0, 20, 0, 10, 0, 10]},
            {"id": "va_000", "split": "val", "bounds_zyx": [65, 75, 0, 10, 0, 10]},
            {"id": "te_000", "split": "test", "bounds_zyx": [80, 100, 0, 10, 0, 10]},
        ])
    )
    assert result["passed"] is True
    assert result["crop_counts"] == {"train": 1, "val": 1, "test": 1}


def test_validator_accepts_an_empty_planned_manifest():
    manifest = mod.build_manifest(
        "ct28_sus", "sus.raw", "a" * 64, (100, 20, 20), (2.8, 2.8, 2.8), "z", 0.1, 0.2, 5, 42
    )
    result = mod.validate_split_manifest(manifest)
    assert result["passed"] is True
    assert result["checks"] == ["source_and_split_policy_valid", "planned_no_crops_recorded"]


def test_validator_fails_closed_for_cross_boundary_and_overlap():
    result = mod.validate_split_manifest(
        manifest_with_crops([
            {"id": "tr_cross", "split": "train", "bounds_zyx": [50, 70, 0, 10, 0, 10]},
            {"id": "te_overlap", "split": "test", "bounds_zyx": [55, 85, 0, 10, 0, 10]},
        ])
    )
    assert result["passed"] is False
    assert any("cross region" in error for error in result["errors"])
    assert any("cross-split voxel overlap" in error for error in result["errors"])


def test_validator_fails_when_source_identity_or_crop_coordinates_are_missing():
    manifest = manifest_with_crops([])
    manifest["source"].pop("sha256")
    result = mod.validate_split_manifest(manifest)
    assert result["passed"] is False
    assert "source missing: sha256" in result["errors"]


def test_completed_manifest_requires_rejection_and_artifact_audit_trail():
    manifest = manifest_with_crops([
        {"id": "tr_000", "split": "train", "bounds_zyx": [0, 20, 0, 10, 0, 10]},
        {"id": "va_000", "split": "val", "bounds_zyx": [65, 75, 0, 10, 0, 10]},
        {"id": "te_000", "split": "test", "bounds_zyx": [80, 100, 0, 10, 0, 10]},
    ])
    manifest["rejected_crops"] = [{"id": "re_000", "bounds_zyx": [55, 75, 0, 10, 0, 10], "reason": "crosses buffer"}]
    assert mod.validate_split_manifest(manifest)["passed"] is True

    manifest["crops"][0].pop("artifact_id")
    manifest["rejected_crops"][0]["reason"] = ""
    manifest["artifacts"].pop("splits_final_json")
    result = mod.validate_split_manifest(manifest)
    assert result["passed"] is False
    assert any("artifact_id" in error for error in result["errors"])
    assert any("reason is required" in error for error in result["errors"])
    assert any("splits_final_json" in error for error in result["errors"])
