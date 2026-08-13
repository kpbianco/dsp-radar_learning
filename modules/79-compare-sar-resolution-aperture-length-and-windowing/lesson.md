# P79 lesson: A SAR Point Has Two Widths and Many Sidelobes

The guiding question is: **What controls range and cross-range resolution and sidelobes?**

A focused SAR image does not draw an ideal point target as one mathematical
pixel. A finite waveform bandwidth spreads it in range, and a finite synthetic
aperture spreads it in cross-range. Abruptly ending either coherent record also
creates sidelobes. P79 separates these effects so one control changes at a
time.

## The local point-spread model

The small image is a local broadside model around `R0 = 1000 m`. It is
separable on purpose:

```text
h(Delta x, Delta R) = h_x(Delta x) h_R(Delta R).
```

This lets us identify which axis a design choice controls. It is not a
replacement for P77's full backprojection or P78's migration correction. A
wide scene, squint, large fractional bandwidth, or uncompensated migration
couples the dimensions and needs the fuller geometry.

Metrics are measured on an isolated point response before several targets are
added to the teaching image. Interference between nearby targets must not be
mistaken for the width or sidelobe level of one isolated response.

## Range: coherent frequency diversity

Let `f_n` be baseband frequency samples spanning bandwidth `B`. A range
hypothesis displaced by `Delta R` has round-trip delay error
`Delta tau = 2 Delta R/c`. Its normalized focused response is the explicit sum

```text
h_R(Delta R) = (1/N_f) sum_n exp(j 4 pi f_n Delta R/c).
```

At the correct range every term aligns. Away from it, phase turns across the
band and the terms cancel. For nearly continuous uniform bandwidth, the first
null is at

```text
Delta R_null = c/(2B).
```

That one-sided first-null distance is the nominal Rayleigh range resolution.
The experiment also reports full half-power width, which is about `0.886`
times this value for a uniform spectrum. These are related metrics, not
interchangeable definitions.

For the `200 MHz` baseline, `c/(2B) = 0.75 m`. Sweeping `100`, `200`, and
`400 MHz` makes the measured range width decrease almost exactly as `1/B`.
Carrier frequency, aperture, scene, image grid, and weighting remain fixed.

The frequency samples are a transparent finite approximation to a continuous
band. Their spacing would eventually repeat the response at a distant delay;
the plotted range interval stays well inside that artificial ambiguity.

## Cross-range: coherent angular diversity

For platform position `x_p`, a target at `(x_t,R0)` has exact slant range

```text
R_t(x_p) = sqrt((x_p-x_t)^2 + R0^2).
```

Focusing a candidate `x` compensates its predicted path. The residual
two-way phase and normalized coherent sum are

```text
Delta phi_p(x) = (4 pi/lambda) [R_x(x_p)-R_t(x_p)],
h_x(x) = sum_p w_p exp(j Delta phi_p(x)) / sum_p w_p.
```

The script evaluates this exact square-root expression; it does not call a SAR
processor. Near broadside with `L << R0`, the first-null scale is

```text
Delta x_null approximately lambda R0/(2L).
```

Thus a longer aperture sees more angle and narrows cross-range response. A
higher carrier frequency also helps by shortening `lambda`, and greater range
worsens cross-range resolution for a fixed physical aperture. The `10 GHz`,
`30 m`, `1000 m` baseline predicts `0.50 m`. Sweeping `L = 10`, `20`, and
`30 m` changes only the aperture and makes width fall approximately as `1/L`.

Use `L=(N-1)d`, the distance between the first and last platform positions,
not `Nd`.

## Sidelobes and aperture windowing

Uniform aperture weights end abruptly. That hard edge gives the narrowest
uniform mainlobe for this fixed track but a peak sidelobe near `-13.3 dB`.
P79 constructs Hamming weights directly:

```text
w_p = 0.54 - 0.46 cos(2 pi p/(N-1)).
```

Smaller edge weights smooth the finite aperture. The normalized Hamming
response has a much lower peak sidelobe, around `-42.6 dB` in the reviewed
grid, but its half-power mainlobe is roughly `1.48` times wider. The displayed
responses are normalized so shape is easy to compare. Before normalization,
the Hamming coherent peak is lower because less total weight is collected;
normalizing a plot does not restore signal-to-noise ratio.

The same principle can be applied across transmitted frequency, which trades
range sidelobes for range width. This experiment holds frequency weights
uniform and changes aperture weights so the affected dimension is unambiguous.

