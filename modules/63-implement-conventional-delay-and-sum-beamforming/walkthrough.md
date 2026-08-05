# P63 walkthrough: Align the Right Spatial Phase

The guiding question is: **How does steering align one direction and misalign others?**

Run `experiment.m` from top to bottom once. It closes only old figures tagged
`P63`, creates five new tagged figures, prints baseline and recovery metrics,
and retains exact arrays and structures in `p63_results`.

## 1. Baseline: follow data through the fixed beamformer

Start with Figure 1. The upper panel is the magnitude of the complex sensor
matrix `X`: eight rows are sensors and 128 columns are simultaneous snapshots.
The sources are not supposed to look like two angles in this panel. Direction
is encoded in phase relationships across rows.

Follow one transition at a time:

```text
source angle -> sensor phase slope -> conjugate steering -> channel sum
             -> output magnitude squared -> snapshot average
```

The lower panel compares one output snapshot with the 128-snapshot power
average. Both use the same fixed bank of scan weights. The averaged curve
should peak near `-20` and `+25 deg`; the one-look curve is rougher and its
relative peak heights are less representative.

Expected baseline observations:

```text
elements                              8
spacing                               0.50 lambda
physical aperture                     3.50 lambda
true source angles                    -20 and +25 deg
nominal per-source input SNR          +10 dB per sensor
snapshots                             128
averaged peak errors                  less than 0.5 deg
direct versus covariance power        agreement within 1e-10
```

## 2. Inspect alignment before reading more scan curves

Figure 2 isolates the `-20 deg` source without sensor noise. Steering to that
same direction removes its spatial slope: all residual contribution phases are
zero, and the cumulative normalized magnitude reaches exactly one.

Steering the same arrival to `0 deg` leaves a residual phase step. The phasors
wind as elements are added, so the cumulative magnitude rises and falls and
ends below `0.25`. This is the mechanism behind every curve in the lesson.

## 3. Sweep 1: separate scene spacing from array resolution

Figure 3A keeps `M=8`, half-wavelength spacing, SNR, and 128 snapshots fixed.
Only symmetric source separation changes through `[6 12 24] deg`.

- At `6 deg`, the two responses merge into one maximum.
- At `12 deg`, the result is still biased inward and not two trustworthy
  angle estimates for this aperture.
- At `24 deg`, distinct peaks appear near both sources.

Figure 3B keeps the source pair fixed at `-8` and `+8 deg`. Only array size
changes through `[4 8 16]`. Four elements span `1.5 lambda` and merge the pair.
Eight span `3.5 lambda` and resolve it; sixteen span `7.5 lambda` and sharpen
both lobes further.

Do not interpret the normalized height as receiver gain. Each curve is
normalized only for shape comparison.

## 4. Sweep 2: separate SNR from snapshot averaging

Figure 4A changes only nominal input SNR through `[-15 0 15] dB` at 128
snapshots. The low-SNR curve has the highest relative off-source floor. The
array and its main-lobe width did not change.

Figure 4B holds the `0 dB` data model fixed and uses prefixes of one record:
`[1 8 128]` snapshots. A single look contains strong random cross-terms. More
looks reduce background ripple because independent phases and noise cancel in
the average.

Covariance averaging estimates the existing spatial response more reliably.
It does not create aperture, reduce the P62 array-factor beamwidth, or guarantee
resolution of coherent sources.

## 5. Broken case: reverse the steering phase sign

Figure 5A uses unchanged data with sources at `-20` and `+30 deg`, but builds
the scan steering vectors with the opposite phase convention before applying
the Hermitian sum. The peaks move to the mirrored labels `+20` and `-30 deg`.

The failure is exact over the symmetric grid:

```text
P_broken(theta) = P_correct(-theta).
```

If only one symmetric source had been used, the sign error could be mistaken
for a plausible answer. The asymmetric two-source fixture makes the mapping
visible.

## 6. Recovery

Figure 5B restores `w(theta)=a(theta)/M` while keeping the received data, SNR,
snapshots, spacing, array size, and scan grid unchanged. The Hermitian product
`w(theta)^H X` now removes the modeled incoming phase and the peaks return to
`-20` and `+30 deg`.

Recovery changes the convention, not the measurements or the answer after
looking at a noise realization.

## Expected observations

- Correct steering makes all contributions from the matched source align.
- Mismatched steering leaves a residual slope and partial cancellation.
- Direct output-power averaging equals `w^H Rhat w`.
- Close sources merge when their conventional beams overlap.
- A larger physical aperture narrows those beams and can resolve the pair.
- Higher SNR lowers the relative scan floor.
- More independent snapshots reduce random ripple without narrowing the beam.
- Wrong-sign steering mirrors every peak; consistent Hermitian steering
  recovers the unchanged data.

## Common interpretation corrections

- If you call Figure 1 a Fourier spectrum, identify the spatial steering
  template and angle axis instead.
- If you say 128 snapshots created a narrower antenna beam, compare the fixed
  aperture and the same deterministic array factor from P62.
- If you identify two sources from the two largest adjacent samples, require
  distinct local lobes rather than two samples from one lobe.
- If you call the wrong-sign peaks front/back ambiguity, reverse the recovered
  curve and check the exact sign-convention identity.
- If you say half-wavelength spacing guarantees arbitrary resolution, separate
  alias avoidance from finite aperture.
- If you treat normalized dB height as absolute gain, inspect the stored linear
  powers and the per-curve normalization.

## Cancellation, timeout, and clean recovery

All loops and matrix sizes are validated before the figures are constructed.
The experiment uses no workers, timers, network, external process, file write,
or persistent checkpoint. After Ctrl+C there is no background task, checkpoint, or partial output
to resume. Close only this lesson's figures if desired:

```matlab
close(findall(0, 'Type', 'figure', 'Tag', 'P63'))
```

Then rerun from the top. The private generators reconstruct the same sources
and noise without changing MATLAB's global random stream. Reviewed ceilings
are 16 elements, two sources, 256 snapshots, 2,001 scan samples, five cases per
sweep, 20,000 private values, 500,000 working numeric values, and five figures.

## Concept connection and completion handoff

P61 encoded arrival angle as spatial phase, and P62 turned ideal residual phase
into a fixed array pattern. P63 applies that match to data and estimates its
power across snapshots. P65 will keep the same data model but replace fixed
delay-and-sum weights with covariance-dependent adaptive weights.

Before completion, explain why the conjugate steering phase aligns one
direction, why an off-target direction partially cancels, why aperture and
snapshot count affect different properties, and how the broken sign convention
was diagnosed and recovered.
