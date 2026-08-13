# P74: Create a Micro-Doppler Spectrogram

**Phase 8: FMCW, MIMO, and Micro-Doppler**  
**Status:** Implemented by governed batch `P74`

## Guiding question

How do rotating or swinging target parts produce time-varying Doppler around bulk motion?

## Experiment

Build one deterministic complex slow-time return from a steadily approaching
torso and two oppositely swinging limb scatterers. The script exposes each
scatterer's radial velocity and phase before summing them, then implements the
full-record Doppler FFT and short-time Fourier transform (STFT) with explicit
windows, frame extraction, and FFTs.

The baseline plots raw complex phase, a dwell-wide Doppler spectrum, and a
signed spectrogram. Three controlled sweeps change swing speed, carrier
frequency, and STFT window duration one variable at a time. An intentionally
broken path discards I/Q phase with `abs`, then recovers the signed
micro-Doppler view from the unchanged complex measurement.

## Learning goal

Identify the nearly constant bulk Doppler ridge and distinguish it from the
periodic side tracks produced by component motion. Explain why a full-dwell
spectrum loses timing, why carrier frequency scales Doppler in hertz, and why
STFT window duration trades time localization against Doppler resolution.

## Prerequisites and dependencies

- P15 supplies explicit STFT and window-duration intuition.
- P18 explains why complex I/Q preserves signed frequency.
- P36 connects radial velocity with coherent phase progression.
- P70 supplies the selected-range-bin slow-time interpretation.
- P73 is the governed curriculum prerequisite.
- Runtime target: base MATLAB R2016b or newer; no optional toolbox is used.

## Run

```matlab
cd modules/74-create-a-micro-doppler-spectrogram
run('experiment.m')
```

Then follow `walkthrough.md` one observation at a time and use `checks.md` for
the completion conversation. The script is a bounded synthetic learning model,
not a physical-radar, human-gait classifier, or operational validation.

## Files

- `experiment.m` — deterministic model, explicit FFT/STFT, three sweeps,
  broken case, recovery, assertions, and retained metrics
- `lesson.md` — physical model, equations, limits, and interpretation traps
- `walkthrough.md` — guided baseline, controlled changes, failure, recovery,
  cancellation, and rollback
- `checks.md` — answered observation/prediction checks and teach-back rubric

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Keep the guiding question exactly:
"How do rotating or swinging target parts produce time-varying Doppler around
bulk motion?" Start with the physical velocity-to-phase model, inspect one
baseline plot at a time, vary only one physical or STFT parameter per step,
make the magnitude-only failure explicit, and finish with a short teach-back.
Do not turn the lesson into MATLAB syntax instruction or describe static checks
as MATLAB runtime evidence.
