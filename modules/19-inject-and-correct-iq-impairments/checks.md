# P19 Checks: Diagnose the Receiver Before Correcting It

## Guiding question

How do DC offset, gain mismatch, and quadrature error change an IQ spectrum?

## Baseline observation checks

1. Which impairment creates a shifted I/Q center and a zero-frequency spike?
   Expected: DC offset. It changes the sample mean but does not by itself
   create the deterministic conjugate image of this tone.
2. Which impairments create the `-160 Hz` image from a `+160 Hz` tone?
   Expected: unequal I/Q gains and quadrature phase error. Both mix in a
   conjugate component.
3. How does gain mismatch differ geometrically from phase error?
   Expected: pure gain mismatch changes the ellipse axis lengths; pure phase
   error shears/tilts the axes and creates nonzero I/Q correlation.
4. Is the negative-frequency image necessarily a second physical source?
   No. In this controlled experiment it is created inside the receiver model.
5. Why are coherent tone projections used in addition to the centered FFT?
   The FFT makes the artifact locations visible; the projections measure the
   desired and conjugate coefficients directly at their known frequencies.

## Correction and sweep prediction checks

1. Why must mean removal precede gain and phase estimation?
   Offset contaminates branch RMS and covariance, so later estimates would mix
   center error with scale and phase-axis error.
2. What should mean removal change?
   The measured DC magnitude should collapse. Image rejection need not improve
   because the imbalance mechanisms remain.
3. As `gI` changes from `1.00` to `1.30` with `gQ=1`, what happens?
   The horizontal-to-vertical axis ratio grows and IRR falls according to
   `(gI+gQ)/abs(gI-gQ)`.
4. As quadrature error changes from `0` to `15 degrees`, what happens?
   I/Q correlation approaches `sin(phi)`, the trajectory tilts more, and IRR
   falls according to `cot(abs(phi)/2)` for equal gains.
5. Why is a full-cycle circular calibration tone important?
   Its ideal mean is zero, its branch powers are equal, and its I/Q covariance
   is zero. Without that excitation assumption, signal statistics can be
   mistaken for receiver error.

## Broken-case and interpretation checks

1. What does the broken case do?
   It globally rotates the gain-corrected complex stream by `-phiHat`.
2. Why does broken IRR remain unchanged?
   A complex rotation multiplies desired and image components by unit-magnitude
   phase factors. It changes their angles, not their magnitudes.
3. What operation actually repairs this model?
   Undo the shear with `Qcorrected=(Q-I*sin(phiHat))/cos(phiHat)` after mean and
   gain correction.
4. Can blind mean subtraction erase a desired signal?
   Yes. A desired component at true baseband DC is indistinguishable from
   receiver offset without another calibration assumption.
5. What happens near `|phi|=90 degrees`?
   `cos(phi)` approaches zero, so inversion becomes singular and amplifies
   noise. This experiment rejects that regime before allocation.
6. Does this one tone calibrate nonlinear or frequency-selective hardware?
   No. It validates only the lesson's static, memoryless I/Q model.

## Malformed, resource, timeout, cancellation, and isolation checks

- A logical, complex, nonfinite, nonscalar, wrong seed/rate/count/frequency,
  noncoherent tone, invalid amplitude/noise, changed offset/gain/error, changed
  sweep, nonpositive gain, noninvertible phase, or breached record/FFT/sweep/
  storage/figure ceiling must fail before random, signal, FFT, cleanup, or
  figure allocation.
- Work is bounded by one 4096-sample baseline, two three-case sweeps, a 360000
  retained-value ceiling, five explicit case rows, four correction stages, and
  six figure groups. There is no wait, prompt, timer, parallel/background,
  file/network, system, or audio operation.
- Ctrl+C cancels the foreground run. An interrupt after cleanup can leave a
  partial P19 figure set and empty/incomplete `results`; rerun from the top to
  recover.
- A malformed rerun preserves the last valid P19 output because validation
  precedes cleanup. A valid rerun replaces only P19-tagged figures and
  `results`; the private stream leaves the global random stream and unrelated
  figures unchanged.
- Base MATLAB is the only runtime dependency. Static Python contracts and
  independent numerical models are not MATLAB/Octave execution or rendered
  plot evidence.

## Recovery and rollback check

- Recovery: restore the mean -> gain -> phase-shear order, rerun, and confirm
  lower DC, higher IRR, near-zero I/Q correlation, and lower complex-sample
  error.
- Rollback: remove P19-owned artifacts, allowed P19/shared tests and catalog
  edits, and P19 evidence; restore only P19 status to `scaffolded`. Preserve
  implemented P18, later canonical identity, `.learning/` state, and active
  batch activation.

## Teach-back completion

A satisfactory two- or three-sentence answer must:

- map DC offset to the center spike/shifted origin and map gain/quadrature
  imbalance to ellipse/shear plus a conjugate spectral image;
- explain why correction proceeds through mean removal, branch gain
  normalization, then quadrature-shear inversion; and
- explain why a global rotation changes carrier phase but cannot improve image
  rejection caused by nonorthogonal I/Q axes.

Do not record personal completion until the learner has inspected the plots and
given this teach-back. Learner progress remains local under `.learning/`.
