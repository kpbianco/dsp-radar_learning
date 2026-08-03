# P34: Plot and Interpret the Ambiguity Function

**Phase 4: Pulsed and Pulse-Doppler Radar Foundations**  
**Status:** Implemented by batch `P34`

## Guiding question

How does a waveform respond to simultaneous delay and Doppler mismatch?

## Experiment

Compute normalized narrowband ambiguity surfaces for an equal-duration
rectangular pulse, LFM chirp, and seeded binary phase-coded sequence using an
explicit zero-filled delay shift and Doppler phasor sum.

## Procedure

Compare two-dimensional delay-Doppler magnitude and the zero-delay and
zero-Doppler cuts. Sweep rectangular-pulse duration, LFM bandwidth, and code
length one variable at a time. Then replace the physical zero-filled shift
with an intentionally broken circular shift, observe wraparound energy, and
recover the original surface exactly.

## What this should teach

The ambiguity function summarizes delay resolution, Doppler tolerance,
sidelobes, and delay-Doppler coupling. A waveform is not simply “good” or
“bad”: its useful ambiguity shape depends on the sensing requirement.

## Completion condition

You can point to the main lobe and explain which waveform is best for a chosen delay/Doppler requirement.

## Prerequisites and dependencies

- Complete P33 first so matched-filter response shape, sidelobes, and receive
  mismatch are familiar.
- Run in base MATLAB. No toolbox is required, and the experiment does not call
  `ambgfun`, `xcorr`, or a phased-array object.
- The model is deterministic complex baseband with a private seed for the
  binary code. It is a finite-record narrowband simulation, not a hardware,
  clutter, detector, or operational-radar model.

## Start the implemented lesson

```bash
./bin/learn start 34
```

Run `experiment.m`, then use `walkthrough.md` and `checks.md` to interpret one
plot and one parameter change at a time.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Plot and Interpret the Ambiguity Function". The guiding question is: "How does a waveform respond to simultaneous delay and Doppler mismatch?" Use this experiment: Compute ambiguity surfaces for a rectangular pulse, LFM chirp, and phase-coded sequence. Have me perform these actions: Plot 2-D delay-Doppler magnitude and cuts through zero delay and zero Doppler. Change pulse duration, bandwidth, and code length. The main concept I must learn is: The ambiguity function summarizes waveform resolution, sidelobes, Doppler tolerance, and delay-Doppler coupling. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Implemented files

- `README.md`
- `experiment.m`
- `lesson.md`
- `walkthrough.md`
- `checks.md`
