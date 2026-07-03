#!/usr/bin/env bash
set -euo pipefail
cd /home/user/HXL/HY7_planb
source ~/miniconda3/bin/activate nnunet_t28
OUT=/home/user/HXL/HY7_planb/phase2/ddpm_ct28_gray
PID_FILE=$OUT/train_50ep_20260703.pid
LOG=$OUT/post_b1_cheap50_20260703.log
{
  echo "[post] started $(date -Iseconds)"
  pid=$(cat "$PID_FILE")
  echo "[post] waiting train pid=$pid"
  while kill -0 "$pid" 2>/dev/null; do
    tail -5 "$OUT/train_50ep_20260703.log" | sed "s/^/[train-tail] /"
    sleep 60
  done
  echo "[post] train pid exited $(date -Iseconds)"
  tail -20 "$OUT/train_50ep_20260703.log"
  test -f "$OUT/best.pt"
  test -f "$OUT/final.pt"
  test -f "$OUT/train_meta.json"

  echo "[post] sampling gray 512"
  python src/hy7_phase2_ddpm.py sample \
    --ckpt "$OUT/best.pt" \
    --out "$OUT" \
    --n 512 --size 128 --base 64 --bs 64 --seed 123 \
    --sample-mode gray --continuous

  echo "[post] threshold generated gray to target phi"
  python - <<"PY"
import json, os, numpy as np
out = "/home/user/HXL/HY7_planb/phase2/ddpm_ct28_gray"
gray = np.load(os.path.join(out, "samples_gray.npy"))
target_phi = 6.4
# Generated gray is normalized [-1,1]; lower gray is interpreted as pore.
thr = float(np.percentile(gray, target_phi))
pore = (gray <= thr).astype(np.uint8)
np.save(os.path.join(out, "samples_pore_threshold_phi64.npy"), pore)
phi = pore.reshape(len(pore), -1).mean(1) * 100
meta = {
  "method": "B1-threshold: generated gray <= percentile threshold",
  "target_phi_pct": target_phi,
  "threshold_norm": thr,
  "n": int(len(gray)),
  "gray_min": float(gray.min()),
  "gray_max": float(gray.max()),
  "gray_mean": float(gray.mean()),
  "phi_pct_mean": float(phi.mean()),
  "phi_pct_median": float(np.median(phi)),
  "notes": "First cheap B1 threshold proxy; nnUNet downstream requires separate generated-slice inference adapter."
}
json.dump(meta, open(os.path.join(out, "threshold_phi64_meta.json"), "w"), ensure_ascii=False, indent=2)
print(json.dumps(meta, ensure_ascii=False, indent=2))
PY

  echo "[post] evaluate threshold pore"
  python src/hy7_phase2_eval.py \
    --real /home/user/HXL/HY7_planb/phase2/slices_ct28_gray_128/test_pore.npy \
    --gen "$OUT/samples_pore_threshold_phi64.npy" \
    --out /home/user/HXL/HY7_planb/phase2/b1_gray_sus_eval_threshold_phi64 \
    --n 512 --rmax 48 --seed 0

  echo "[post] hash artifacts"
  (
    cd "$OUT"
    sha256sum best.pt final.pt train_meta.json samples_gray.npy samples_continuous.npy samples_grid.png samples_pore_threshold_phi64.npy threshold_phi64_meta.json code_sync_20260703.txt run_b1_train_50ep_20260703.sh train_50ep_20260703.log
  ) > "$OUT/b1_cheap50_hashes_20260703.txt"
  (
    cd /home/user/HXL/HY7_planb/phase2/b1_gray_sus_eval_threshold_phi64
    sha256sum metrics.json fig_eval.png
  ) >> "$OUT/b1_cheap50_hashes_20260703.txt"
  echo "[post] done $(date -Iseconds)"
} 2>&1 | tee -a "$LOG"
