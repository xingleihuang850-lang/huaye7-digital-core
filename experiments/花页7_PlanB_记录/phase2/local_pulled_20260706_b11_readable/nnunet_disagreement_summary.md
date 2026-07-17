# B1.1 rescue20 nnUNet/disagreement review

| variant | phi | S2 rmse | Euler | maxCC | Dice vs threshold φ6.4 | IoU | reverse fail |
|---|---:|---:|---:|---:|---:|---:|:---:|
| ep005_orig | 2.178 | 0.00872 | 58.93 | 0.0931 | 0.507 | 0.340 | True |
| ep005_qmatch | 5.787 | 0.00159 | 113.78 | 0.0621 | 0.949 | 0.903 | False |
| ep015_orig | 3.687 | 0.00603 | 88.03 | 0.0743 | 0.731 | 0.576 | True |
| ep015_qmatch | 5.795 | 0.00172 | 116.15 | 0.0651 | 0.950 | 0.905 | False |
