# P69 walkthrough: Watch Parallel Ramps Become a Tone

## Guiding question

Why does a delayed chirp produce a nearly constant beat frequency?

Run `experiment.m` once without editing it. The script is finite and
foreground-only. It creates six figures tagged `P69` and `p69_results`.

## Baseline: compare the ramps before the FFT

Open **P69 instantaneous frequency** first. The transmitted and received lines
have the same slope. Read their approximately `150 kHz` vertical separation
only where the received trace exists.

Expected observation: delay shifts an ideal linear ramp horizontally, which
also creates a constant vertical frequency gap. The blank pre-echo interval is
not a zero-frequency beat; there is no echo from this chirp there.

Now open **P69 dechirped mixer output**. Its real part is a nearly steady tone,
while unwrapped phase is nearly a straight line. Noise roughens the line but
does not change its average positive slope.

## Processing transition: one tone becomes one range

Open **P69 beat spectrum and range**. The positive-frequency FFT peak should
sit near the theoretical `S tau`. The known range, FFT estimate, and independent
phase-increment check should nearly agree.

Connect the panels in this order:

```text
parallel ramp gap -> mixer phase slope -> FFT peak f_b -> c f_b/(2S).
```

Do not credit zero padding with the physical result. The delay and chirp slope
create the beat; the FFT only measures it on a finite record.

## Sweep 1: vary only target range

Open **P69 target range sweep**. The cases are `15, 30, 45, 60, 75 m` and use
one unchanged slope and deterministic noise record.

Expected observations:

- round-trip delay grows linearly with range;
- the FFT beat peak grows linearly with delay; and
- converting with the fixed slope makes estimated range follow the identity
  line within the finite-record tolerance.

Try changing only the final range from `75` to `72 m`. Predict a slightly lower
beat and an estimate near `72 m`; no other physical parameter should move.

## Sweep 2: vary only chirp slope

Open **P69 chirp slope sweep**. Range and duration stay fixed. Bandwidth changes,
so `S = B/T` changes from `0.25` to `0.75 THz/s`.

Expected observation: beat frequency scales with slope, but the lower panel
stays near `45 m` because every case divides by its own slope.

Try changing only `slope_bandwidth_sweep_hz(1)` from `10 MHz` to `8 MHz`.
Predict a smaller first beat with essentially unchanged recovered range. Keep
bandwidth strictly increasing and below the sampled complex-baseband limit.

## Broken case

Open **P69 broken conversion and recovery**. The broken bar is approximately
twice the known range because `c f_b/S` omits the monostatic round-trip factor.
The same FFT peak produced the baseline, broken, and recovered bars. This is a
unit/model interpretation failure, not random noise, a bad FFT, or a lost echo.

## Recovery on the unchanged measurement

Recovery restores `R = c f_b/(2S)` without regenerating a chirp or re-estimating
the peak. The script asserts that the recovered value equals the baseline FFT
range to numerical precision. That isolation identifies the causal fix.

## Cancellation and rerun recovery

Press `Ctrl+C` between figure sections if needed. There is no worker, timer,
network request, file write, or external process continuing in the background.
An interruption can leave already-created `P69` figures and intermediate
variables in the current MATLAB workspace, but it leaves no background or
external persistent state. Rerun the script to close only figures tagged
`P69`, clear and rebuild `p69_results`, regenerate the private noise stream,
and recover the exact baseline. Unrelated figures and variables are not
broadly cleared.

## Before the teach-back

Be ready to explain why equal-slope delayed ramps have a constant frequency
gap, why mixer order determines beat sign, why monostatic delay contains a
factor two, why the two sweeps show different cause/effect relationships, and
why zero padding does not improve the physical range resolution.
