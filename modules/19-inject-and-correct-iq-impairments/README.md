# P19: Inject and Correct IQ Impairments

**Phase 2: Fourier, Spectral, and I/Q Intuition**  
**Status:** Implemented by batch `P19`

## Guiding question

How do DC offset, gain mismatch, and quadrature error change an IQ spectrum?

## Experiment

Create a clean complex tone or QPSK waveform, then add DC offset, unequal I/Q gains, and phase error.

## Procedure

Apply each impairment separately and together. Measure carrier/image ratio, constellation shape, and center spike. Correct mean, gain, and phase in stages.

## What this should teach

Common direct-conversion receiver artifacts have distinct signatures and can often be estimated from the samples.

## Completion condition

You can identify each impairment visually and improve image rejection with simple corrections.

## Dependencies

- P18: complex samples, signed spectra, and the information carried by I and Q

Base MATLAB is sufficient. The script uses a private deterministic random
stream and explicit arithmetic; no RF, DSP, or Communications Toolbox is
required.

## Start or implement

```bash
./bin/learn start 19
```

Tutor mode should state the guiding question, inspect the baseline signatures,
change one impairment at a time, and use `checks.md` before recording personal
completion.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Inject and Correct IQ Impairments". The guiding question is: "How do DC offset, gain mismatch, and quadrature error change an IQ spectrum?" Use this experiment: Create a clean complex tone or QPSK waveform, then add DC offset, unequal I/Q gains, and phase error. Have me perform these actions: Apply each impairment separately and together. Measure carrier/image ratio, constellation shape, and center spike. Correct mean, gain, and phase in stages. The main concept I must learn is: Common direct-conversion receiver artifacts have distinct signatures and can often be estimated from the samples. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Implemented files

- `README.md`
- `experiment.m`
- `lesson.md`
- `walkthrough.md`
- `checks.md`
