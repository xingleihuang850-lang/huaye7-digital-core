import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "src" / "hy7_phase2_ddpm.py"


def test_train_help_exposes_periodic_validation_controls():
    res = subprocess.run(
        [sys.executable, str(SCRIPT), "train", "--help"],
        text=True,
        capture_output=True,
        check=True,
    )

    help_text = res.stdout
    for flag in (
        "--save-every",
        "--eval-every",
        "--eval-n",
        "--eval-gray-test",
        "--eval-real",
        "--eval-porosity-targets",
        "--select-metric",
        "--soft-euler-lambda",
        "--soft-maxcc-lambda",
        "--soft-maxcc-scales",
    ):
        assert flag in help_text
