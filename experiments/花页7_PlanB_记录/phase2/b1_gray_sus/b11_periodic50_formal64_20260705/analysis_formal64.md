# B1.1 formal64 periodic validation analysis

| epoch | formal target | pass | status | score | phi | S2 | Euler | maxCC | fast target/pass |
|---:|---:|:---:|---|---:|---:|---:|---:|---:|---|
| 10 | 6.0 | False | rejected | 201.4433 | 6.000 | 0.00406 | 84.00 | 0.0950 | 5.0/False |
| 20 | 5.5 | False | rejected | 201.4914 | 5.500 | 0.00447 | 77.58 | 0.0879 | 5.0/False |
| 30 | 7.5 | False | rejected | 101.6752 | 7.500 | 0.01101 | 110.42 | 0.0746 | 7.5/True |
| 40 | 6.0 | False | rejected | 200.9475 | 6.000 | 0.00156 | 95.38 | 0.0859 | 5.5/False |
| 50 | 8.0 | False | rejected | 101.6364 | 8.000 | 0.00871 | 111.03 | 0.0815 | 8.0/True |

## Conclusion
No checkpoint passed formal gate. Best formal score is ep050 target 8.0% with score 101.6364, but pass=False status=rejected.
This confirms validation metric repair worked as a stricter gate: B1.1 current baseline fails formal S2/Euler/maxCC selection, so next step is topology-aware cheap modification, not B2 or 100/200ep scaling.