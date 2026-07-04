#!/usr/bin/env bash
set -euo pipefail
cd /home/user/HXL/HY7_planb
source ~/miniconda3/bin/activate nnunet_t28
BASE=phase2/ddpm_ct28_gray
DATA=phase2/slices_ct28_gray_128
OUT=phase2/b1_gray_sus_b11_output_calib_20260703
mkdir -p "$OUT/best_none" "$OUT/best_train_moments" "$OUT/final_none" "$OUT/final_train_moments" "$OUT/nnunet_in" "$OUT/nnunet_pred"
python src/hy7_phase2_ddpm.py sample --ckpt "$BASE/best.pt" --out "$OUT/best_none" --n 512 --bs 64 --base 64 --sample-mode gray --continuous --seed 123
python src/hy7_phase2_ddpm.py sample --ckpt "$BASE/best.pt" --out "$OUT/best_train_moments" --n 512 --bs 64 --base 64 --sample-mode gray --continuous --seed 123 --intensity-calibration train-moments --calibration-data "$DATA"
python src/hy7_phase2_ddpm.py sample --ckpt "$BASE/final.pt" --out "$OUT/final_none" --n 512 --bs 64 --base 64 --sample-mode gray --continuous --seed 123
python src/hy7_phase2_ddpm.py sample --ckpt "$BASE/final.pt" --out "$OUT/final_train_moments" --n 512 --bs 64 --base 64 --sample-mode gray --continuous --seed 123 --intensity-calibration train-moments --calibration-data "$DATA"
python - <<"PY"
import json, os, numpy as np, SimpleITK as sitk
ROOT="/home/user/HXL/HY7_planb"
OUT=f"{ROOT}/phase2/b1_gray_sus_b11_output_calib_20260703"
DATA=f"{ROOT}/phase2/slices_ct28_gray_128"
train=np.load(f"{DATA}/train.npy", mmap_mode="r")
test=np.load(f"{DATA}/test.npy", mmap_mode="r")[:512]
variants={}
for name in ["best_none","best_train_moments","final_none","final_train_moments"]:
    arr=np.load(f"{OUT}/{name}/samples_gray.npy")
    variants[name]=arr
    raw=((np.clip(arr,-1,1)+1)*0.5*(205-45)+45).astype(np.float32)
    img=sitk.GetImageFromArray(raw); img.SetSpacing((1,1,1))
    sitk.WriteImage(img, f"{OUT}/nnunet_in/{name.upper()}_0000.nii.gz")

def summ(a):
    f=a.ravel(); return {"mean":float(f.mean()),"std":float(f.std()),"min":float(f.min()),"max":float(f.max()),"p6p4":float(np.percentile(f,6.4)),"frac_minus1":float((f<=-0.999999).mean()),"frac_plus1":float((f>=0.999999).mean())}
report={"train":summ(np.asarray(train)),"test512":summ(test),"variants":{k:summ(v) for k,v in variants.items()}}
for k,v in variants.items():
    report["variants"][k]["mean_shift_vs_train"]=report["variants"][k]["mean"]-report["train"]["mean"]
    report["variants"][k]["mean_shift_vs_test512"]=report["variants"][k]["mean"]-report["test512"]["mean"]
json.dump(report, open(f"{OUT}/sample_stats.json","w"), indent=2)
print(json.dumps(report, indent=2))
PY
export nnUNet_raw=/home/user/HXL/HY7_planb/nnunet/nnUNet_raw
export nnUNet_preprocessed=/home/user/HXL/HY7_planb/nnunet/nnUNet_preprocessed
export nnUNet_results=/home/user/HXL/HY7_planb/nnunet/nnUNet_results
nnUNetv2_predict -i "$OUT/nnunet_in" -o "$OUT/nnunet_pred" -d 722 -c 2d -f 0 -tr nnUNetTrainer_50epochs -p nnUNetPlans -chk checkpoint_best.pth --disable_tta -device cuda > "$OUT/nnunet_predict_20260703.log" 2>&1
python - <<"PY"
import json, os, subprocess, sys, numpy as np, SimpleITK as sitk
ROOT="/home/user/HXL/HY7_planb"
OUT=f"{ROOT}/phase2/b1_gray_sus_b11_output_calib_20260703"
REAL=f"{ROOT}/phase2/slices_ct28_gray_128/test_pore.npy"
summary={}
for name in ["best_none","best_train_moments","final_none","final_train_moments"]:
    seg=sitk.GetArrayFromImage(sitk.ReadImage(f"{OUT}/nnunet_pred/{name.upper()}.nii.gz"))
    pore=(seg==1).astype(np.uint8)
    npy=f"{OUT}/{name}_pore_nnunet2d.npy"; np.save(npy,pore)
    eval_dir=f"{OUT}/eval_nnunet2d_{name}"
    subprocess.run([sys.executable, f"{ROOT}/src/hy7_phase2_eval.py", "--real", REAL, "--gen", npy, "--out", eval_dir, "--n", "512", "--rmax", "48", "--seed", "0"], check=True)
    m=json.load(open(f"{eval_dir}/metrics.json"))
    summary[name]={"phi":m["porosity_pct"]["gen_mean"],"s2":m["S2_radial"]["rmse_gen"],"euler":m["euler_chi"]["gen_mean"],"maxcc":m["connectivity"]["max_cc_frac_gen"]}
json.dump(summary, open(f"{OUT}/nnunet_eval_summary.json","w"), indent=2)
print(json.dumps(summary, indent=2))
PY
(cd "$OUT" && sha256sum code_sync_20260703.txt run_b11_output_calib_20260703.sh run_b11_output_calib_20260703.log sample_stats.json nnunet_predict_20260703.log nnunet_eval_summary.json */sample_intensity_calibration.json eval_nnunet2d_*/metrics.json eval_nnunet2d_*/fig_eval.png) > "$OUT/b11_output_calib_hashes_20260703.txt"
