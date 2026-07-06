# B1.1 formal n=512 evaluation (ep050 vs ep040)

OUT: `/home/user/HXL/HY7_planb/phase2/b1_gray_sus_b11_formal_eval_20260705`

## threshold headline
| variant | phi target | phi | S2 rmse | Euler | maxCC | best S2 target | best S2 |
|---|---:|---:|---:|---:|---:|---:|---:|
| ep040_orig | 6.4 | 6.400 | 0.00335 | 106.36 | 0.0725 | 5.5 | 0.00185 |
| ep040_qmatch | 6.4 | 6.742 | 0.00429 | 109.04 | 0.0734 | 5.5 | 0.00187 |
| ep050_orig | 6.4 | 6.400 | 0.00636 | 104.73 | 0.0699 | 5.0 | 0.00337 |
| ep050_qmatch | 6.4 | 6.742 | 0.00741 | 107.44 | 0.0703 | 5.0 | 0.00355 |

## nnUNet downstream
| variant | phi | S2 rmse | Euler | maxCC |
|---|---:|---:|---:|---:|
| ep040_orig | 11.493 | 0.01652 | 145.57 | 0.0647 |
| ep040_qmatch | 5.404 | 0.00165 | 101.95 | 0.0725 |
| ep050_orig | 4.704 | 0.00293 | 95.07 | 0.0630 |
| ep050_qmatch | 5.111 | 0.00223 | 102.25 | 0.0609 |

## gray distribution
| variant | mean | std | KS vs real | Wasserstein | low freq | mid freq | high freq |
|---|---:|---:|---:|---:|---:|---:|---:|
| ep040_orig | -0.1616 | 0.4275 | 0.1137 | 0.0833 | 0.4940 | 0.3920 | 0.1133 |
| ep040_qmatch | -0.0989 | 0.3539 | 0.0020 | 0.0004 | 0.5004 | 0.3885 | 0.1104 |
| ep050_orig | 0.0832 | 0.4404 | 0.2190 | 0.1824 | 0.3808 | 0.4712 | 0.1471 |
| ep050_qmatch | -0.1022 | 0.3446 | 0.0191 | 0.0036 | 0.3891 | 0.4674 | 0.1426 |