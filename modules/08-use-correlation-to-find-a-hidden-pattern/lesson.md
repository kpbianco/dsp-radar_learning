# P08 Lesson — Use Correlation to Find a Hidden Pattern

## Guiding question

How can a known waveform be located inside noise and delay?

## Physical mental model

Imagine sliding a transparent copy of a known coded pulse along a noisy receiver
record. At each possible start delay, multiply samples that lie on top of one
another and add the signed products. Random noise sometimes agrees and sometimes
disagrees, so much of it cancels in the sum. At the correct alignment, every
chip of the hidden copy agrees with the reference and the contributions add
coherently.

P08 uses a dimensionless reference `s[m]` and a received voltage `x[n]`. If a
positive copy with amplitude `A` starts at zero-based delay `D`, the model is

```text
x[n] = A s[n-D] + w[n],
```

where `s[k]` is zero outside its finite support and `w[n]` is noise. This lab's
correlation convention is

```text
r_xs[ell] = sum_m x[ell+m] s[m].
```

A positive `ell` means the reference begins later in the record. With an
untruncated positive copy and modest noise, the largest signed value occurs at
`ell = D`. Because `s[m]` is dimensionless, every product and the accumulated
correlation have volts as their unit.

## Read the baseline plots

The first figure shows the 26-sample known code, the full 256-sample noisy
record, and then a revealed zoom. The zoom is diagnostic: it proves what was
inserted, but it is not how the delay is estimated. In the full record, individual
samples have little authority because noise can imitate any one sample.

The second figure freezes the correct alignment. Each bar is one product
`x[D+m]s[m]`; the cumulative curve shows those signed products building the
correlation peak. The lower plot repeats that sum for every candidate lag. Its
horizontal coordinate is relative delay in samples, not a MATLAB array index.

The script evaluates the double sum directly. Only after the lag convention is
visible does it check the same values with
`conv(x,fliplr(s))`. Reversal is required because correlation asks whether the
reference matches at each relative placement; the convolution output must also
be relabeled from index `0 ... N+M-2` to lag `-(M-1) ... N-1`.

## Why processing gain appears

The unit-RMS reference has energy

```text
E_s = sum_m |s[m]|^2 = M.
```

With no noise, the correct-lag value is `A E_s`. Independent noise products add
with signs; for white noise with standard deviation `sigma`, their output RMS
is approximately `sigma sqrt(E_s)`. The nominal peak-to-noise-RMS amplitude
ratio therefore scales like

```text
A sqrt(E_s) / sigma.
```

Squaring that amplitude ratio gives the corresponding linear output power SNR,
`A^2 E_s / sigma^2`.

This is coherent integration, not noise removal. A longer useful code can make
the aligned peak grow faster than random output fluctuations, provided the
receiver has the right reference and maintains alignment.

## What the controlled changes isolate

Sweep 1 changes only hidden amplitude from `0.10` to `0.30` to `0.65 V`. The
delay, reference, and exact noise samples stay fixed. At the true lag, increasing
amplitude by `delta A` increases the correlation by exactly `delta A E_s`; weak
cases may still let a random peak win elsewhere.

The noise comparison changes only configured noise standard deviation from
`0.20` to `0.50` to `0.90 V`. The clean signal, delay, code, and underlying
standard-normal samples stay fixed. This lets the random correlation structure
grow without confusing that effect with a new noise realization.

Sweep 2 adds a second weaker copy and changes only its separation from the first:
`1`, `8`, then `32` samples. Each copy produces the reference autocorrelation
centered on its delay. At one-sample separation those lobes overlap into one
deformed peak. Wider spacing reveals two peaks. This is waveform-dependent delay
resolution, not proof that two physical targets merged.

## Limiting cases

- If `A = 0`, no deterministic hidden-pattern delay exists; the largest peak is
  selected from noise.
- If `sigma = 0` and one full positive copy is present, `r_xs[D] = A E_s` and
  the configured code peaks at `D`.
- If `D = 0`, the correct peak is at zero lag even though the convolution vector
  begins at lag `-(M-1)`.
- If the reference has length one, correlation is only sample-by-sample scaling;
  there is no multi-sample processing gain or distinctive shape.
- If the reference is all zeros, every correlation value is zero and delay is
  undefined; P08 rejects that malformed reference.
- If a copy is negative, a signed correlation produces a negative peak. A
  polarity-unknown detector may search `abs(r_xs)`, but it must retain the sign
  for interpretation.
- If the reference is periodic or highly self-similar, several lags can have
  large values and delay becomes ambiguous.
- If two copies are closer than the main-lobe width of the reference
  autocorrelation, their peaks overlap; changing only sample rate does not
  create independent waveform bandwidth.
- If a copy is clipped by the record boundary, fewer products overlap. Raw
  correlation magnitude then changes with overlap length unless normalization
  is handled explicitly.
- Colored noise or interference that resembles the code does not cancel like
  ideal white noise and can create structured false peaks.

## Why the broken case fails

The maximum of `conv(x,fliplr(s))` returns a one-based MATLAB vector index. Even
after subtracting one, that coordinate is a convolution-output index whose
origin corresponds to lag `-(M-1)`. Calling it a delay skips the origin shift:

```text
wrong delay = peak_index - 1
right delay = correlation_lags_samples(peak_index)
```

For a reference of length `M`, the wrong report is exactly `M-1` samples late.
The correlation values are correct; the coordinate interpretation is broken.
Recovery attaches the explicit lag vector and returns the configured delay.

## Radar connection and common mistakes

Correlation is the conceptual core of synchronization and matched filtering. A
radar receiver correlates against a transmitted or expected waveform to estimate
echo delay. P08 stops at signal start delay. Converting a monostatic echo delay
to range later requires propagation speed, round-trip timing, calibration, and
the factor of two; this synthetic result is not a physical range measurement.

Do not read a high peak as proof of a target. Do not compare unnormalized peaks
from references with different energy as though only similarity changed. Do not
confuse the peak's vector index with lag, or MATLAB's one-based storage with the
zero-based physical sample model. Do not claim that close-copy peak merging is
caused by noise when it is already present in the waveform autocorrelation.

P07 is the prerequisite, and this lesson uses base MATLAB only. No toolbox,
external data, helper, network, device, or hardware operation is needed.
