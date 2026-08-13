# P79: Compare SAR Resolution, Aperture Length, and Windowing

**Phase 9: SAR, ISAR, Passive Radar, and Capstone**  
**Status:** Implemented by governed batch `P79`

## Guiding question

What controls range and cross-range resolution and sidelobes?

## Experiment

The experiment builds a focused SAR point-spread function from two transparent
coherent sums. Frequency samples across `200 MHz` produce the range response;
platform positions across a `30 m` synthetic aperture produce the cross-range
response for a `10 GHz` monostatic radar viewing broadside at `1000 m`.

Three point targets make the two axes visible in a small range/cross-range
image. The script then changes only bandwidth, only aperture length, only
aperture weighting, and only platform-sample spacing. It reports half-power
width, first-null locations, and peak sidelobe level from unclipped linear
responses. The intentionally broken `5 m` platform spacing creates nearly
equal-height cross-range replicas about `3 m` apart; recovery rebuilds the
response from the unchanged scene with `0.25 m` spacing.

## Learning goal

Independently control the two dimensions: transmitted bandwidth sets range
resolution, synthetic aperture and geometry set cross-range resolution, and
taper trades lower sidelobes for a wider mainlobe. Explain why dense display
pixels cannot repair sparse aperture sampling.

## Prerequisites and dependencies

- P12 and P33 establish finite-record leakage and the width/sidelobe cost of
  weighting.
- P30-P32 establish two-way range and bandwidth-limited pulse compression.
- P61-P63 establish spatial phase, finite aperture, taper, and grating lobes.
- P75 establishes exact monostatic SAR phase history.
- P76 establishes the range-compressed matrix.
- P77 establishes explicit path-compensated coherent focusing.
- P78 establishes why the correct range path must be sampled before focusing.
- Runtime target: base MATLAB R2016b or newer; no toolbox is used.

The model assumes known broadside geometry and ideal point targets. P80 owns
unknown motion error and autofocus.

## Run

```matlab
cd modules/79-compare-sar-resolution-aperture-length-and-windowing
run('experiment.m')
```

Then follow `walkthrough.md` one transition at a time and use `checks.md` for
the completion conversation. The script writes no files and performs no
network, timer, worker, or external-process operation.

## Files

- `experiment.m` — seeded point scene, explicit range/aperture sums, four
  controlled comparisons, sparse-sampling failure, recovery, assertions, and
  resource bounds
- `lesson.md` — physical model, equations, limiting cases, and interpretation
  traps
- `walkthrough.md` — baseline observations, one-variable changes, failure,
  recovery, cancellation, rollback, and concept connection
- `checks.md` — answered observation/prediction checks and teach-back rubric

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Keep the guiding question exactly:
"What controls range and cross-range resolution and sidelobes?" Begin with the
separable focused point response and inspect one dimension at a time. Show the
explicit coherent sums over frequency and platform position. Vary only
bandwidth, then only aperture length. Compare uniform and Hamming aperture
weights without claiming that taper improves resolution. Deliberately
undersample the platform track so cross-range aliases appear, and recover from
the unchanged scene with dense sampling. Distinguish physical resolution from
display spacing, connect each metric to metres and dB, teach physical meaning
rather than MATLAB syntax, and never describe static checks as MATLAB runtime
evidence.
