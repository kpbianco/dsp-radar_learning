# P14: Compare Periodogram and Welch PSD Estimates

**Phase 2: Fourier, Spectral, and I/Q Intuition**  
**Status:** Implemented by governed batch `P14`

## Guiding question

Why does averaging make a noise spectrum easier to interpret?

## Experiment

Estimate the one-sided power spectral density (PSD) of the same four-second,
real-valued noisy two-tone record in two ways: one full-record periodogram and
an explicit Welch average of shorter, overlapping Hann-windowed segments.
Then change segment length, change overlap, repeat the noise realization across
24 private seeds, and deliberately average dB values the wrong way.

## Procedure

1. Compare the fine but jagged full-record periodogram with the coarser,
   steadier 15-segment Welch estimate.
2. Sweep segment length through 1024, 512, and 256 samples at fixed 50%
   overlap. Read noise ripple beside frequency spacing and weak-tone
   prominence.
3. Sweep overlap through 0%, 50%, and 75% at a fixed 512-sample segment. Compare
   actual segment count with an approximate independent-average count.
4. Repeat 24 seeded noise realizations at a tone-free 360 Hz probe and compare
   estimator coefficient of variation.
5. Run the broken average-in-dB calculation, classify its low bias, and recover
   by averaging linear `V^2/Hz` values before converting once to dB.

## What this should teach

A periodogram preserves the full record's fine frequency scale but has high
realization-to-realization variance. Welch averaging makes random spectral
fluctuations steadier by trading each long observation for several shorter
ones. Segment duration sets frequency resolution; overlap reuses more of the
record but does not create the same number of independent observations as its
raw segment count suggests.

## Completion condition

You can choose segment length and averaging based on the weakest feature you
need to resolve, explain what overlap does and does not buy, and keep PSD
averaging in linear power units.

## Dependencies and execution boundary

- Learning dependencies: P11 supplies the FFT frequency map, P12 supplies the
  Hann-window response and normalization intuition, and P13 distinguishes
  display spacing from true finite-observation resolution.
- Runtime dependency: base MATLAB only. The main operation is explicit; the
  script does not call `periodogram`, `pwelch`, or another toolbox estimator.
- The record and 24-trial repeat use private `RandStream` instances, write no
  files, do not alter MATLAB's global random stream, and replace only figures
  tagged `P14`.
- Fixed limits bound the record at 4096 samples, FFT length at 4096, segment
  count at 32, trial count at 24, sweep cases at eight, and figure groups at
  four. Press Ctrl+C to cancel; rerunning from the top reconstructs the same
  samples and requires no cleanup.
- Repository checks are static and independently reproduce the PSD equations.
  They do not claim MATLAB execution, rendered-figure review, or educational
  effectiveness.

## Start

```bash
./bin/learn start 14
```

Follow `walkthrough.md` one observation at a time and use `checks.md` before
recording learner completion.

## Recovery and rollback

For an interrupted or malformed run, correct the visible control and rerun
from the top; no partial file state exists. To roll back the batch, remove only
P14-owned artifacts, tests, catalog changes, and evidence, then restore only
the P14 manifest status to `scaffolded`. Preserve P13 and ignored `.learning/`
progress.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Compare Periodogram and Welch PSD Estimates". The guiding question is: "Why does averaging make a noise spectrum easier to interpret?" Use this experiment: Estimate the PSD of noisy tones using one periodogram and Welch averaging with different segment lengths and overlaps. Have me perform these actions: Repeat the experiment with different random seeds. Compare variance, frequency resolution, and weak-tone visibility as segment length and averaging change. The main concept I must learn is: PSD estimation trades resolution for statistical variance; averaging stabilizes noise estimates but shortens each effective observation. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.
