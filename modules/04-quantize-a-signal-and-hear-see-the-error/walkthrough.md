# Walkthrough

## Guiding question

How do ADC bit depth and full-scale range change the measurement?

Run `experiment.m` from this module directory. Inspect one figure and its
printed metrics at a time. The committed record is coherent, so its error
spectrum emphasizes quantization structure rather than record-edge leakage.

## Baseline

Keep `A = 0.9` V, `full_scale = 1.0` V, and `bits_baseline = 6`. The ADC input
range is `-1 V` through `+1 V`, there are 64 levels, and one LSB is
`2/64 = 0.03125 V`.

In the first figure, compare the smooth input sample sequence with the
stair-step ADC output. Then inspect `x_q-x` in the lower panel.

Expected observation: many neighboring input values become the same reported
voltage. No sample clips, and every error stays between approximately
`-0.015625 V` and `+0.015625 V`, which is half an LSB.

In the baseline spectrum, expect repeatable lines rather than an ideally flat
noise floor. A sine revisits related positions inside the voltage bins, so its
undithered error is signal-dependent.

The printed measured SNR describes this record. The printed
`6.02*B + 1.76 dB` value is only an ideal full-scale-sine reference; do not
force the measured value to equal it.

## Sweep 1: change only bit depth

The first sweep uses `[3 6 10 14]` bits while keeping the same sinusoid and
`+/-1 V` input range.

Inspect the four staircase panels from 3 through 14 bits. At 3 bits, one step
is `0.25 V`; the output visibly jumps between a few levels. Every added bit
halves the step. At 14 bits, the steps are too fine to distinguish at the same
plot scale, but the printed and logarithmic RMS-error plot retain the change.

Expected observation: voltage step and RMS error decrease monotonically, while
measured signal-to-error ratio rises. The only changed variable is the number
of code levels inside the same physical voltage span.

Common mistake: saying that more bits increase the maximum input voltage. They
do not in this sweep. `V_FS` remains 1 V; only the spacing between measurement
levels changes.

## Sweep 2: change only the ADC full-scale range

The second sweep fixes the 8-bit depth and reuses the same 0.9 V peak input,
then changes the ADC limits to `+/-1 V`, `+/-3.6 V`, and `+/-9 V`. The unchanged
input therefore uses 90%, 25%, and 10% of each range. Compare the same input
samples with each quantized output.

Expected observation: all three cases have zero clipped samples, while the
steps grow from `0.0078125 V/LSB` to `0.028125 V/LSB` and
`0.0703125 V/LSB`. The wider ADC settings make the unchanged signal occupy
fewer codes, so its measured signal-to-error ratio becomes much worse.

Moving the same signal from 90% to 10% range use predicts about
`20*log10(0.9/0.1) = 19.1 dB` of loss under the usual quantization model. The
measured loss should be in that neighborhood, not treated as an exact law for
this deterministic waveform.

Common mistake: calling poor utilization clipping. The input is identical in
all three cases, and the 10% case never reaches an endpoint. It wastes
resolution because the ADC range is unnecessarily wide, but it retains its
peaks.

## Optional dither comparison

The dither section adds seeded TPDF voltage from `-1` through `+1` baseline LSB
before the same 6-bit quantizer. Compare the two time-error traces and then the
two spectra.

Expected observation: dither breaks up the repeating error pattern and spreads
spectral energy more broadly. Its total RMS error may increase. That is the
trade: less signal-correlated structure for a higher broadband floor, not free
accuracy.

The script does not start an audio device. After inspecting all amplitudes, you
may optionally run `soundsc(audio_preview, fs)` to hear original, quantized,
and clipped segments, or `soundsc(audio_error_preview, fs)` to hear an 8x error
preview. Playback is not required for completion; stop it with Ctrl+C if your
MATLAB environment blocks. The retained validation does not claim audio-device
behavior.

## Broken case: overload the input range

The deliberately broken case holds the ADC at `+/-1 V` and 8 bits but raises
the input peak to `1.35 V`.

Expected observation: the output flattens near both limits. The clipped-sample
count is nonzero, peak error is much larger than half an LSB, and RMS error is
worse than every non-clipping utilization case. Information about how far the
input traveled beyond the endpoint has disappeared.

Common mistake: trying to repair clipping by adding bits while keeping the same
range. More interior levels cannot identify a peak that saturation already cut
off.

Radar connection: a strong close target, clutter return, leakage tone, or
interferer can overload a receiver even when the desired weak echo would
otherwise be well resolved. Full-scale headroom and analog gain must be chosen
before the ADC; digital attenuation afterward is too late.

## Recovery

Restore `A = 0.9`, `f0 = 128`, `phi = pi/7`, `fs = 4096`, `duration = 0.25`,
`bits_baseline = 6`, `full_scale = 1.0`, bit depths `[3 6 10 14]`, utilization
fractions `[0.90 0.25 0.10]`, `utilization_bits = 8`,
`overload_amplitude = 1.35`, and `overload_bits = 8`. Every assertion should
then pass.

If an input guard stops the script, use finite real scalar controls, an integer
bit depth from 2 through 16, an even coherent record from 16 through 16384
samples, and no more than eight sweep cases. Keep `fs > 2*f0`, keep baseline
`A < full_scale`, and make `f0*duration` an integer.

Recover a measurement system non-destructively by reducing front-end gain or
increasing the ADC range until expected peaks do not clip, then use as much of
the remaining range as practical. If a weak signal still occupies too few
codes, improve analog gain distribution or use a suitable higher-resolution
converter; digital gain after quantization cannot recreate discarded detail.

You are ready for the checks when you can distinguish quantization noise,
clipping, and poor full-scale utilization from the plots.
