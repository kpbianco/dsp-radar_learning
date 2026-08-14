# P82 lesson: Listen Twice, Then Match Delay and Doppler

## Guiding question

How can a known broadcast-like reference reveal delayed Doppler-shifted echoes without transmitting?

## Physical mental model

A passive radar does not know what a separate transmitter intended to send.
It therefore listens in two directions:

1. the **reference channel** tries to hear the illuminator cleanly; and
2. the **surveillance channel** hears direct leakage, static reflections,
   possible moving-target echoes, and receiver noise.

The reference is a moving stencil. Slide it in delay, rotate its phase at a
trial Doppler, and ask how coherently it matches the surveillance record. A
weak target adds the same waveform at a later arrival time with a steady phase
rotation. That copy can accumulate coherently even though this receiver never
transmitted.

## The synthetic channels

The experiment uses a unit-RMS complex waveform (r[n]). Seeded QPSK-like
symbols and an explicit finite pulse create wide bandwidth; this is
"broadcast-like," not a model of a named broadcast standard. The measured
reference is

\[
q[n] = \operatorname{normalize}\{r[n] + \eta_q[n]\}.
\]

The surveillance channel is

\[
y[n] = a_0r[n]
     + a_mr[n-d_m]
     + a_tr[n-d_t]e^{j2\pi f_t n/f_s}
     + \eta_y[n].
\]

The terms are a strong direct path, delayed stationary multipath, a weaker
delayed moving-target copy, and surveillance noise. Positive delay is
implemented with zeros before the copy, not circular wrapping. The baseline
uses \(d_t=24\) samples and \(f_t=+500\ \text{Hz}\).

## The visible operation: cross-ambiguity

For trial delay (d) and Doppler (f), the script evaluates

\[
\chi(d,f) =
\frac{\left|\sum_{n=0}^{N-1}
y[n]q^*[n-d]e^{-j2\pi fn/f_s}\right|}
{\sqrt{\sum_n|y[n]|^2\sum_n|q[n-d]|^2}},
\]

where samples outside the record are zero. The conjugated delayed reference
undoes the waveform phase when the delay is right. The negative trial-Doppler
phasor undoes the target's positive phase rotation when (f=f_t). Thus the
model's positive injected delay and positive injected Doppler appear on
positive map axes.

The normalization makes the value a dimensionless coherence. It prevents a
shorter overlap at a large delay from winning merely because of scale, but it
does not turn the result into detection probability.

The implementation forms every delayed product and every trial phasor
explicitly. It does not use `ambgfun`, `xcorr`, `phased.*`, or a hidden passive
radar object.

## Why the first map fails

The direct path has voltage `2.50`; the target has voltage `0.18`. At delay
zero and Doppler zero, thousands of direct-path samples add with the same
phase. The target is present in the uncancelled map, but the map maximum answers
"direct path," not "target."

This failure is physical, not a plotting inconvenience. The displayed maps use
the coherent sum divided by delayed-reference energy, so each cell is a
matched complex-voltage magnitude. Both baseline panels share the uncancelled
matched-voltage peak scale. Renormalizing each panel independently would make a
weak residual look artificially as bright as the original leakage. Separate
dimensionless coherence values drive the localization and contrast metrics.

## Transparent direct-path cancellation

The one-tap teaching canceller finds the complex scale that best predicts the
surveillance channel from the measured reference:

\[
\hat a_0 = \frac{q^Hy}{q^Hq}, \qquad
y_c = y-\hat a_0q.
\]

This is an orthogonal projection, the simplest cousin of the adaptive
cancellation in P26. After projection, (q^Hy_c=0) to arithmetic precision,
so the origin collapses. The delayed `+500 Hz` copy then becomes the global
peak at its true coordinate.

This is deliberately not a practical extensive-cancellation algorithm. It
removes the surveillance projection onto the unshifted measured reference. The
delayed static path remains a distinct peak in this experiment, although any
finite-record correlation with the unshifted reference can bias the fitted
coefficient and partially attenuate a delayed path. The one-tap model cannot
represent delayed multipath, solve clock or carrier offsets, or track
time-varying channels. A dictionary of delayed reference taps could address
multipath, but an over-rich dictionary can also cancel a zero-Doppler target
whose delay is included.

