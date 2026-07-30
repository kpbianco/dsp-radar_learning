# P12: Separate Leakage from Noise

**Phase 2: Fourier, Spectral, and I/Q Intuition**  
**Status:** Scaffolded; implementation batch `P12` is pending

## Guiding question

Why does a perfectly clean tone spread across many FFT bins?

## Experiment

Analyze a noncoherent sinusoid using rectangular, Hann, Hamming, Blackman, and flat-top windows.

## Procedure

Keep the tone and record fixed while changing only the window. Compare main-lobe width, peak amplitude error, and sidelobe level on a dB plot.

## What this should teach

Spectral leakage comes from finite observation and endpoint discontinuity; windows trade resolution for sidelobe suppression or amplitude accuracy.

## Completion condition

You can select a window based on whether the task is resolving neighbors, measuring amplitude, or finding weak signals near strong ones.

## Start or implement

```bash
./bin/learn start 12
```

If this module is scaffolded, tutor mode may review this brief but must not pretend the experiment is complete. Activate Portfolio Control batch `P12` to add the runnable MATLAB experiment, explanation, walkthrough, checks, validation, and evidence.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Separate Leakage from Noise". The guiding question is: "Why does a perfectly clean tone spread across many FFT bins?" Use this experiment: Analyze a noncoherent sinusoid using rectangular, Hann, Hamming, Blackman, and flat-top windows. Have me perform these actions: Keep the tone and record fixed while changing only the window. Compare main-lobe width, peak amplitude error, and sidelobe level on a dB plot. The main concept I must learn is: Spectral leakage comes from finite observation and endpoint discontinuity; windows trade resolution for sidelobe suppression or amplitude accuracy. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Files currently present

- `README.md`
