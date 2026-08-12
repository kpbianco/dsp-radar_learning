# P68: Build an Introductory STAP Clutter-Ridge Experiment

**Phase 7: Arrays, Beamforming, DOA, and STAP**  
**Status:** Implemented by batch `P68`

## Guiding question

How can space and slow time be processed together to suppress moving-platform clutter?

## Experiment

Build an eight-element by eight-pulse space-time snapshot. Sixty-one ground
patches form a deterministic angle-Doppler clutter ridge, while one weak moving
target sits off that ridge even though its angle and Doppler each overlap a
clutter marginal. Use independent range cells to estimate covariance without
putting the target into clean training.

The script exposes space-time steering, a fixed matched weight, separate
spatial and slow-time loaded-MVDR weights, the full joint covariance, and a
joint loaded-MVDR weight. It compares response maps and analytical output SCNR
on the same physical model.

## Procedure

1. Inspect the angle-Doppler power map and its tilted clutter ridge.
2. Inspect the 64-by-64 covariance and eigenvalue spread.
3. Compare fixed, separable, and joint response surfaces and output SCNR.
4. Sweep clean training support using prefixes of one unchanged 128-cell record.
5. Sweep target-like contamination on that same record.
6. Observe the contaminated, slightly mismatched broken case, then recover by
   restoring target-free training without changing the cell under test.

All steering, covariance, loading, constrained solves, response maps, and
power accounting are explicit base-MATLAB operations.

## What this should teach

Moving-platform ground clutter is not merely near zero Doppler. Its angle and
Doppler are coupled, so many patches trace a ridge. A separable spatial/Doppler
product is restricted to a rectangular response. Joint space-time weights can
place low response along the coupled ridge while preserving an off-ridge target.

Adaptive performance depends on covariance evidence. Too few independent
training cells poorly support a 64-dimensional estimate. Target-like training
contamination is especially dangerous when the protected steering model is
slightly wrong: the covariance can suppress part of the actual target while
the constraint still preserves the assumed vector.

## Completion condition

The joint filter improves target-to-clutter-plus-noise ratio over the separate
spatial/Doppler filter, and you can identify degradation from insufficient or
contaminated training data.

## Run the lesson

```bash
./bin/learn start 68
```

In MATLAB, run `experiment`, follow `walkthrough.md` one observation at a time,
and use `checks.md` before giving the short teach-back.

## Dependencies and compatibility

P37 supplies the element-by-pulse layout, P41 clutter intuition, P42 slow-time
Doppler processing, P61/P63 the positive broadside-referenced receive steering
convention, P65 the loaded MVDR constraint, and P67 the lesson that an adaptive
constraint protects an assumed signature rather than an imperfect physical one.

The script requires MATLAB R2016b or newer and no optional toolbox. It uses
private deterministic generators, bounded arrays, script-local functions, and
six tagged figure groups. It writes no file and starts no network request,
timer, worker, or external process.

This is a narrowband, far-field, side-looking teaching model with an ideal ULA,
independent Gaussian patch reflectivities across training range cells, one CPI,
and no range migration. The ridge law is
`nu_c = 2 v_p sin(theta)/(lambda PRF)`; it is illustrative rather than a
terrain, antenna-pattern, internal-clutter-motion, or measured-data model.
Static checks and the deterministic Python oracle do not constitute MATLAB
runtime, rendered-figure, antenna, bench, hardware/HIL, real-time, field, or
operational-radar validation.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Build an Introductory STAP Clutter-Ridge Experiment". The guiding question is: "How can space and slow time be processed together to suppress moving-platform clutter?" Use this experiment: Create a small space-time data cube with clutter occupying an angle-Doppler ridge, one moving target, and thermal noise. Have me perform these actions: Visualize angle-Doppler power, form a space-time covariance, compare separate spatial/Doppler filtering with a joint adaptive weight, and vary training support. The main concept I must learn is: STAP exploits joint spatial and Doppler structure to suppress clutter that overlaps the target in either dimension alone. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Files

- `README.md`
- `experiment.m`
- `lesson.md`
- `walkthrough.md`
- `checks.md`