## What the four controlled changes mean

### Target delay

Changing `[12 24 48]` samples changes only the echo arrival. The peak moves
across columns and stays at `+500 Hz`. A sample corresponds to excess bistatic
path

\[
\Delta L = c\,d/f_s.
\]

At `200 ksample/s`, one sample is `1.5 km` of excess path. This is not generic
target range and is not the monostatic expression (c\tau/2). Converting to a
target position needs transmitter, receiver, and target geometry.

### Target Doppler

Changing `[-500 0 +500] Hz` moves the peak across rows while delay remains 24
samples. Doppler sign is meaningful because the samples are complex. Passive
bistatic Doppler is not converted to speed with the monostatic
(f_D=2v/\lambda) formula; the geometry and carrier would be required.

At zero Doppler the target shares the clutter row. It remains separable here
because its delay differs from the direct and multipath delays. In real clutter
that is a difficult limiting case.

### Coherent integration time

The prefixes `[1024 2048 4096]` samples correspond to `[5.12 10.24 20.48] ms`.
The target phase is modeled correctly, so its sum grows coherently while
uncorrelated background does not. Target-to-map-median contrast rises. The
nominal Doppler scale (1/T) shrinks from about `195` to `49 Hz`.

Longer time does not guarantee indefinite gain. Acceleration, oscillator
error, waveform change, or channel variation eventually breaks coherence.
Zero-padding could interpolate a map but would not replace longer observed
time.

### Reference quality

The surveillance scene remains fixed while measured-reference quality falls
from `[35 15 5] dB`. The wrong reference both matches the target less well and
predicts the direct path less faithfully. Normalized target coherence and
contrast fall; at the poorest endpoint another residual cell becomes the map
maximum.

This sweep separates illuminator observability from target strength. Raising
target voltage would answer a different question.

## Intentionally broken cancellation and recovery

The broken path subtracts only `20%` of the estimated direct coefficient. The
origin stays the map maximum. The failure does not mutate either measured
channel. Recovery starts again from those retained channels, applies the full
projection, and reproduces the baseline residual and cross-ambiguity map
element for element.

The experiment has no transaction, device, or background task to roll back.
If a foreground run or graphics render is interrupted with Ctrl+C, close only
figures tagged `P82` or simply rerun the script; startup closes stale P82
figures and rebuilds the deterministic channels.

## Limiting cases

- With target voltage zero, no deterministic target cell should remain.
- With a perfect reference and exact direct-only surveillance, projection
  leaves roundoff.
- With an uncorrelated reference, both cancellation and cross-ambiguity fail.
- A target at zero delay and zero Doppler is indistinguishable from a change in
  direct-path coefficient in this model.
- A zero-Doppler target can be removed by a cancellation dictionary containing
  its delay.
- Near-record-length delay leaves little overlap and little coherent energy.
- Doppler outside ((-f_s/2,f_s/2)) aliases.
- A narrowband or repetitive illuminator has broad or ambiguous delay
  correlation even with a dense delay grid.
- A shorter CPI broadens Doppler response; a denser plotted grid does not
  create resolution.

## Common interpretation mistakes

- Calling excess bistatic path "range" without specifying geometry.
- Converting passive Doppler directly to monostatic radial speed.
- Reading separately normalized colors as absolute suppression.
- Treating the strongest pre-cancellation cell as a target.
- Assuming one complex coefficient removes delayed multipath.
- Assuming more cancellation taps are always safer for slow targets.
- Confusing delay-grid spacing with waveform bandwidth and delay resolution.
- Treating synthetic coherence as calibrated probability of detection.

## Dependencies and claim boundary

P08 introduced correlation; P18 made signed complex frequency visible; P26
introduced learned cancellation; P34 established delay-Doppler ambiguity; P36
connected Doppler to coherent phase; and P42 formed a two-dimensional
range-Doppler map. P81 is the governed batch prerequisite. P82 reuses those
ideas with a non-cooperative illuminator and two receive channels.

The source targets base MATLAB R2016b+ and uses no toolbox or external data.
Static checks and an independent Python oracle can test contracts and the
model equations. They are not MATLAB runtime, physical radar/HIL, bench,
field, real-time, or operational validation.
