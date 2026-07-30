# P20: Estimate Tone Frequency and Phase from Noisy Samples

**Phase 2: Fourier, Spectral, and I/Q Intuition**  
**Status:** Scaffolded; implementation batch `P20` is pending

## Guiding question

How accurately can frequency and phase be estimated from a finite noisy record?

## Experiment

Generate one complex tone at a fractional FFT bin with controlled SNR and estimate frequency using peak-bin, interpolated-FFT, and phase-increment methods.

## Procedure

Sweep SNR and record length. Compare bias, variance, phase wrapping, and failure cases when amplitude becomes small.

## What this should teach

Estimator performance depends on observation time, SNR, model assumptions, and whether it uses phase coherently.

## Completion condition

You can show which estimator is most reliable in each SNR/record-length region.

## Start or implement

```bash
./bin/learn start 20
```

If this module is scaffolded, tutor mode may review this brief but must not pretend the experiment is complete. Activate Portfolio Control batch `P20` to add the runnable MATLAB experiment, explanation, walkthrough, checks, validation, and evidence.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Estimate Tone Frequency and Phase from Noisy Samples". The guiding question is: "How accurately can frequency and phase be estimated from a finite noisy record?" Use this experiment: Generate one complex tone at a fractional FFT bin with controlled SNR and estimate frequency using peak-bin, interpolated-FFT, and phase-increment methods. Have me perform these actions: Sweep SNR and record length. Compare bias, variance, phase wrapping, and failure cases when amplitude becomes small. The main concept I must learn is: Estimator performance depends on observation time, SNR, model assumptions, and whether it uses phase coherently. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Files currently present

- `README.md`
