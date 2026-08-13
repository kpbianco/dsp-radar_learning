# Lesson: the target stays put while its delay walks

## Guiding question

Why does a target move through range bins during a long synthetic aperture?

## Physical mental model

Imagine a fixed reflector and a radar sliding along a rail. The reflector does
not change ground coordinates, but the tape-measure distance from radar to
reflector changes at every rail position. Radar stores that distance as
round-trip delay. After range compression, each aperture row has a localized
echo at the current delay, so stacking the rows draws a curved ridge.

For platform cross-range position `x_p` and a target at `(x_t,y_t)`, the exact
monostatic slant range is

```text
R(x_p) = sqrt((x_p-x_t)^2 + y_t^2),       tau(x_p) = 2 R(x_p)/c.
```

The square root is the cause of the curve. A constant reference range changes
the label but not the variation:

```text
DeltaR(x_p) = R(x_p) - R_ref.
```

In the baseline, `R` changes by about `33.25 m`. That is `66.5` stored samples
on a `0.5 m` range grid, but about `16.6` physical resolution cells for the
`2 m` compressed response. These numbers answer different questions:

- sampling bins say how densely the range axis is stored;
- resolution cells say whether two physical ranges could be separated.

Changing sample spacing alone could change the first count without changing
the migration in metres or the waveform's resolution.

## What is in one range-compressed sample

The synthetic target response in aperture row `p` is

```text
s_p(r) = A g(r-R_p) exp[-j 4*pi*(R_p-R_0)/lambda] + n_p(r),
```

where `g` is an explicitly generated sinc-like compressed response, `R_p` is
the exact slant range, and `n_p` is private seeded complex noise. The factor
`4*pi/lambda` is two-way carrier phase: distance changes the outgoing and
return paths.

The magnitude term `g(r-R_p)` decides which range columns contain target
energy. The complex exponential decides how aperture looks rotate in phase.
These are separate problems. Applying perfect phase compensation to a fixed
range column cannot restore target samples that migrated into other columns.

## The correction is a change of sampling coordinate

Choose the center-look range as `R_ref`. For each aperture row, sample the
original data at an offset input coordinate:

```text
y_p(r) = s_p(r + DeltaR_p).
```

If the output coordinate is `r = R_ref`, the requested input is
`R_ref + DeltaR_p = R_p`, exactly where the target lies. Because that requested
range is usually between stored samples, the experiment exposes linear
interpolation rather than calling an opaque resampler:

```text
q = (r_requested-r_min)/Delta_r + 1
k = floor(q)
alpha = q-k
y = (1-alpha) s[k] + alpha s[k+1].
```

This row shift aligns magnitude, but coherent focusing still needs the complex
two-way phase compensation

```text
exp[+j 4*pi*(R_p-R_0)/lambda].
```

The fixed-bin and corrected profiles in the experiment both receive this same
phase term. Their difference isolates range migration: corrected processing
samples the curved ridge; fixed-bin processing stays in one column.

## From one aligned ridge to an image

The known-path row shift aligns this one reference target. A scene contains
many candidate positions, each with a different `R_p`. The image comparison
therefore evaluates each candidate pixel explicitly:

1. predict its slant range at every platform position;
2. either sample a single center-look range (fixed-bin assumption) or linearly
   sample the changing predicted range (path following);
3. apply the same predicted two-way phase compensation;
4. add the aperture looks coherently.

The path-following form is backprojection. P77 introduced it as a focusing
operation; P78 shows why following range is essential when the aperture is
long enough for the ridge to cross many cells.

## Why the two sweeps behave as they do

### Aperture length

The `100`, `200`, and `400 m` cases keep target, carrier, range grid, and
platform spacing fixed. Longer travel samples more extreme viewing distances,
so the range span grows. A very short aperture can keep migration below one
resolution cell; a long aperture cannot safely use a fixed-bin approximation.

### Squint offset

The `0`, `60`, and `80 m` cases keep the full aperture fixed and move only the
target's along-track offset. Broadside geometry has a symmetric range curve.
Squint makes the curve asymmetric around the center look and increases the
reviewed range span. Squint does not mean the stationary target moved during
collection.

## The deliberately wrong sign

The correct mapping samples `r + DeltaR_p`. The broken mapping samples
`r - DeltaR_p`. A target originally at `R_ref + DeltaR_p` then appears near
`R_ref + 2 DeltaR_p`: the mapping roughly doubles the relative motion instead
of removing it. The failure is diagnostic, not random.

Recovery does not invert or repair the already shifted matrix. It reruns the
correct interpolation from the byte-for-byte retained complex range history.
That makes rollback exact and avoids compounding interpolation loss.

## Limiting cases

- **Zero aperture:** one look has no aperture migration.
- **Very short aperture or coarse resolution:** migration may remain below one
  resolution cell, so a fixed-bin approximation can be adequate.
- **Closest approach:** `dR/dx_p = 0` at one point, but total migration over a
  finite aperture is generally not zero.
- **Target at broadside:** the curve is symmetric, not flat.
- **Dense range sampling:** more stored bins do not imply finer physical range
  resolution.
- **Correct magnitude alignment without I/Q:** the ridge can look straight,
  but coherent aperture focus is unavailable after phase is discarded.
- **One known correction path:** it aligns one reference target; a wide scene
  needs pixel-dependent interpolation/backprojection.
- **Constant range bias:** it shifts the reference coordinate but does not
  remove the path-dependent variation.
- **Unknown geometry or motion:** this module's exact correction no longer
  applies directly; P80 treats motion error and autofocus.

## Common interpretation mistakes

- “The target walks across the ground.” No: the measured slant delay walks.
- “Phase compensation alone fixes migration.” No: it cannot recover energy
  absent from the chosen range column.
- “A range bin is always a resolution cell.” No: stored spacing and physical
  resolution are distinct.
- “Subtracting `R_ref` removes migration.” No: it removes only a constant.
- “The parabola is the data model.” No: the script uses exact square-root
  range; a parabolic form is only a local approximation.
- “Any interpolation direction is just a display choice.” No: the sign decides
  whether the ridge aligns or its motion doubles.
- “A straightened magnitude ridge is a finished SAR image.” No: complex phase
  must also be preserved and focused.

## Declared runtime and bounds

The experiment targets base MATLAB R2016b or newer and uses no optional
toolbox, files, network, timers, workers, or background tasks. It bounds the
aperture, range, image, sweeps, private noise, interpolation operations, image
operations, total operations, live workspace, and six tagged figure groups
before claiming completion. These constraints make the synthetic lesson
repeatable; they do not provide hardware, real-time, field, or operational
radar validation.
