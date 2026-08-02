# P16: Create an Analytic Signal with the Hilbert Transform

**Phase 2: Fourier, Spectral, and I/Q Intuition**  
**Status:** Implemented by governed batch `P16`

## Guiding question

How can a real waveform be represented by a complex envelope?

## Experiment

Create one deterministic, amplitude- and phase-varying real bandpass signal.
Form its analytic signal explicitly with an FFT-domain Hilbert mask, then compare
the real waveform, analytic magnitude, unwrapped phase, instantaneous frequency,
and positive/negative-frequency spectra.

## Procedure

1. Inspect the baseline real waveform and the analytic signal's envelope, phase,
   and phase-difference frequency estimate.
2. Sweep only envelope modulation depth through `0.20`, `0.60`, and `0.90` while
   preserving the phase law and noise realization.
3. Sweep only phase-deviation index through `0.20`, `0.60`, and `1.20` radians
   while preserving the envelope and noise realization.
4. Deliberately notch the envelope almost to zero below the noise scale. Observe
   the unstable phase and frequency spike, then recover by requiring both phase-
   difference endpoints to exceed a visible amplitude threshold.

## What this should teach

A real bandpass signal stores the same information in mirrored positive- and
negative-frequency components. The analytic signal removes that redundancy and
packages the waveform as a rotating complex quantity: magnitude is envelope and
angle is phase. Instantaneous frequency is the phase slope, but angle has no
stable physical direction when magnitude approaches zero.

## Completion condition

You can recover the designed envelope, explain how the FFT mask creates the
analytic signal, connect phase slope to instantaneous frequency, and identify
where instantaneous frequency becomes meaningless.

## Dependencies and execution boundary

- Learning dependencies: P11 maps FFT bins to hertz, P12 establishes mirrored
  real-signal spectra and finite-record effects, and P15 introduces time-varying
  frequency.
- Runtime dependency: base MATLAB only. The script explicitly constructs the
  even-length analytic mask, doubles positive-frequency bins, retains DC and
  Nyquist, zeroes negative-frequency bins, and applies `ifft`. It does not call
  `hilbert`, `envelope`, or an opaque toolbox estimator.
- A private seed-1016 `RandStream` creates bounded baseline and broken-case
  noise without changing MATLAB's global random stream. The script writes no
  files and replaces only figures tagged `P16`.
- Fixed ceilings bound the record and FFT at 4096 samples, each sweep at three
  cases, retained numeric storage at 250000 values, and figure groups at five.
  Press Ctrl+C to cancel. Rerunning first removes stale P16 figures and `results`,
  then validates every visible control before random, signal, FFT, or figure
  allocation.
- Repository validation is static and includes an independent numerical model.
  It is not MATLAB execution, rendered-figure review, or learner validation.

## Start

```bash
./bin/learn start 16
```

Follow `walkthrough.md` one observation at a time and use `checks.md` before
recording learner completion.

## Recovery and rollback

If a control is malformed or a run is interrupted, correct it and rerun from
the top; no file, background task, or partial persistent state needs cleanup.
To roll back P16, remove only P16-owned module artifacts, tests, catalog changes,
and evidence, then restore only P16's manifest status to `scaffolded`. Preserve
P15, later canonical module identities, and ignored `.learning/` progress.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Create an Analytic Signal with the Hilbert Transform". The guiding question is: "How can a real waveform be represented by a complex envelope?" Use this experiment: Generate an amplitude- and phase-varying real bandpass signal, form its analytic signal, and extract envelope and instantaneous phase. Have me perform these actions: Compare the real signal, analytic magnitude, unwrapped phase, and instantaneous frequency. Include a case where amplitude approaches zero and phase becomes unstable. The main concept I must learn is: The analytic signal suppresses negative-frequency redundancy and exposes envelope and phase, but instantaneous phase is unreliable at low amplitude. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.
