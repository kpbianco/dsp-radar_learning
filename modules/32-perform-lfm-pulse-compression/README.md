# P32: Perform LFM Pulse Compression

**Phase 4: Pulsed and Pulse-Doppler Radar Foundations**  
**Status:** Implemented by batch `P32`

## Guiding question

How can a long energetic pulse achieve short-pulse range resolution?

## Experiment

Generate an LFM chirp, create delayed echoes, and correlate with a matched replica.

## Procedure

Compare the raw long echo with the compressed output. Sweep chirp bandwidth and duration independently. Measure compressed width and processing gain.

## What this should teach

Pulse compression combines energy from long duration with resolution set mainly by bandwidth.

## Completion condition

You can predict how bandwidth changes compressed width and how time-bandwidth product changes gain.

## Prerequisites and dependencies

- Complete P31 first so bandwidth-driven range response width is familiar.
- Run in base MATLAB; no toolbox is required.
- The experiment uses only deterministic synthetic complex-baseband echoes. It
  does not model an RF transmitter, propagation hardware, Doppler, clutter, or
  an operational detector.

## Start or implement

```bash
./bin/learn start 32
```

The learner CLI opens the implemented lesson and its tutor walkthrough. Run
`experiment.m` for the deterministic baseline, the independent bandwidth and
duration sweeps, and the mismatched-replica failure and recovery.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Perform LFM Pulse Compression". The guiding question is: "How can a long energetic pulse achieve short-pulse range resolution?" Use this experiment: Generate an LFM chirp, create delayed echoes, and correlate with a matched replica. Have me perform these actions: Compare the raw long echo with the compressed output. Sweep chirp bandwidth and duration independently. Measure compressed width and processing gain. The main concept I must learn is: Pulse compression combines energy from long duration with resolution set mainly by bandwidth. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Implemented files

- `README.md`
- `experiment.m`
- `lesson.md`
- `walkthrough.md`
- `checks.md`
