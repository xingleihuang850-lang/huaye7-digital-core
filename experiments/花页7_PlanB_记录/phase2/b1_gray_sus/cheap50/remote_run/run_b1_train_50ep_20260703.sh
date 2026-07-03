#!/usr/bin/env bash
set -euo pipefail
cd /home/user/HXL/HY7_planb
source ~/miniconda3/bin/activate nnunet_t28
python src/hy7_phase2_ddpm.py train \
  --data /home/user/HXL/HY7_planb/phase2/slices_ct28_gray_128 \
  --out /home/user/HXL/HY7_planb/phase2/ddpm_ct28_gray \
  --epochs 50 \
  --bs 64 \
  --base 64 \
  --lr 1e-4 \
  --amp \
  --seed 42 \
  --sample-every 10 \
  --sample-mode gray
