# P36 checks: Measure Doppler from Pulse-to-Pulse Phase

Guiding question: **How does target velocity create coherent phase progression across pulses?**

Use the figures and printed metrics. These checks test physical interpretation,
not MATLAB syntax.

## Observation checks

1. Which direction does the baseline I/Q phasor rotate under the stated sign
   convention?
2. What ideal Doppler, phase increment, FFT-bin spacing, and unambiguous
   Doppler interval are printed?
3. Why can the phase-based estimate be near `1000.69 Hz` while the FFT peak is
   on the `1000 Hz` bin?

Passing observation: you identify counterclockwise positive rotation, about
`1000.69 Hz`, `1.572 rad/pulse`, `125 Hz/bin`, `[-2000, 2000) Hz`, and
finite FFT-grid quantization.

## Prediction checks

1. If velocity changes from `+15` to `-15 m/s`, what happens to echo magnitude,
   phase slope, and FFT-peak sign?
2. At fixed velocity and PRF, what happens to phase increment when carrier
   frequency doubles?
3. At fixed PRF, what happens to Doppler-bin spacing and unambiguous interval
   when pulse count doubles?
4. What phase progression and Doppler should a stationary ideal target have?

Passing prediction: magnitude is unchanged ideally while rotation reverses;
phase increment doubles with carrier; bin spacing halves but the interval does
not change with pulse count; and a stationary target has flat phase at zero
Doppler.

## Interpretation checks

1. Explain the factor of two in `f_d = 2 v_r/lambda`.
2. Connect `angle(conj(x[p]) x[p+1])` to Doppler frequency and velocity.
3. Distinguish velocity-bin spacing from velocity-estimator accuracy.
4. Why are Dopplers separated by an integer multiple of PRF indistinguishable?
5. Why cannot magnitude-only slow time distinguish approach from recession?

Passing interpretation: you mention two-way path change, phase change per PRI,
finite-grid reporting, modulo-`2*pi` sampling, and loss of complex angle.

## Failure and recovery checks

1. Did the broken target physically stop when its spectrum moved to zero?
2. What exact information did `abs(received_echo)` discard?
3. What state and operation does recovery restore?
4. Why does unwrapping sampled phase not repair a Doppler already aliased past
   `PRF/2`?

Passing recovery: you reject the false stationary interpretation, identify
complex phase and sign as lost, restore coherent samples plus the private-seed
noise exactly, and explain that missing inter-pulse cycle count was never
sampled. A clean rerun reproduces the result. If needed, cancel with Ctrl+C;
there is no worker, timer, network request, hardware session, file write, or
external transaction to clean up, and only figures tagged `P36` are closed.

## Compatibility, isolation, and resource checks

- Confirm all controls are finite before arrays are allocated.
- Confirm at most 128 pulses, 7 cases per sweep, 6 figure groups, and 50,000
  estimated stored numeric values.
- Confirm the base MATLAB path exposes the equations, adjacent products,
  phase slope, window, FFT, axes, and velocity conversion.
- Confirm no toolbox radar object, background worker, global RNG mutation, or
  `.learning/` write is used.
- Confirm this synthetic one-bin experiment is not hardware, HIL, field,
  real-time, detector, deployment, or operational-radar evidence.

## Completion checklist

- [ ] I can state the positive-approaching sign convention.
- [ ] I can calculate wavelength, Doppler, and phase increment per pulse.
- [ ] I can infer signed velocity from phase progression or FFT location.
- [ ] I can explain why more pulses narrow bins but do not widen ambiguity.
- [ ] I can predict how carrier frequency changes phase sensitivity.
- [ ] I can diagnose the magnitude-only failure and recover coherent phase.

## Short teach-back rubric

Give two or three sentences containing all three ideas:

1. Monostatic radial motion gives `f_d=2v_r/lambda`, and coherent sampling once
   per PRI turns that into `Delta_phi=2*pi*f_d/PRF`.
2. Phase direction and FFT side encode the velocity sign, while pulse count
   controls bin spacing.
3. Phase is sampled modulo `2*pi`, so the PRF limits unambiguous Doppler and
   magnitude-only processing cannot restore discarded sign.

Completion means you can predict phase increment per pulse and velocity from the Doppler-bin location. Personal completion is recorded only after this teach-back through the learner CLI under ignored `.learning/` state.
