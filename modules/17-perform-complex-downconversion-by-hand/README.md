# P17: Perform Complex Downconversion by Hand

**Phase 2: Fourier, Spectral, and I/Q Intuition**  
**Status:** Scaffolded; implementation batch `P17` is pending

## Guiding question

How does multiplying by a complex oscillator move an RF/IF signal to baseband?

## Experiment

Create a real passband tone or modulated signal, multiply by exp(-j2*pi*fLO*t), and low-pass filter the result.

## Procedure

Try LO exactly on the carrier, slightly offset, and on the wrong side. Plot spectra before mixing, after mixing, and after filtering, plus the baseband IQ trajectory.

## What this should teach

Complex mixing translates frequency while preserving sign, amplitude, and phase; low-pass filtering selects the desired translated band.

## Completion condition

You can predict the baseband frequency and rotation direction for any carrier/LO offset.

## Start or implement

```bash
./bin/learn start 17
```

If this module is scaffolded, tutor mode may review this brief but must not pretend the experiment is complete. Activate Portfolio Control batch `P17` to add the runnable MATLAB experiment, explanation, walkthrough, checks, validation, and evidence.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Perform Complex Downconversion by Hand". The guiding question is: "How does multiplying by a complex oscillator move an RF/IF signal to baseband?" Use this experiment: Create a real passband tone or modulated signal, multiply by exp(-j2*pi*fLO*t), and low-pass filter the result. Have me perform these actions: Try LO exactly on the carrier, slightly offset, and on the wrong side. Plot spectra before mixing, after mixing, and after filtering, plus the baseband IQ trajectory. The main concept I must learn is: Complex mixing translates frequency while preserving sign, amplitude, and phase; low-pass filtering selects the desired translated band. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Files currently present

- `README.md`
