import importlib.util
from pathlib import Path

import openpyxl
import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("hy7_etl", ROOT / "src" / "hy7_etl.py")
assert SPEC is not None and SPEC.loader is not None
etl = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(etl)


def save_workbook(path, title, rows):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = title
    for row in rows:
        ws.append(row)
    wb.save(path)


def test_parse_minerals_requires_expected_sheet_and_numeric_rows(tmp_path):
    missing = tmp_path / "missing.xlsx"
    save_workbook(missing, "Sheet", [[None, "石英", 10.0]])
    with pytest.raises(ValueError, match="missing required sheet"):
        etl.parse_minerals(missing)

    empty = tmp_path / "empty.xlsx"
    save_workbook(empty, "矿物", [[None, "石英", "not numeric"]])
    with pytest.raises(ValueError, match="no numeric mineral"):
        etl.parse_minerals(empty)

    valid = tmp_path / "valid.xlsx"
    save_workbook(valid, "矿物", [[None, "石英", 12.345], [None, "方解石", 87.655]])
    assert etl.parse_minerals(valid) == [{"mineral": "石英", "pct": 12.35}, {"mineral": "方解石", "pct": 87.66}]


def test_facekong_total_handles_dual_and_single_columns(tmp_path, monkeypatch):
    monkeypatch.setattr(etl, "B", str(tmp_path))
    filename = "孔隙喉道、裂缝统计数据.xlsx"

    dual_dir = tmp_path / "dual"
    dual_dir.mkdir()
    save_workbook(dual_dir / filename, "面孔率", [["裂缝面孔率", "孔隙面孔率"], [1.0, 2.0], [3.0, 4.0]])
    assert etl.facekong_components("dual") == {
        "sheet": "面孔率",
        "n_slices": 2,
        "fracture_pct": 2.0,
        "pore_pct": 3.0,
        "total_pct": 5.0,
    }
    assert etl.facekong_total("dual") == 5.0

    single_dir = tmp_path / "single"
    single_dir.mkdir()
    save_workbook(single_dir / filename, "面孔率", [["面孔率"], [1.0], [3.0]])
    assert etl.facekong_components("single") == {"sheet": "面孔率", "n_slices": 2, "total_pct": 2.0}
    assert etl.facekong_total("single") == 2.0


def test_facekong_total_fails_with_clear_schema_errors(tmp_path, monkeypatch):
    monkeypatch.setattr(etl, "B", str(tmp_path))
    filename = "孔隙喉道、裂缝统计数据.xlsx"

    no_sheet = tmp_path / "no_sheet"
    no_sheet.mkdir()
    save_workbook(no_sheet / filename, "统计", [["面孔率"], [1.0]])
    with pytest.raises(ValueError, match="missing face-porosity sheet"):
        etl.facekong_total("no_sheet")

    bad_column = tmp_path / "bad_column"
    bad_column.mkdir()
    save_workbook(bad_column / filename, "面孔率", [["其他指标"], [1.0]])
    with pytest.raises(ValueError, match="no supported porosity column"):
        etl.facekong_total("bad_column")


def test_report_direct_constants_preserve_provider_table_provenance():
    assert etl.MAPS_REPORT["total_porosity_pct"] == 0.4112
    assert etl.MAPS_REPORT["classification"][2]["radius_nm"] == 63.23
    assert "Maps精扫实验报告.docx" in etl.MAPS_REPORT["remote_path"]
    assert etl.FIB_REPORT["organic_pct"] == 1.52
    assert etl.FIB_REPORT["pores"] == 76252
    assert etl.FIB_REPORT["throats"] == 62086
    assert "FIB报告.docx" in etl.FIB_REPORT["remote_path"]
    assert etl.MAPS_REPORT["page"] is None
    assert "表号" in etl.FIB_REPORT["locator_note"]


def test_fib_count_recovery_and_interpretive_mineral_grouping_contracts():
    assert etl.infer_total_count([25.0, 50.0, 25.0], max_total=10) == 4
    with pytest.raises(ValueError, match="sum to 100"):
        etl.infer_total_count([20.0, 20.0])
    with pytest.raises(ValueError, match="no exact count denominator"):
        etl.infer_total_count([33.33, 66.67], max_total=10, tolerance=1e-8)

    groups = etl.mineral_groups([
        {"mineral": "石英", "pct": 50.0},
        {"mineral": "方解石", "pct": 30.0},
        {"mineral": "黄铁矿", "pct": 5.0},
        {"mineral": "其它矿物", "pct": 15.0},
    ])
    assert groups == {"长英质": 50.0, "碳酸盐": 30.0, "黏土": 0, "黄铁矿": 5.0, "其它": 15.0}
    assert etl.COARSE_MINERAL_GROUPING_V1["evidence_grade"] == "INTERPRETIVE"
    assert etl.LITHOLOGY_INTERPRETATION["not_a_vendor_classification"] is True
