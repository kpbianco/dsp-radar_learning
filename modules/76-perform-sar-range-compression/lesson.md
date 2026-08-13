# Lesson: the product before azimuth focusing

## Guiding question

**What information is created before azimuth focusing begins?**

Range compression produces a complex matrix whose rows are aperture positions
and whose columns are slant-range samples. A point target becomes a narrow
range ridge, but its complex value still rotates along the aperture according
to path length. That matrix is a **range-compressed phase history**, not yet a
SAR image.

## Start with the physical signal

At platform position `x_p`, target `k` has slant range

```text
R_k(x_p) = sqrt(y_k^2 + (x_p - x_k)^2).
```

The module inserts one sampled LFM waveform `s[n]` at the corresponding
monostatic delay and gives it the narrowband two-way carrier phase

```text
d_k(x_p) = round((R_k(x_p) - R_gate) / Delta_R_sample)
phi_k(x_p) = phi_0,k - 4*pi*(R_k(x_p) - y_k)/lambda
x[p,n] = sum_k A_k s[n-d_k(x_p)] exp(j phi_k(x_p)) + w[p,n].
```

Here `Delta_R_sample = c/(2 Fs)`. Subtracting `y_k` from the phase removes one
target-constant rotation; it does not remove the phase variation across the
aperture. The `4*pi/lambda` factor is the monostatic round trip. The script
does not also encode carrier delay inside the baseband chirp, so carrier phase
is not counted twice.

## What range compression does

For every aperture row independently, the matched replica is

```text
h[n] = conj(s[N-1-n])
y[p,m] = sum_n x[p,n] h[m-n] / sum_n |s[n]|^2.
```

This is an explicit linear convolution, not a circular correlation or an
opaque toolbox object. The energy normalization keeps a single isolated
target's compressed peak in voltage units. Linear convolution adds `N-1`
samples of filter delay, which the displayed range axis explicitly removes.

The operation aligns the chirp samples from one delay. A long echo therefore
becomes a localized response. Its approximate range-resolution scale is

```text
Delta_R_resolution approximately c/(2B).
```

Do not confuse this with `c/(2 Fs)`: sample rate sets the displayed range-grid
spacing, while waveform bandwidth sets the physical ability to separate close
delays. The baseline has a 1.25 m grid and a 7.5 m nominal resolution scale.

## What survives compression

The matched filter acts down fast time and does not combine aperture rows.
Consequently, the target's complex peak is approximately

```text
y[p, target ridge] approximately A_k exp(j phi_k(x_p)) + filtered noise.
```

Two kinds of information coexist:

- ridge location gives sampled slant range at each aperture position;
- complex ridge phase records coherent path change across positions.

P77 can later test a cross-range hypothesis by compensating that phase and
adding aperture looks. A bright magnitude ridge alone cannot support that
coherent sum. P76 therefore measures agreement between the observed ridge
phasor and the expected two-way path phasor.

## Read the three cause-and-effect experiments

The bandwidth sweep holds duration, isolated-target delay, sample rate, and
all other scene assumptions fixed. Raising `B` from 10 to 40 MHz makes the
full -3 dB response width decrease and makes `c/(2B)` decrease. Pulse duration
stays fixed, so this is a bandwidth effect.

The spacing sweep holds the 20 MHz waveform and equal target amplitudes fixed.
At 3.75 m and 10 m, the pair does not create a valley below the weaker peak's
-3 dB level. At 15 m, the reviewed pair is separated. This is a resolution
statement, not an accuracy statement and not an azimuth result.

The broken case copies `abs(Y)`. Its magnitude map is exactly the same as the
complex map's magnitude, so all visible range ridges survive. But every
nonnegative sample has zero phase, destroying agreement with the expected
aperture phase. Recovery points back to the unchanged complex matrix and must
match it exactly.

## Limiting cases and model boundary

- As `B` decreases toward zero, compressed responses broaden and nearby
  targets merge even if the range grid is dense.
- Increasing `Fs` at fixed `B` samples the same physical response more finely;
  it does not by itself create finer range resolution.
- If target separation is far below `c/(2B)`, two returns behave like one
  composite response. Near the limit, phase and amplitude can change the exact
  valley, so the script binds only its reviewed equal-phase case.
- If aperture length shrinks to one position, range compression still works,
  but there is no aperture phase history available for cross-range focus.
- If complex phase is discarded, range localization survives and coherent
  azimuth focusing does not.
- If platform spacing is too large, adjacent phase changes can exceed `pi`
  radians and spatially alias. The reviewed limit is `0.90*pi`.
- Integer delays can differ from true slant range by half a range sample. This
  experiment keeps that quantization visible rather than claiming sub-sample
  accuracy.
- Rectangular LFM weighting produces sidelobes. They are responses of the
  waveform, not additional physical targets.
- Stop-and-go motion, stationary isotropic point targets, exact platform
  positions, narrowband carrier phase, no within-pulse Doppler, no clutter,
  and no propagation loss are assumptions. P78 owns range-cell migration,
  P79 owns SAR window/resolution tradeoffs, and P80 owns motion error.

## Dependencies and runtime boundary

P18 provides complex phase, P30 provides round-trip delay, P32 provides LFM
matched filtering, P37 provides radar-matrix orientation, and governed P75
provides SAR phase-history intuition. The experiment targets base MATLAB
R2016b or newer with no optional toolbox. Static checks and independent Python
oracles are not MATLAB runtime or rendered-figure evidence.
