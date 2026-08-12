# P72: Use Up/Down Triangular Chirps to Separate Range and Velocity

**Phase 8: FMCW, MIMO, and Micro-Doppler**  
**Status:** Implemented by governed batch `P72`

## Guiding question

How can opposite chirp slopes disentangle delay and Doppler?

## Experiment

Generate deterministic complex up- and down-chirp legs for one moving target,
dechirp each delayed Doppler-shifted echo with `tx .* conj(rx)`, and preserve
both signed beat frequencies. Their difference recovers delay and range; their
sum recovers signed Doppler and velocity.

## Procedure

Inspect both chirp slopes and beat spectra, then solve the two equations for
range and Doppler. Sweep range, velocity, and receiver noise one variable at a
time. In a two-target composite record, deliberately pair each up beat with
the wrong down beat, observe plausible ghost reports, and recover using the
unchanged detected beats with the correct association.

## What this should teach

For positive approaching velocity and the declared mixer,

```text
f_up   =  S tau - f_d,       f_down = -S tau - f_d,
R      =  c(f_up - f_down)/(4S),
v      = -lambda(f_up + f_down)/4.
```

Opposite slopes provide independent combinations of delay and Doppler for one
target. With multiple targets, the spectra do not label which up and down
beats belong together; every pairing produces a mathematical solution, so
association needs information beyond these two equations.

## Completion condition

You recover range and velocity for one target, predict what the range,
velocity, and noise sweeps change, and explain why multiple targets complicate
beat pairing.

## Run the lesson

```bash
./bin/learn start 72
```

In MATLAB, run `experiment`, follow `walkthrough.md` one observation at a time,
and use `checks.md` before giving the short teach-back.

## Dependencies and compatibility

P17 supplies complex mixer-sign intuition, P36 supplies the signed Doppler
law, P69 derives stationary FMCW beat-to-range conversion, P70 separates fast-
and slow-time measurements, and P71 exposes the one-slope coupling that this
module resolves. P71 is the governed batch prerequisite.

The script requires MATLAB R2016b or newer and no optional toolbox. It uses
explicit quadratic phase, delayed echoes, `tx .* conj(rx)`, manual Hann
windows, base-MATLAB FFTs, a visible lag-one signed-tone estimator, a bounded
multi-peak extractor, and a private deterministic noise generator. It uses at
most 3,200 samples per leg, two multi-target components, seven sweep cases,
350,000 retained numeric values, and seven tagged figure groups. It writes no
file and starts no network request, timer, worker, or external process.

This is a first-order equal-magnitude-slope model. It treats delay and Doppler
as common across the adjacent legs and omits the turnaround transient,
within-pair range migration, acceleration, time scaling, multipath, leakage,
chirp nonlinearity, phase noise, antenna effects, ADC quantization, detection,
and calibrated power. Static tests and a standard-library numerical oracle do
not constitute MATLAB runtime, rendered-figure, RF, bench, hardware/HIL,
real-time, field, or operational-radar validation.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Use Up/Down Triangular Chirps to Separate Range and Velocity". The guiding question is: "How can opposite chirp slopes disentangle delay and Doppler?" Use this experiment: Generate alternating up- and down-chirps for one moving target and measure both beat frequencies. Have me perform these actions: Solve the two equations for range and Doppler. Sweep range, velocity, and noise, and include an incorrect pairing case with multiple targets. The main concept I must learn is: Opposite slopes provide independent combinations of delay and Doppler but create association challenges in multi-target scenes. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Files

- `README.md`
- `experiment.m`
- `lesson.md`
- `walkthrough.md`
- `checks.md`