## Why sparse platform sampling creates false targets

Keeping the same `30 m` endpoints but changing platform spacing from `0.25 m`
to `5 m` leaves only seven looks. In the broadside approximation, candidate
directions repeat when the two-way phase advance between looks differs by an
integer turn:

```text
Delta sin(theta) = k lambda/(2d),
Delta x_alias approximately k lambda R0/(2d).
```

The factor `2` belongs to monostatic two-way phase. P62's receive-array alias
formula is one-way and must not be copied without this change. With
`lambda=0.03 m`, `R0=1000 m`, and `d=5 m`, false copies appear about `3 m`
apart. The exact square-root sum makes the replicas nearly, though not
perfectly, equal over this local scene.

Adding display pixels only samples the already aliased response more finely.
A fixed taper cannot distinguish two directions that produce the same sampled
phase history. Recovery must return to adequately dense platform measurements;
the script freshly refocuses the byte-for-byte unchanged synthetic scene with
`0.25 m` spacing.

## What each metric means

- **Nominal resolution:** the one-sided first-null/Rayleigh scale `c/(2B)` or
  `lambda R0/(2L)`.
- **Half-power width:** full distance between magnitude `1/sqrt(2)` crossings,
  equivalent to `-3.0103 dB` power points.
- **First-null width:** full distance between the nearest minima; it is about
  twice the nominal one-sided resolution.
- **Peak sidelobe level (PSL):** largest magnitude outside those first minima,
  relative to the main peak using `20 log10`.
- **Display spacing:** distance between plotted pixels. It affects how smoothly
  a response is drawn, not the information collected.

Metrics use unclipped linear magnitude. The `-50 dB` floor is applied only for
display, so clipping cannot invent a sidelobe number.

## Limiting cases

- `B -> 0`: frequency samples carry no delay diversity, so range response
  becomes broad and range discrimination disappears.
- Larger `B`: range mainlobe narrows until unmodeled waveform, sampling, or
  propagation limits matter; aperture geometry does not set this ideal scale.
- `L -> 0`: repeated looks from one position add amplitude but supply no
  cross-range discrimination.
- Larger `L`: cross-range narrows, but P78's range migration and P80's motion
  accuracy become increasingly important.
- Larger `R0` at fixed `L`: the observed angular span shrinks, so physical
  cross-range resolution worsens.
- Shorter `lambda`: cross-range resolution improves for fixed geometry, but
  phase becomes more sensitive to position error.
- Stronger taper: sidelobes fall while effective aperture and coherent SNR
  decrease; the response cannot become both arbitrarily narrow and sidelobe
  free.
- Sparse `d`: grating-lobe-like replicas enter the scene even though the local
  peak may look narrow.
- Denser output grid: reported curves become smoother, but physical widths and
  aliases remain.

## Common interpretation mistakes

- Saying bandwidth improves both axes ignores the independent aperture phase
  record in this local model.
- Saying aperture length improves range confuses fast-time bandwidth with
  slow-space angle diversity.
- Calling half-power width, full first-null width, and Rayleigh separation the
  same number creates a factor-of-two or `0.886` error.
- Using `c/B` for monostatic range forgets the round trip; nominal range
  resolution is `c/(2B)`.
- Using `lambda/d` for this monostatic sampling failure forgets its two-way
  phase; the local alias interval is `lambda R0/(2d)`.
- Calling lower sidelobes better resolution ignores the wider tapered
  mainlobe and coherent loss.
- Measuring a multi-target composite instead of an isolated PSF makes target
  phase and interference contaminate the metric.
- Calling a finer plot a recovery confuses interpolation with new
  measurements.

## Dependencies, compatibility, and claim boundary

P12/P33 supply leakage and taper intuition; P30-P32 supply delay, range
resolution, and pulse compression; P61-P63 supply aperture sampling; P75-P78
supply phase history, range compression, focusing, and migration correction.
The experiment uses base MATLAB, explicit complex sums, bounded foreground
loops, and a private deterministic generator that does not alter global random
state. It requires script-local functions (MATLAB R2016b or newer).

It writes no file and uses no network, timer, worker, GPU, process, checkpoint,
or persistent state. Static checks and an independent Python oracle cannot
prove MATLAB parsing, rendering, performance, educational effectiveness,
hardware/HIL, bench, real-time, field, operational radar, deployment, or
production behavior.
