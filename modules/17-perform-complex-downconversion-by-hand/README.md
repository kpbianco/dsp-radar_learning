# P17: Perform Complex Downconversion by Hand

**Phase 2: Fourier, Spectral, and I/Q Intuition**  
**Status:** Implemented by governed batch `P17`

## Guiding question

How does multiplying by a complex oscillator move an RF/IF signal to baseband?

## Experiment

Create a deterministic real 240 Hz passband tone, multiply it sample by sample
by `exp(-j*2*pi*fLO*t)`, and low-pass filter the result with an explicit
windowed-sinc FIR. Inspect the desired difference-frequency term and the
sum-frequency image at every stage.

## Procedure

1. Run the exact-LO baseline and compare spectra before mixing, after mixing,
   and after filtering, plus the calibrated baseband I/Q point.
2. Sweep LO frequency through 204, 240, and 276 Hz. Read the signed outputs
   `+36`, `0`, and `-36` Hz and their counterclockwise, stationary, and
   clockwise I/Q motion.
3. Sweep only LO phase through `0`, `pi/2`, and `pi`. Confirm that it rotates
   the I/Q point without changing magnitude or frequency.
4. Deliberately reverse the oscillator sign at a 216 Hz LO. Observe that a real
   input supplies a conjugate spectral copy, so the wrong sign selects `-24 Hz`
   instead of the intended `+24 Hz`; restore the negative-exponent convention.

## What this should teach

Complex mixing translates frequency by subtraction while preserving signed
frequency and relative phase. A real cosine splits its peak amplitude equally
between positive and negative spectral copies, so the retained mixer term is
one half until the script applies a visible `2x` calibration. Low-pass filtering
selects the desired translated copy; it does not perform the translation.

## Completion condition

You can predict `fBB = fc - fLO`, its I/Q rotation direction, the output phase
`phiRF - phiLO`, the real-input one-half mixer gain, and which spectral copy the
low-pass filter retains.

## Dependencies and execution boundary

- Learning dependencies: P11 supplies signed FFT-bin mapping, P12 explains the
  mirrored spectrum of a real signal, and P16 introduces analytic/IQ magnitude
  and phase.
- Runtime dependency: base MATLAB only. The script exposes complex
  multiplication, every coefficient of the 129-tap Hamming-windowed sinc FIR,
  convolution, group-delay removal, and the real-input `2x` calibration. It
  does not call `lowpass`, `fir1`, `designfilt`, `filter`, `downconvert`, a
  toolbox demodulator, or an opaque receiver object.
- A private seed-1017 `RandStream` creates bounded noise without changing the
  global random stream. The script writes no files and replaces only figures
  tagged `P17` and its own `results` variable.
- Fixed ceilings bound the record and FFT at 4096 samples, the FIR at 129 taps,
  each sweep at three cases, retained numeric storage at 180000 values, and
  figure groups at five. Press Ctrl+C to cancel. Rerunning clears stale P17
  output, validates controls before allocation, and recreates the same noise.
- Repository checks use static source contracts and an independent Python
  numerical model. They are not MATLAB/Octave execution, rendered-figure
  inspection, learner validation, or hardware evidence.

## Start

```bash
./bin/learn start 17
```

Follow `walkthrough.md` one observation at a time and use `checks.md` before
recording personal completion.

## Recovery and rollback

If a control is rejected or the foreground run is interrupted, correct it and
rerun from the top; there is no file, timer, worker, or background state to
repair. Rollback removes only P17-owned artifacts, allowed catalog/CLI tests,
and P17 evidence, then restores only P17's manifest status to `scaffolded`.
Preserve implemented P16, later canonical identities, and ignored `.learning/`
progress.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Perform Complex Downconversion by Hand". The guiding question is: "How does multiplying by a complex oscillator move an RF/IF signal to baseband?" Use this experiment: Create a real passband tone or modulated signal, multiply by exp(-j2*pi*fLO*t), and low-pass filter the result. Have me perform these actions: Try LO exactly on the carrier, slightly offset, and on the wrong side. Plot spectra before mixing, after mixing, and after filtering, plus the baseband IQ trajectory. The main concept I must learn is: Complex mixing translates frequency while preserving sign, amplitude, and phase; low-pass filtering selects the desired translated band. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.
