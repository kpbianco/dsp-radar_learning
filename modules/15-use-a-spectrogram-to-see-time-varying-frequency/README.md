# P15: Use a Spectrogram to See Time-Varying Frequency

**Phase 2: Fourier, Spectral, and I/Q Intuition**  
**Status:** Implemented by governed batch `P15`

## Guiding question

How do window duration and overlap control time-frequency visibility?

## Experiment

Build one deterministic four-second record containing a 90 Hz steady tone, a
gated 220-to-320 Hz chirp, a 64-sample 380 Hz burst, and a continuous-phase
frequency hop from 156 to 174 Hz. Form every spectrogram explicitly by slicing
the record, multiplying by a symmetric Hann window, taking an FFT, and scaling
the one-sided power spectral density (PSD).

## Procedure

1. Inspect the baseline 128-sample, 50%-overlapped spectrogram and its frequency,
   frame-time, burst-time, and chirp-ridge metrics.
2. Sweep the window through 512, 128, and 64 samples while holding overlap at
   50%. Compare close-frequency visibility with transient localization.
3. Hold the window at 128 samples and sweep overlap through 0%, 50%, and 75%.
   Compare time-column spacing and capture of the boundary-aligned burst.
4. Deliberately zero-pad the 64-sample window to 512 FFT points and make the
   broken claim that its 2 Hz display spacing is 2 Hz physical resolution.
   Recover by comparing the 64 Hz Hann main-lobe scale with the 18 Hz hop.

## What this should teach

A spectrogram is a bank of finite-time views, not a measurement with independent
time and frequency knobs. A short window follows transients quickly but produces
broad spectral responses. A long window narrows those responses but mixes a
longer interval into each time column. Overlap samples that same windowed view
more often; it does not narrow the window response. Zero-padding makes a smoother
frequency grid but does not undo the uncertainty tradeoff.

## Completion condition

You can explain why the short window best localizes the burst and hop, why the
long window best distinguishes the two hop frequencies near the transition,
and why neither heavy overlap nor zero-padding creates missing physical
resolution.

## Dependencies and execution boundary

- Learning dependencies: P11 maps FFT bins to hertz, P12 explains the Hann
  response, P13 separates display spacing from true resolution, and P14 shows
  how overlap reuses finite records.
- Runtime dependency: base MATLAB only. The script does not call `spectrogram`,
  `stft`, `pspectrum`, or a toolbox estimator; the STFT equation, windowing,
  frame centers, FFT, one-sided conversion, and PSD scaling are visible.
- A private seed-1015 `RandStream` generates the small noise component. The run
  writes no files, leaves MATLAB's global random stream unchanged, and replaces
  only figures tagged `P15`. At rerun start it removes prior tagged figures and
  clears the prior `results` value so malformed input cannot leave stale P15
  output looking current.
- Fixed ceilings bound the record at 4096 samples, windows and FFTs at 512
  points, frames at 256 per case, sweep cases at four, spectrogram storage at
  100000 cells per case, and figure groups at four. Press Ctrl+C to cancel;
  rerunning from the top reconstructs the same signal and needs no cleanup.
- Repository checks are static and independently reproduce the STFT/PSD
  equations. They do not claim MATLAB execution, rendered-figure review, or
  learner effectiveness.

## Start

```bash
./bin/learn start 15
```

Follow `walkthrough.md` one observation at a time and use `checks.md` before
recording learner completion.

## Recovery and rollback

If a visible control is malformed or a run is interrupted, correct it and rerun
from the top; no partial file state exists. To roll back the batch, remove only
P15-owned artifacts, tests, catalog changes, and evidence, then restore only the
P15 manifest status to `scaffolded`. Preserve P14 and ignored `.learning/`
progress.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Use a Spectrogram to See Time-Varying Frequency". The guiding question is: "How do window duration and overlap control time-frequency visibility?" Use this experiment: Create a signal containing a steady tone, a chirp, a short burst, and a frequency hop, then display spectrograms with several window lengths. Have me perform these actions: Use short and long STFT windows with matched and mismatched overlap. Compare localization of the burst and separation of close frequencies. The main concept I must learn is: The uncertainty tradeoff prevents arbitrarily fine time and frequency resolution simultaneously. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.
