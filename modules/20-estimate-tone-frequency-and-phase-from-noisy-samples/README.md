# P20: Estimate Tone Frequency and Phase from Noisy Samples

**Phase 2: Fourier, Spectral, and I/Q Intuition**  
**Status:** Implemented by batch `P20`

## Guiding question

How accurately can frequency and phase be estimated from a finite noisy record?

## Experiment

Generate one complex tone at a fractional FFT bin with controlled SNR and
estimate frequency using the peak FFT bin, a three-bin interpolated FFT peak,
and a coherent adjacent-sample phase increment. Estimate initial phase by
de-rotating the record at each frequency estimate and coherently summing the
samples.

## Procedure

Run the deterministic baseline, then sweep SNR while record length stays fixed
and sweep record length while SNR stays fixed. Compare frequency bias and
standard deviation, circular phase bias and spread, phase wrapping, and a
deliberately broken endpoint-phase estimate. Finally collapse the tone
amplitude while holding receiver noise fixed and use coherence to reject the
plausible-looking but unsupported estimate.

## What this should teach

Estimator performance depends on observation time, SNR, model assumptions,
and whether phase is combined coherently. FFT-bin spacing is a reporting grid,
not by itself an accuracy bound; interpolation can reduce grid quantization,
while phase-increment estimation uses every adjacent rotation but requires a
single tone whose per-sample rotation is inside the signed Nyquist interval.

## Prerequisite

Complete **P19** first. P19 establishes a usable complex I/Q record and shows
why receiver imbalance can corrupt phase; P20 assumes those impairments have
already been corrected well enough that a single-tone model is meaningful.

## Completion condition

You can use the plots and metrics to explain which estimator is most reliable
for the observed SNR and record length, why phase error must be compared
modulo `2*pi`, and why low coherence means the estimate should be withheld.

## Start

```bash
./bin/learn start 20
```

Then run `experiment.m`, keep the visible controls at their baseline values for
the first pass, and follow `walkthrough.md` one transition at a time.

## Files

- `experiment.m` — seeded base-MATLAB experiment, metrics, sweeps, and failure case
- `lesson.md` — physical model, equations, limits, and radar connection
- `walkthrough.md` — guided baseline, two one-variable sweeps, failure, and recovery
- `checks.md` — observation, prediction, interpretation, and teach-back checks

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. The guiding question is: "How
accurately can frequency and phase be estimated from a finite noisy record?"
Start with the physical meaning of a rotating noisy phasor, inspect one plot at
a time, compare the explicit peak-bin, interpolated-FFT, and coherent
phase-increment operations, and connect every SNR or duration change to its
effect on bias and spread. Use the broken wrapped-endpoint estimate and the
low-coherence case to correct any claim that every numerical answer is a valid
measurement. Focus on interpretation rather than MATLAB syntax.
