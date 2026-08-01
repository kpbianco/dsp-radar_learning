# Walkthrough

## Guiding question

Why does a high-frequency tone appear as a lower-frequency tone after sampling?

Run `experiment.m` from this module directory. Work through one figure at a
time; the printed metrics are there to confirm what the plots show.

## Baseline

Keep `f_input = 700` Hz and `fs = 1000` samples/s. In the first figure, compare
the solid 700 Hz input, dashed 300 Hz alias, and sample stems.

Expected observation: the continuous curves take different paths between
measurements, yet both pass through every stem. The lower panel shows that the
stored sequence and the correctly phased alias prediction coincide. The
recurrence estimator prints 300 Hz because a real sequence exposes only the
fold inside zero through the 500 Hz Nyquist limit.

Connect the metrics to the equation: `round(700/1000) = 1`, so the signed fold
is `700 - 1*1000 = -300` Hz and the apparent magnitude is 300 Hz.

## Sweep 1: change only input frequency

Leave `fs = 1000` samples/s and run the committed
`input_frequency_sweep = 0:25:3000` Hz.

Expected observation: apparent frequency rises from DC to 500 Hz, falls back to
DC at 1000 Hz, and repeats through 3000 Hz. Estimator dots sit on the theoretical
triangles. The signed view alternates slope and stays inside `-500` to `+500`
Hz. This is deterministic folding around multiples and half-multiples of the
sample rate, not random damage.

Then inspect the representative sequences at 450, 500, 550, 950, 1000, and
1050 Hz. Compare one panel at a time:

- 450 and 550 Hz both appear at 450 Hz, on opposite sides of the Nyquist fold.
- 500 Hz sits exactly at the fold boundary.
- 950 and 1050 Hz both appear at 50 Hz around the fold at 1000 Hz.
- 1000 Hz repeatedly lands at one phase and appears as DC.

The only changed variable is the analog input frequency.

## Sweep 2: change only sample rate

The second sweep holds the input at 700 Hz and changes `sample_rate_sweep` from
2000 to 1200, 1000, and 800 samples/s.

Expected apparent frequencies are 700, 500, 300, and 100 Hz. At 2000 samples/s
the input is below Nyquist. Reducing only the measurement-clock rate moves the
same physical tone through different folds, so its stored sample pattern and
reported frequency change.

Radar connection: replacing `fs` with pulse repetition frequency gives the
same result for pulse-to-pulse Doppler. Changing PRF changes which velocity
aliases share a slow-time sequence.

## Broken case: keep the wrong phase

The deliberately broken section takes the correct apparent magnitude, 300 Hz,
but incorrectly keeps `+phi` after the signed fold became negative. The dotted
curve visibly misses the sample stems, and its printed maximum error exceeds
0.5 amplitude unit.

Common mistake: taking an absolute value is sufficient for reporting an
unsigned frequency, but it is not sufficient for reproducing the sampled real
cosine. A reflected fold reverses phase. The broken model has the right
frequency label and the wrong sequence.

Another common mistake is calling the reported 300 Hz the known analog input.
The 300 Hz sequence is also consistent with analog inputs at 700 Hz, 1300 Hz,
and infinitely many other alias-family frequencies when their phase is mapped
correctly. Samples alone do not identify the family member.

## Recovery

Restore `A = 1`, `f_input = 700`, `fs = 1000`, `phi = pi/5`, `duration = 0.2`,
`fs_display = 20000`, `display_duration = 0.025`,
`input_frequency_sweep = 0:25:3000`, representative frequencies
`[450 500 550 950 1000 1050]`, and sample rates `[2000 1200 1000 800]`.
Restore `phi_alias = -phi` whenever the signed fold is negative. Every
assertion should then pass.

If a guard stops the script, restore finite real scalar controls, an integer
sample count of at least five, and the committed ceilings: 20001 dense display
points, 5000 samples per record, 128 input-frequency cases, and eight
representative or sample-rate cases. Keep the display rate above twice the
highest continuously drawn baseline frequency.

Measurement-system recovery must happen before ambiguity is created: use an
analog anti-alias filter to restrict input bandwidth and select a sufficient
sample rate. Changing an estimator or drawing a smoother curve after sampling
cannot recover the discarded alias-family identity.

You are ready for the checks when you can predict a fold above Nyquist, explain
the phase reversal, and connect ADC aliasing to ambiguous Doppler under a PRF.
