# P62 walkthrough: Watch the Aperture Add and Cancel

The guiding question is: **How do aperture size and element spacing shape a beam pattern?**

Run `experiment.m` from top to bottom once. It closes only old figures tagged
`P62`, creates five new tagged figures, prints the baseline and recovery
metrics, and retains exact arrays and structures in `p62_results`.

## 1. Baseline: read one beam in linear and dB units

Begin with Figure 1. The upper panel shows the normalized magnitude made by
adding eight explicit complex element contributions. At broadside, steering
removes every phase difference and the magnitude reaches one.

Follow one physical transition:

```text
direction -> residual phase at each element -> complex sum -> beam pattern
```

The two black circles mark amplitude `1/sqrt(2)`, so their separation is the
full half-power beamwidth. The red crosses mark the first nulls. The dB panel
makes sidelobes visible without changing the underlying linear data.

Expected baseline observations:

```text
element count                         8
spacing                               0.50 lambda
physical aperture                     3.50 lambda
peak angle                            about 0 deg
half-power beamwidth                  about 12.803 deg
first-null beamwidth                  about 28.950 deg
peak sidelobe level                   about -12.797 dB
```

## 2. Sweep 1: increase only element count

In Figure 2, all cases keep `d=lambda/2`, broadside steering, and uniform
weights. Only `M` changes through `[4 8 16]`, so the filled physical aperture
grows through `[1.5 3.5 7.5] lambda`.

Observe the local main lobe before comparing the far sidelobes. HPBW falls
from roughly `26.32` to `12.80` to `6.36 deg`. The main result is aperture
resolution: a larger path difference develops across the array for the same
angular offset, causing cancellation closer to the steering direction.

Do not conclude that the larger uniform array eliminates sidelobes. Its first
sidelobe remains near the usual uniform-aperture level.

## 3. Sweep 2: increase only spacing

Figure 3 keeps eight elements, broadside steering, and uniform weights while
spacing changes through `[0.5 0.75 1.0] lambda`. The local main lobe narrows as
spacing grows because the physical aperture grows.

Now inspect the full visible interval, not just the central lobe. At one
wavelength, equal-height copies appear at the `+/-90 deg` boundaries. The
`0.75 lambda` broadside case has no equal-height copy in this interval. Use the
condition

```text
sin(theta_g) = sin(theta_0) + k/(d/lambda)
```

instead of repeating “anything above half wavelength always has a grating
lobe.” Half wavelength is the full-scan guarantee; the actual alias depends on
steering and the visible sector.

## 4. Compare uniform and tapered weights

Figure 4 changes only the weights. The upper panel compares dB patterns; the
lower panel shows exactly which element contributions changed.

The Hamming taper reduces edge-element weight, lowers the peak sidelobe by more
than `15 dB`, and widens HPBW by more than `5 deg`. The taper is not free gain:
it trades effective aperture for lower sidelobe response.

## 5. Broken case: optimize the local width and miss an alias

Figure 5 deliberately steers to `+30 deg` and sets `d=lambda`. The upper panel
has two `0 dB` peaks: the intended `+30 deg` direction and a false `-30 deg`
direction. Their sampled steering vectors are identical because their phase
increments differ by exactly one full cycle per element.

This is not an ordinary `-13 dB` sidelobe, plotting interpolation, or numerical
noise. A source at either marked direction receives the same coherent gain.
Tapering both directions with the same weights would preserve their equality.

## 6. Recovery

The lower panel changes only spacing back to `lambda/2`. It preserves the
intended `+30 deg` peak and makes the old `-30 deg` direction cancel. The
analytic grating-angle enumeration also becomes empty over the visible region.

The recovery is a spatial-sampling repair. It does not change the true angle,
element count, weights, scan grid, or answer after observing the output.

## Expected observations

- Coherent broadside addition normalizes to one.
- A larger filled aperture produces a narrower local main lobe.
- Uniform weighting retains finite-aperture sidelobes as element count grows.
- Larger spacing can create an equal-height copy even while the local beam
  looks narrower.
- Hamming taper lowers sidelobes and widens the main lobe.
- Half-wavelength recovery removes the exact off-broadside spatial alias.

## Common interpretation corrections

- If you call the half-power crossing `AF=0.5`, replace it with
  `AF=1/sqrt(2)`.
- If you call the uniform first sidelobe a grating lobe, compare its `-12.8 dB`
  height with the broken case's exact `0 dB` copy.
- If you claim `d=0.75 lambda` must alias at broadside, evaluate the integer
  grating equation over `sin(theta)` in `[-1,1]`.
- If you say taper fixed the broken case, compare the identical sampled phase
  vectors; fixed weights cannot distinguish them.
- If you say more elements create uniqueness, separate main-lobe width from
  spatial sampling.

## Cancellation, timeout, and clean recovery

All loops are finite and validated before figures are built. The experiment
uses no workers, timers, network, external process, or file writes. After
Ctrl+C there is no background task, checkpoint, or partial output to resume.
Close only this lesson's figures if desired:

```matlab
close(findall(0, 'Type', 'figure', 'Tag', 'P62'))
```

Then rerun from the top. The private seed reconstructs the same off-grid probe
angles without changing MATLAB's global random stream. The reviewed ceilings
are 32 elements, 10,001 angle samples, five cases per sweep, eight probe
angles, 250,000 retained numeric values, and five figures.

## Concept connection and completion handoff

P61 encoded direction as spatial phase. P62 shows what happens when those
phases are coherently added. P63 will use the same steering alignment on array
data rather than only an ideal response curve.

Before completion, explain how aperture controls beamwidth, how the integer
direction-cosine equation predicts a grating lobe, and why a taper trades
sidelobe height for resolution without repairing spatial aliasing.
