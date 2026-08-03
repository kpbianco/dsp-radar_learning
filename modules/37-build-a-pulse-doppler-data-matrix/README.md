# P37: Build a Pulse-Doppler Data Matrix

**Phase 4: Pulsed and Pulse-Doppler Radar Foundations**  
**Status:** Implemented by batch `P37`

## Guiding question

What are fast time and slow time in a radar data block?

## Experiment

Build a complex pulse-Doppler matrix whose rows are samples taken after each
transmit event and whose columns are successive pulses. Three idealized targets
have independent ranges and radial velocities. Their delays select rows; their
Doppler phase progression runs across columns.

The baseline shows selected pulse columns, selected target rows, and the whole
matrix magnitude. Two one-variable sweeps make the axes concrete:

1. changing only target range moves the bright response to another fast-time
   row; and
2. changing only target velocity changes the slow-time phase slope while the
   target stays in the same row.

The intentionally broken case takes matrix magnitude before slow-time
processing. The target range remains visible, but the complex phase history
and signed Doppler are lost. Recovery restores the coherent complex matrix and
recreates the private seeded noise exactly.

## What this teaches

For fast-time sample `n` and pulse index `p`, the transparent model is

```text
X[n,p] = sum_k A_k g[n-n_k] exp(j(phi_k + 2 pi f_d,k p/PRF)) + w[n,p]
n_k = round((2 R_k/c) f_s)
f_d,k = 2 v_k/lambda
```

Delay chooses a row and therefore range. Repeated coherent looks at that row
form a slow-time sequence whose phase rate carries Doppler. A magnitude image
can locate range energy, but magnitude alone cannot show the signed phase
rotation.

## Run

From the repository root, run:

```matlab
run('modules/37-build-a-pulse-doppler-data-matrix/experiment.m')
```

Inspect the six `P37`-tagged figure groups and the `results` structure. The
script is finite, noninteractive, deterministic through private `RandStream`
instances, and closes only figures tagged `P37`.

## Dependencies and compatibility

- P35 supplies fast-time delay, range-bin spacing, and the one-PRI range
  interval.
- P36 supplies coherent pulse-to-pulse phase, Doppler sign, and the PRF
  aliasing limit.
- P18 supplies the signed complex-frequency picture.

The transparent path uses base MATLAB array construction, complex arithmetic,
`unwrap`, and `fft`; no Phased Array System Toolbox object, range helper, or
Doppler helper is required. The matrix represents idealized range-resolved I/Q
samples, not waveform propagation or a full range-Doppler processor. It is not
hardware, HIL, field, real-time, deployment, or operational-radar validation.

## Tutor entry

```bash
./bin/learn start 37
```

Begin with the whole-matrix view. Ask which axis changes when target delay
changes, then inspect one target row across pulses before changing velocity.

## Completion condition

You can trace one target through raw data to its range bin and slow-time sinusoid.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Build a Pulse-Doppler Data Matrix". The guiding question is: "What are fast time and slow time in a radar data block?" Use this experiment: Simulate several pulsed-radar targets with independent ranges and velocities and arrange samples as fast-time by pulse. Have me perform these actions: Plot selected pulses, selected range bins across pulses, and the matrix magnitude. Label which dimension contains delay/range and which contains Doppler history. The main concept I must learn is: Pulse-Doppler processing separates within-pulse delay from pulse-to-pulse phase evolution. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Files

- `experiment.m` — deterministic matrix construction, plots, sweeps, failure,
  and recovery
- `lesson.md` — physical model, conventions, limiting cases, and connections
- `walkthrough.md` — guided observations and one-variable changes
- `checks.md` — observation, prediction, recovery, and teach-back checks
