# P71 walkthrough: Separate the Two Contributions

## Guiding question

Why can target motion bias the range estimated from one chirp?

Run `experiment.m` once without editing it. The script is finite and
foreground-only. It creates six figures tagged `P71` and retains `p71_results`.

## Baseline: see delay and Doppler inside one beat

Open **P71 transmitted and moving echo chirp**. The echo is delayed by
`0.300 us` and shifted upward by about `10.267 kHz` because the target is
approaching. The plot shows instantaneous chirp frequency relative to the
carrier; the valid overlap begins after the round-trip delay.

Open **P71 signed dechirped beat**. The time trace is one complex rotation, and
the lower panel places its signed spectral peak near `+139.733 kHz`. Read the
three vertical markers in order:

- delay alone contributes `+150.000 kHz`;
- approaching Doppler contributes `+10.267 kHz` to the echo; and
- `tx .* conj(rx)` measures their difference, about `+139.733 kHz`.

Expected observation: motion did not create a separately labeled peak. Both
causes occupy the same beat.

## Processing transition: apply the stationary conversion

Open **P71 naive range and corrected range**. The true target is at `45 m`.
The stationary conversion reports about `41.920 m`, while adding independently
known Doppler before range conversion recovers `45 m`.

Common mistake: saying the target moved `3.080 m` during the chirp. At
`20 m/s` it moved only `0.8 mm`; the larger number is a range-inference bias.

## Sweep 1: change only radial velocity

Open **P71 velocity sweep**. Range, carrier frequency, chirp duration,
bandwidth, slope, sample rate, and amplitude remain fixed while velocity takes
`-30, -15, 0, +15, +30 m/s`. Every case reuses the same private noise samples.

Expected observations:

- receding velocities produce positive range bias;
- zero velocity produces zero bias;
- approaching velocities produce negative range bias; and
- equal velocity steps produce equal bias steps.

Try changing only `velocity_sweep_mps` to `[-40 -20 0 20 40]`. Predict biases
of `+6.16, +3.08, 0, -3.08, -6.16 m`, then restore the reviewed vector.

## Sweep 2: change only chirp slope

Open **P71 chirp-slope sweep**. Velocity stays `+20 m/s` and duration stays
`40 us`; bandwidth takes `10, 15, 20, 25, 30 MHz` so slope increases.
Every case again reuses the same private noise samples.

Expected observations:

- the fixed Doppler contribution remains about `10.267 kHz`;
- the delay contribution and total beat grow with slope; and
- the magnitude of range bias shrinks from `6.160` to about `2.053 m`.

Try changing only the first bandwidth to `5 MHz`. Predict a `0.125 THz/s`
slope and `-12.32 m` bias. Restore `10 MHz` afterward.

Common mistake: saying higher bandwidth removes Doppler. It makes the same
Doppler error smaller after conversion to meters; the beat still contains it.

## Broken case: use the wrong correction sign

Open **P71 broken correction and recovery**. The broken path subtracts the
approaching Doppler from a beat that already contains `-f_d`. It reports about
`38.840 m`, doubling the stationary-assumption error to `-6.160 m`.

Explain the failure in physical terms: with this mixer, approaching Doppler
lowered the beat, so the correction must add that known Doppler contribution
back before applying the range scale.

## Recovery on the unchanged measurement

The recovery changes only the sign of the Doppler correction. Confirm:

- `p71_results.measured_beat_frequency_hz` is shared by all three paths;
- `p71_results.stationary_range_bias_m` is near `-3.080 m`;
- `p71_results.wrong_sign_range_bias_m` is near `-6.160 m`; and
- `p71_results.corrected_range_error_m` is near zero.

Velocity is labeled independently supplied. Do not claim the one chirp
estimated it.

## Signed-beat edge case

The velocity sweep keeps every reviewed beat positive, but the equation is
signed. If approaching Doppler equals the delay contribution, the beat reaches
DC. Beyond that point it becomes negative. A positive-half FFT or `abs`-based
frequency estimate would erase the sign and produce a false range.

## Cancellation, rerun recovery, and rollback

Press `Ctrl+C` between figure sections if needed. There is no worker, timer,
network request, file write, or external process continuing in the background.
An interruption can leave partial `P71` figures and workspace arrays, but no
external persistent state. Rerun from the top to close only figures tagged
`P71`, clear and rebuild `p71_results`, and regenerate the same private noise
stream. Unrelated figures and variables are not broadly cleared.

Repository rollback is file-local: remove the P71 learning artifacts and
focused evidence/catalog changes, then restore only P71's manifest status to
`scaffolded`. Preserve P70, later module identities, ignored `.learning/`
progress, and operator-managed active-batch contracts.

## Concept connection

Complete this sentence aloud:

> One up-chirp beat equals the delay contribution ___ the Doppler
> contribution; under this convention an approaching target appears too ___,
> and correction requires ___ velocity information.

The intended answer is minus, near, and independent. P72 adds an opposite
chirp slope to supply another measurement equation.
