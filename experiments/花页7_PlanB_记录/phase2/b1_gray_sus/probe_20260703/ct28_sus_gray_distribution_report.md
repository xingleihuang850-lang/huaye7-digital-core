# ct28 sus gray distribution probe
generated_at: 2026-07-03T15:49:10+0800
sus: /home/user/HXL/HY7_source/吉林大学数据报告归总/微米CT精细扫描-2p8um/处理图像/202510052_5mm_1500c_8bit_2p8um_sus.raw
pore: /home/user/HXL/HY7_source/吉林大学数据报告归总/微米CT精细扫描-2p8um/处理图像/202510052_5mm_1500c_8bit_2p8um_pore.raw
valid_mask_rule: (sus != 0) OR (pore == pore_val); pore overrides outside-air zeros
pore_val: 0

## voxel counts
- total: 3375000000
- valid: 2615526000
- outside_or_invalid: 759474000
- pore: 187843908
- nonpore_valid: 2427682092
- valid_frac_pct: 77.497067
- pore_frac_of_total_pct: 5.565745
- pore_frac_of_valid_pct: 7.181879

## valid gray percentiles uint8
- p0: 0
- p0.1: 15
- p0.5: 35
- p1: 45
- p2: 55
- p5: 70
- p10: 81
- p25: 98
- p50: 115
- p75: 132
- p90: 151
- p95: 165
- p98: 186
- p99: 205
- p99.5: 233
- p99.9: 254
- p100: 254
mean: 115.915536
std: 30.192172

## M7 tile probe
- n_tiles: 20750
- n_train: 16600
- n_test: 4150
gray_mean_per_tile: {'n': 20750, 'mean': 117.597556, 'std': 6.810011, 'min': 96.294617, 'p1': 102.676044, 'p5': 106.432144, 'p50': 117.907074, 'p95': 127.818552, 'p99': 130.312237, 'max': 141.877441}
gray_std_per_tile: {'n': 20750, 'mean': 30.047862, 'std': 3.961303, 'min': 20.068374, 'p1': 22.50219, 'p5': 24.430581, 'p50': 29.656526, 'p95': 36.240963, 'p99': 44.722413, 'max': 58.315889}
pore_phi_pct_per_tile: {'n': 20750, 'mean': 7.123638, 'std': 3.171862, 'min': 1.806641, 'p1': 2.954102, 'p5': 3.448486, 'p50': 6.317139, 'p95': 13.62915, 'p99': 17.074768, 'max': 31.811523}

## recommended first normalization
{"policy": "valid-mask percentile clip then linear map to [-1,1]", "candidate_p1_p99": [45, 205], "candidate_p0_5_p99_5": [35, 233], "note": "Use valid mask including true pore zeros; do not treat all zero gray as outside air because pore label overrides outside mask."}
