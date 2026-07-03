# B1 gray sus slice dataset evidence

Generated B1 gray-medium DDPM dataset from same-grid ct28 `sus`; no training was run in this step.

Remote dataset directory:

```text
hy7-linux:/home/user/HXL/HY7_planb/phase2/slices_ct28_gray_128/
```

Remote large arrays (not in git):

```text
train.npy       float32 [-1,1] shape=(16600,128,128)
test.npy        float32 [-1,1] shape=(4150,128,128)
test_pore.npy   uint8 {0,1}    shape=(4150,128,128)
```

Local evidence files:

```text
meta.json
verify_summary.json
sha256.txt
```

Key parameters:

```text
valid_mask_rule = (sus != 0) OR (pore == pore_val)
pore_val        = 0
clip_low/high   = 45 / 205
tile            = 128
z_step          = 6
axes            = z
min_valid       = 0.999
test_frac       = 0.2
seed            = 42
```

Verification summary:

```text
train_shape      = [16600, 128, 128], dtype=float32, min/max=[-1,1]
test_shape       = [4150, 128, 128], dtype=float32, min/max=[-1,1]
test_pore_shape  = [4150, 128, 128], dtype=uint8, unique=[0,1]
test_pore_phi    = 6.442654896931475 %
```

Remote sha256:

```text
7ee29988dd647945f44d2e2a559fc759a2eef0fa70bd072279f8bdd44e13ef46  train.npy
e858583c2015a100879d6c45c438073931884cd63ad8fc7eb35e6b5735b3d9c9  test.npy
6ad7f625e044d2fc20c6264d54afcd0387a7ac929fc975c3410f7a362d197f7a  test_pore.npy
801e3b2b62890ba7f594748c49fdc6764b924966baf22a6a274f4b57ca8b2f85  meta.json
535d4ac62dd67dfaf286a77d9ce3929334b981d9d864b211b47ec4f5d21c75cc  verify_summary.json
```
