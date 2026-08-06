# P65: Use MVDR/Capon Adaptive Beamforming

**Phase 7: Arrays, Beamforming, DOA, and STAP**  
**Status:** Implemented by batch `P65`

## Guiding question

How can a beamformer place data-dependent nulls on interference?

## Experiment

Observe a weak desired source and a much stronger independent interferer on an
eight-element half-wavelength ULA. Form the sample covariance explicitly,
solve the diagonally loaded MVDR/Capon system, normalize the result to preserve
the chosen look direction, and compare its pattern and output SINR with a
conventional fixed beamformer.

## Procedure

Run one deterministic baseline and then change one physical control at a time:

1. inspect the array covariance and its eigenvalue spread;
2. compare conventional and MVDR patterns, interference response, white-noise
   gain, and analytical output SINR;
3. sweep snapshot count using prefixes of one unchanged 256-snapshot record;
4. sweep diagonal loading under a fixed three-degree steering mismatch; and
5. observe self-nulling with too little loading, then recover first by loading
   and finally by correcting the assumed steering vector on the same data.

No phased-array toolbox call hides steering vectors, covariance estimation,
the constrained normalization, or output-power accounting.

## What this should teach

MVDR minimizes measured output power while enforcing unit response in one
assumed direction. The covariance lets the weights place a narrow null where
the data contain strong interference. Finite snapshots, ill-conditioning, and
steering mismatch can make that adaptivity fragile; diagonal loading trades
some ideal null depth for better numerical and model robustness.

## Completion condition

The deterministic baseline places a deeper null near the interferer and
improves output SINR over conventional beamforming, and you can explain why
the sample-starved mismatched case self-nulls the desired source and why
loading improves robustness without correcting the underlying steering model.

## Run the lesson

```bash
./bin/learn start 65
```

In MATLAB, run `experiment`, follow `walkthrough.md` one observation at a time,
and use `checks.md` before giving the short teach-back.

## Dependencies and compatibility

P61 supplies the broadside-referenced ULA phase convention, P62 supplies array
pattern and grating-lobe intuition, P63 supplies the explicit conjugate receive
sum, and P64 distinguishes a fixed comparator from the data-adaptive weights
used here. P66 will reuse covariance structure for MUSIC DOA estimation, while
P67 will broaden the steering mismatch into calibration and coupling errors.

The experiment uses base MATLAB arithmetic and script-local functions, so it
requires MATLAB R2016b or newer and no optional toolbox. Elements, snapshots,
scan samples, sweep cases, private deterministic samples, working arrays, and
figures have immutable ceilings. It writes no file and starts no network,
timer, worker, or external process.

This is a narrowband, far-field, complex-baseband ULA model with independent
constant-modulus sources and spatially white receiver noise. It omits element
patterns, coupling, multipath, broadband effects, near-field curvature,
nonstationarity, covariance training contamination beyond the shown desired
signal, automatic loading selection, calibration estimation, detection, and
tracking. Static checks and an independent Python oracle do not constitute
MATLAB runtime, rendered-figure, antenna, hardware/HIL, real-time, field, or
operational-radar validation.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Use MVDR/Capon Adaptive Beamforming". The guiding question is: "How can a beamformer place data-dependent nulls on interference?" Use this experiment: Simulate a weak desired source, strong interferer, and finite snapshots on a ULA. Have me perform these actions: Estimate covariance, form MVDR weights, and compare patterns/output SINR with conventional beamforming. Sweep snapshot count and diagonal loading. The main concept I must learn is: MVDR minimizes output power while preserving a chosen direction, but covariance errors can make it unstable. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Files

- `README.md`
- `experiment.m`
- `lesson.md`
- `walkthrough.md`
- `checks.md`
