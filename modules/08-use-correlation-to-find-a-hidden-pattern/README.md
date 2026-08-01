# P08: Use Correlation to Find a Hidden Pattern

**Phase 1: Signals, Sampling, and Systems**  
**Status:** Implemented by batch `P08`

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

## Run the lab

```bash
./bin/learn start 8
```

Run `experiment.m` in base MATLAB, then use `walkthrough.md` and `checks.md` to
connect the largest signed similarity peak to the hidden waveform's zero-based
start delay. The experiment writes no files and uses no toolbox, helper
function, external data, network, device, or service. It uses private seeded
noise, preserves the global random stream and unrelated figures, bounds all
loops and arrays, and creates or replaces only its named workspace variables
and P08-tagged figures.

## Dependency and operation contract

P07 is the prerequisite. The baseline embeds a fixed asymmetric Barker-coded
pulse in a longer noisy voltage record. It evaluates
`r_xs[lag] = sum_m x[lag+m]s[m]` with explicit bounded loops before using
base MATLAB `conv(x,fliplr(s))` as a numerical cross-check. The full lag vector is
constructed explicitly, so the essential similarity operation and the mapping
from vector index to physical delay are not hidden behind `xcorr`, `finddelay`,
a toolbox matched-filter object, or another black box.

The script includes two formal one-variable sweeps—hidden amplitude and
second-copy separation—plus a controlled noise-only comparison. The deliberately
broken case reports a convolution output index as a delay and creates a known
`M-1` sample error; recovery uses the explicit lag axis. Static repository
checks do not imply that MATLAB or the figures ran.

Batch rollback removes the four P08 implementation artifacts and P08
tests/evidence, restores this brief and public catalog wording, and must restore only P08
manifest status to `scaffolded`. It does not alter learner state or P07.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Use Correlation to Find a Hidden Pattern". The guiding question is: "How can a known waveform be located inside noise and delay?" Use this experiment: Embed a short known code or pulse at an unknown delay in a longer noisy record and cross-correlate with the reference. Have me perform these actions: Vary delay, amplitude, and noise. Compare raw waveform visibility with the correlation peak. Add a second delayed copy and see when the peaks merge. The main concept I must learn is: Correlation measures similarity versus relative delay and is the conceptual core of synchronization, matched filtering, and radar ranging. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Files

- `README.md`
- `experiment.m`
- `lesson.md`
- `walkthrough.md`
- `checks.md`
