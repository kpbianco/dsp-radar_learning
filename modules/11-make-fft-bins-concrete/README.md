# P11: Make FFT Bins Concrete

**Phase 2: Fourier, Spectral, and I/Q Intuition**  
**Status:** Scaffolded; implementation batch `P11` is pending

## Guiding question

What frequency does each FFT bin represent?

## Experiment

Generate tones exactly on a bin and halfway between bins for several record lengths.

## Procedure

Label the bin frequencies, place a coherent tone exactly on one, then move it by fractional-bin offsets. Compare magnitude and phase at neighboring bins.

## What this should teach

FFT bins are projections onto discrete complex sinusoids determined jointly by sample rate and record length.

## Completion condition

You can calculate the expected bin number for a tone and explain what changes when it lies between bins.

## Start or implement

```bash
./bin/learn start 11
```

If this module is scaffolded, tutor mode may review this brief but must not pretend the experiment is complete. Activate Portfolio Control batch `P11` to add the runnable MATLAB experiment, explanation, walkthrough, checks, validation, and evidence.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Make FFT Bins Concrete". The guiding question is: "What frequency does each FFT bin represent?" Use this experiment: Generate tones exactly on a bin and halfway between bins for several record lengths. Have me perform these actions: Label the bin frequencies, place a coherent tone exactly on one, then move it by fractional-bin offsets. Compare magnitude and phase at neighboring bins. The main concept I must learn is: FFT bins are projections onto discrete complex sinusoids determined jointly by sample rate and record length. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Files currently present

- `README.md`
