# P38: Implement a Two-Pulse and Three-Pulse MTI Canceller

**Phase 4: Pulsed and Pulse-Doppler Radar Foundations**  
**Status:** Implemented by batch `P38`

## Guiding question

How do simple delay-line cancellers remove stationary clutter?

## Experiment

Build a deterministic complex radar data matrix whose rows are range samples
and whose columns are coherent pulses. Strong stationary scatterers share the
scene—and one range cell—with much weaker moving targets. Apply the transparent
two-pulse and three-pulse operations across columns:

```text
y2[p] = x[p] - x[p-1]
y3[p] = x[p] - 2 x[p-1] + x[p-2]
```

The baseline compares the unfiltered scene, the two canceller outputs, exact
frequency responses, stationary-clutter residual, moving-target gain, and
white-noise power gain. Two one-variable sweeps change target velocity and PRF.
The intentionally broken case differences range rows instead of pulses; it
creates range edges but does not perform MTI. Recovery restores the slow-time
axis and recreates the private seeded noise exactly.

## What this teaches

The two-pulse response is `H2 = 1 - exp(-j omega)` and the three-pulse response
is `H3 = (1 - exp(-j omega))^2`, with
`omega = 2 pi f_d/PRF` and `f_d = 2 v/lambda`. Both responses are zero for
stationary clutter and repeat their null at every integer multiple of PRF. Near
zero Doppler, the three-pulse canceller rejects more strongly, but it can also
attenuate slow targets more and its `[1 -2 1]` coefficients multiply white-noise
power by six rather than the factor of two from `[1 -1]`.

## Run

From the repository root, run:

```matlab
run('modules/38-implement-a-two-pulse-and-three-pulse-mti-canceller/experiment.m')
```

Inspect the six `P38`-tagged figure groups and the `results` structure. The
script is finite, noninteractive, deterministic through private `RandStream`
instances, and closes only figures tagged `P38`.

## Dependencies and compatibility

- P36 supplies the signed pulse-to-pulse Doppler phase model and PRF ambiguity.
- P37 supplies the range-row by pulse-column complex data-matrix convention.

The transparent path uses base MATLAB complex arithmetic and explicit array
subtraction. It does not require Phased Array System Toolbox or an MTI/filter
design helper. The scene is an idealized coherent slow-time model with no range
migration, clutter spectrum, fluctuating targets, or waveform propagation. It
is not hardware, HIL, field, real-time, deployment, or operational-radar
validation.

## Tutor entry

```bash
./bin/learn start 38
```

Begin with the raw range profile and the stationary-clutter null. Then compare
the slow target's gain in the two cancellers before changing one parameter.

## Completion condition

You can explain which velocities are preserved or attenuated by each canceller.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Implement a Two-Pulse and Three-Pulse MTI Canceller". The guiding question is: "How do simple delay-line cancellers remove stationary clutter?" Use this experiment: Create slow-time data containing strong zero-Doppler clutter and weaker moving targets. Have me perform these actions: Apply first- and second-difference filters across pulses. Plot frequency response and compare clutter suppression, target attenuation, and noise amplification. The main concept I must learn is: MTI cancellers place spectral nulls at zero Doppler and periodically elsewhere; higher order sharpens clutter rejection but changes noise and target response. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Files

- `experiment.m` — deterministic scene, cancellers, responses, sweeps, failure,
  and exact recovery
- `lesson.md` — physical model, limiting cases, tradeoffs, and connections
- `walkthrough.md` — guided baseline, one-variable changes, and recovery
- `checks.md` — observation, prediction, interpretation, and teach-back checks
