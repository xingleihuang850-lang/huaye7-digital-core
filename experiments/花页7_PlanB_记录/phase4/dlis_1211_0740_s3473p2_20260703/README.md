# HY7 DLIS inventory — 1211_0740_s3473.2.dlis

Source file is not committed.

```text
path: /Users/hxl/Documents/1211_0740_s3473.2.dlis
size_bytes: 161411598
sha256: 95b58c8e8f081cfce05e8e97163dcbfeb5d7d7493fef02ad36c97180039353ab
```

Depth coverage found in DLIS frames: approximately 3873.00–4313.10 m. Target HY7 depth 4199.21 m is inside all three frames.

Frames found:

- frame 50: rows=4401, spacing=-0.1 m, depth=3873.100–4313.100 m, channels=78
- frame 51: rows=17604, spacing=-0.025 m, depth=3873.025–4313.100 m, channels=8
- frame 52: rows=176040, spacing=-0.0025 m, depth=3873.003–4313.100 m, channels=32

Important channels observed:

- Frame 50: general logging/navigation channels, gamma `GRU`, accelerometer/magnetometer/navigation channels.
- Frame 51: slow channels including `RGR_T` natural gamma and transmitter current/voltage/power.
- Frame 52: high-resolution electrical imaging / XRMI-style arrays: `XPAD1`–`XPAD6` dimension 25 and `XPADS` dimension 200, plus fast accelerometer and pad profile channels.

Preview artifacts around 4199.21 ±2 m were exported as CSV/PNG/NPZ. The NPZ is a lightweight local evidence artifact, not the full DLIS.
