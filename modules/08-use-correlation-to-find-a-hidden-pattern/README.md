# P08: Use Correlation to Find a Hidden Pattern

**Phase 1: Signals, Sampling, and Systems**  
**Status:** Scaffolded; implementation batch `P08` is pending

## Guiding question

How can a known waveform be located inside noise and delay?

## Experiment

Embed a short known code or pulse at an unknown delay in a longer noisy record and cross-correlate with the reference.

## Procedure

Vary delay, amplitude, and noise. Compare raw waveform visibility with the correlation peak. Add a second delayed copy and see when the peaks merge.

## What this should teach

Correlation measures similarity versus relative delay and is the conceptual core of synchronization, matched filtering, and radar ranging.

## Completion condition

You can estimate the hidden signal delay even when the waveform is not obvious in time.

## Start or implement

```bash
./bin/learn start 8
```

If this module is scaffolded, tutor mode may review this brief but must not pretend the experiment is complete. Activate Portfolio Control batch `P08` to add the runnable MATLAB experiment, explanation, walkthrough, checks, validation, and evidence.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Use Correlation to Find a Hidden Pattern". The guiding question is: "How can a known waveform be located inside noise and delay?" Use this experiment: Embed a short known code or pulse at an unknown delay in a longer noisy record and cross-correlate with the reference. Have me perform these actions: Vary delay, amplitude, and noise. Compare raw waveform visibility with the correlation peak. Add a second delayed copy and see when the peaks merge. The main concept I must learn is: Correlation measures similarity versus relative delay and is the conceptual core of synchronization, matched filtering, and radar ranging. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Files currently present

- `README.md`
