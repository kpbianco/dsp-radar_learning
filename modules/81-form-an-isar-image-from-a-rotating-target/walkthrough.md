# P81 walkthrough: Let Rotation Supply the Looks

The guiding question is: **How does target rotation create synthetic aperture when the radar is stationary?**

Run `experiment.m` once. It creates five tagged figure groups and prints
bandwidth, wavelength, angular aperture, CPI, translation, resolution, layout,
and recovery metrics. Inspect one transition at a time.

## 1. Baseline: inspect range before cross-range

The radar is stationary at `10 GHz`; the rigid ten-scatterer target rotates
from `-3` to `+3 deg`. Coherent stepped frequencies span `600 MHz`, and the
target centroid translates at `2 m/s` during the `1 s` CPI.

Figure 1 left shows the explicit IFFT range profiles before compensation. The
bright tracks migrate by about `2 m`. Figure 1 right applies

```text
exp(+j 4 pi f_k d_p/c)
```

to the raw complex frequency history before repeating the IFFT. The envelopes
now share projected range and the common carrier phase is restored.

Concrete observation question: if the bright range tracks are shifted into
place using magnitude alone, what coherent information would the later
angle-domain FFT still be missing?

## 2. Focus the aligned aspect history

Figure 2 applies the angle-domain FFT independently to every range bin and maps
angular frequency with `x = -lambda f_theta/2`. White crosses show the declared
target-fixed scatterer layout.

- Nominal range resolution is `0.25 m` from `c/(2B)`.
- Nominal cross-range resolution is about `0.143 m` from
  `lambda/(2 Delta theta)`.
- Truth-neighborhood power and truth/background peak ratio are computed on
  unclipped linear image power. The normalized dB color is only for display.

The result is recognizable because different `y` values separate through
frequency diversity and different `x` values create different phase slopes
through angle.

## 3. Sweep 1: change only angular aperture

Figure 3 compares `2`, `4`, `6`, and `8 deg`, always using 65 looks. Carrier,
bandwidth, target, reflectivity, translation rule, and correct compensation
stay fixed.

1. Read the left plot: nominal cross-range resolution improves inversely with
   angular aperture.
2. Read the truth-map correlation on the right: the broad `2 deg` responses
   merge more of the layout than the `8 deg` responses.
3. Notice the trade: fixed look count means wider angle also means coarser
   angular sampling and a smaller unambiguous cross-range interval.

Prediction before looking at the last point: would extending this simple FFT
model indefinitely keep improving the image? No. Large angles expose
`sin(theta)` nonlinearity, `y cos(theta)` migration, aspect-dependent
reflectivity, and sampling limits.

## 4. Sweep 2: change rate while preserving the same angles

Figure 4 uses rates `3`, `6`, and `12 deg/s` but keeps the same `-3` to `+3 deg`
samples.

- CPI falls from `2 s` to `0.5 s`.
- The implied PRF rises from `32 Hz` to `128 Hz` because the same 65 angles
  arrive sooner; rotational Doppler remains below the matching Nyquist limit.
- Maximum cross-range Doppler magnitude in hertz grows in direct proportion to
  rate.
- Correlation with the `6 deg/s` angle-domain image stays essentially one
  after exact translation compensation.

This is the important controlled distinction: angular aperture sets nominal
cross-range resolution. Rate says how quickly those angles arrive and where
their phase slope appears in slow-time hertz. Faster rate would enlarge the
aperture only if CPI—not aspect span—were held fixed.

The `2 m/s` centroid path is handed to the processor as known unwrapped
displacement at every look. Its Doppler would be aliased at these PRFs, so this
lesson does not estimate translation from slow time.

## 5. Broken case: omit translation compensation

Figure 5 left sends the raw migrating profiles directly into the angle FFT.
Nothing else changes.

1. Range cells contain different scatterers at different looks.
2. Wideband range walk couples into the angle transform. Its linear carrier
   phase alone mainly shifts/wraps cross-range; nonlinear residual phase would
   add true defocus.
3. Coherent layout energy spreads and correlation with the aligned image falls below
   `0.65` in the reviewed case.
4. A bright normalized pixel does not rescue the geometry; compare the full
   image and retained correlation.

Figure 5 right recovers by returning to the unchanged raw complex history,
applying the complete frequency-dependent translation correction, and freshly
running range compression and angle focus. The result exactly matches Figure 2
through the deterministic path.

## 6. Recovery, cancellation, rerun, and isolation

The broken image is never used as recovery input. The raw `65 x 129` complex
history is retained and asserted unchanged before and after the failure path.

The script has finite bounded foreground loops and no timer, worker, file,
network, GPU, subprocess, or checkpoint. Press Ctrl+C to cancel. Cancellation
may leave partial P81 figures and variables, but no persistent state. Rerun
`experiment.m`; it closes prior figures tagged `P81`, rebuilds its private
seeded reflectivity, and does not alter MATLAB's global random stream.

## 7. Connect the concepts

- P75-P79: platform motion supplied aspect diversity for SAR; aperture length,
  sampling, and coherence controlled focus.
- P80: small unmodeled path errors corrupted coherent aperture phase.
- P81: target rotation supplies the aspect diversity, while translation and
  rotation estimates become target-motion compensation problems.
- P82 will replace active transmission with a known reference and a
  delay-Doppler search; it does not change P81's permanent identity.

The concise answer is: rotation makes each target-fixed cross-range coordinate
write a distinct two-way phase slope versus aspect. Preserve complex phase,
align centroid translation, collect enough well-sampled angular support, and
the stationary radar can form a range/cross-range image.

## Rollback and completion handoff

Repository rollback removes only P81-owned implementation/test/evidence and
restores only P81's manifest status to `scaffolded`. Preserve P80, future
module identities/statuses, personal `.learning/` state, and operator-managed
batch contracts.

Use `checks.md`. Completion requires a short teach-back that connects the echo
phase to cross-range, separates aperture from rate, explains both parts of
translation compensation, and identifies the small-angle/model limits.
