# P61 walkthrough: Follow the Wavefront Across the Array

## Before running

The guiding question is: **How does a direction of arrival become a phase slope across sensors?**

Use the convention printed at the top of `experiment.m`: the ULA grows along
positive x, angle is measured from broadside, and a positive angle points
toward the positive-x end. Run the script from top to bottom once. It creates
five figures tagged `P61` and stores results in `p61_results`.

## 1. Baseline geometry and snapshot

Start with Figure 1. The upper plot is not a phase plot: it is geometric arrival
time relative to element zero. At `+30 deg`, later positive-x elements have
more-negative delay, meaning the wave reaches them earlier.

Now inspect I/Q versus element and the complex-plane path. Observe that return
magnitude stays near one while angle advances. Direction is encoded primarily
in relative channel phase, not in an amplitude ramp.

Expected baseline metrics:

```text
wavelength                         about 0.099931 m
adjacent geometric delay           -83.333 ps
ideal spatial slope                +1.570796 rad/element
estimated angle                    within 1 deg of +30 deg
```

## 2. From wrapped phase to angle

Move to Figure 2. The upper trace jumps at `+/-pi`; those are coordinate wraps,
not sudden changes in arrival direction. In the lower trace, compare the noisy
unwrapped samples, geometric model, and straight-line fit.

Follow this one processing transition:

```text
geometry -> channel delay -> carrier phase -> unwrapped spatial slope -> angle
```

The inverse is credible here because half-wavelength spacing keeps the baseline
step inside the unambiguous principal interval.

## 3. Sweep 1: change only arrival angle

In Figure 3, spacing remains `lambda/2` and frequency remains 3 GHz. The five
directions are `[-60 -30 0 30 60] deg`.

Observe three things:

1. broadside is flat;
2. changing angle sign changes slope sign;
3. slope follows sine, so its growth versus degrees is not perfectly linear.

Do not interpret the parallel-looking phase traces as different frequencies in
time. Each trace is one simultaneous snapshot sampled in space.

## 4. Sweep 2: separate spacing from frequency

Figure 4 contains two one-variable paths.

- Circles change physical spacing at fixed 3 GHz.
- Squares change frequency while holding the baseline physical spacing fixed.

Both paths visit `d/lambda = [0.25 0.375 0.5]` and produce the same phase
slopes. Their delay behavior differs: physical spacing changes arrival-time
difference, while carrier frequency changes phase accumulated over one fixed
time difference. This is the physical connection between path and phase.

## 5. Broken case: make the array spatially ambiguous

Figure 5 deliberately changes spacing to one wavelength. The true `+36.87 deg`
snapshot and the `-23.58 deg` alias lie exactly on top of each other. The naive
principal-step inverse reports the negative alias, more than 50 degrees from
truth.

This failure is not noise, a poor fit, or a plotting problem. It is missing
information: the sampled spatial phases differ by one complete cycle per
element. Unwrapping cannot know which cycle count was present between sensors.

## 6. Recovery

The recovery keeps source angle, frequency, element count, and initial phase
unchanged and returns spacing to `lambda/2`. The step becomes `0.6 pi`, and the
reported angle returns to `+36.87 deg`.

To recover after interruption, close only P61 figures if desired:

```matlab
close(findall(0, 'Type', 'figure', 'Tag', 'P61'))
```

Then rerun from the top. The private seed reconstructs the baseline snapshot;
there is no checkpoint or partial output to resume. All loops and arrays are
validated against fixed ceilings, so no background task continues after
Ctrl+C.

## Expected observations

- Positive broadside-referenced angle produces positive spatial phase slope
  under the stated sign convention.
- The baseline fit is close to, but not exactly, the ideal line because its
  noise is deterministic and nonzero.
- Spacing and carrier frequency scale phase through `d/lambda`.
- Frequency does not change geometric delay when the physical array is fixed.
- Two different angles can create exactly the same snapshot after spatial
  aliasing.
- Safe spacing restores the angle without changing the source.

## Common interpretation corrections

- If you say later sensors receive a larger positive delay, revisit the delay
  sign: for this positive angle they receive an advance.
- If you say the baseline has a monostatic factor of two, remove it; the array
  path difference is one way.
- If you say more sensors always remove aliases, distinguish fit variance from
  sampling ambiguity.
- If you say `unwrap` recovered truth in the broken case, compare the two
  identical complex snapshots: no algorithm can distinguish them without
  additional information.

## Completion connection

For an unambiguous array, infer direction by measuring the phase slope, dividing
out `2*pi*d/lambda`, and applying inverse sine under the declared angle/sign
convention. Then explain why that same inverse is not unique after the spatial
step can cross a full-cycle branch.
