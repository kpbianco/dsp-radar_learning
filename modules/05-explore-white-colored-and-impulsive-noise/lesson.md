# P05 Lesson — Equal RMS Is Not Equal Behavior

## Guiding question

**What does the word noise hide about time behavior and spectrum?**

“Noise” often gets reduced to one RMS number. RMS answers how much average
power a record contains. It does not say whether the samples are Gaussian,
whether adjacent samples remember one another, where the power sits in
frequency, or whether rare outliers dominate the peaks. Those properties
change what a receiver sees and which processing step can help.

P04 separated bounded quantization error from overload. P05 uses that habit of
failure classification again: equal voltage RMS is a controlled starting
point, not a complete description of disturbance.

## Four physical models

The baseline creates four centered records and rescales each to
`0.25 V RMS`.

1. **Gaussian white noise** has independent samples drawn from a bell-shaped
   distribution. Its power is spread broadly, so its autocorrelation is close
   to an impulse: strong at zero lag and small elsewhere.
2. **Low-pass colored noise** passes an independent Gaussian driver through
   the explicit one-pole recursion

   ```text
   y[n] = alpha y[n-1] + (1-alpha) w[n].
   ```

   A large `alpha` carries more of the previous output forward. The waveform
   changes slowly, adjacent samples correlate, and power collects at low
   frequency. “Colored” describes spectral shape, not a different unit or
   necessarily a non-Gaussian amplitude distribution.
3. **Narrowband interference** is a sinusoid at the target frequency. It is
   deterministic after its seeded phase is chosen, yet it is a realistic
   disturbance because a receiver does not control its phase or origin. Its
   power occupies one narrow spectral line and its autocorrelation oscillates
   rather than dying quickly.
4. **Impulsive noise** is zero most of the time and contains sparse signed
   outliers. Equal RMS forces its total power to match the other records, but
   its large crest factor and long histogram tails reveal how that power
   arrives.

The experiment calls all four “noise types” for comparison, while retaining
the more precise label *interference* for the narrowband case.

## Why center and normalize

For a finite raw record `x[n]`, the script first removes its sample mean and
then applies

```text
x_equal[n] = sigma_target (x[n] - mean(x)) / rms(x - mean(x)).
```

Every normalized record therefore has the same finite-record RMS
`sigma_target`. The operation preserves waveform shape, correlation shape, and
relative spectral distribution while removing total power as a confound. It
does not make the probability distributions or spectra identical.

This distinction matters because generator parameters do not define a common
physical scale. A unit-variance Gaussian source, a unit-amplitude sinusoid, a
smoothed source, and a mostly-zero impulse source naturally have different
RMS. Comparing those raw outputs would answer “which generator happened to be
loudest?” rather than “how does noise type matter?”

## Four views answer four different questions

### Time record and histogram

A short time record shows smoothness, periodicity, and isolated peaks. The
histogram counts the fraction of samples inside common voltage bins. Gaussian
white and Gaussian-driven colored noise can have similar bell-shaped
histograms even though one has memory and the other does not. Conversely,
impulsive noise may put most samples near zero and a few far into the tails.

The crest factor

```text
CF = max |x[n]| / rms(x)
```

summarizes peak burden. It is useful for recognizing outlier stress, but it
still does not reveal where power sits in frequency.

### Autocorrelation

At nonnegative lag `ell`, the script computes the finite-record estimate

```text
r[ell] = mean_n x[n] x[n+ell]
```

and divides by `r[0]`. White noise should be near zero beyond lag zero in a
long record. Colored noise decays over several samples. A sinusoid produces an
oscillating correlation. Sparse impulses generally have little sustained
memory even though their distribution is far from Gaussian.

Autocorrelation and PSD are two descriptions of the same second-order
structure: longer correlation in time corresponds to more concentrated power
in frequency.

### Power spectral density

The script states and evaluates the DFT

```text
X[k] = sum_n x[n] exp(-j 2 pi k n/N)
```

and forms a rectangular-window, one-sided periodogram

```text
Sxx[k] = |X[k]|^2 / (fs N).
```

Non-DC and non-Nyquist bins are doubled after discarding the negative-frequency
half. The resulting unit is `V^2/Hz`; its decibel label is `dB V^2/Hz`.
This raw periodogram is deliberately not Welch-averaged—P14 will study why
averaging changes estimator variance.

### Tone projection

Every noise record is added to the same coherent target tone. The time-domain
tone-to-noise ratio is identical because every noise RMS is identical. The
receiver then estimates the target’s complex amplitude with

```text
c_hat = (2/N) sum_n y[n] exp(-j 2 pi f0 n/fs).
```

Broadband noise contributes only its finite projection onto that sinusoid.
Low-pass colored noise contributes little at a target well above its strongest
band. A co-channel sinusoidal interferer projects completely into the target
estimate: a taller spectral line is not proof that more of the line came from
the desired target. Sparse impulses spread error broadly and can also stress
time-domain clipping or robust estimators even when their average power is
ordinary.

## Parameter limits that expose the mechanisms

- **`alpha = 0`:** the one-pole equation becomes the independent driver; the
  colored source has essentially no filter memory.
- **`alpha` approaching 1:** correlation lasts longer and power crowds toward
  DC. Exactly 1 is excluded because the `(1-alpha)` input term vanishes and the
  committed zero initial condition produces a zero record that cannot be RMS
  normalized.
- **Interferer offset `0 Hz`:** target and interferer occupy the same coherent
  basis function, so frequency alone cannot separate them.
- **Nonzero coherent-bin offset:** over this finite record, a sinusoid at an
  integer-bin offset is orthogonal to the target basis and does not bias the
  exact target projection. A shorter, noncoherent, or windowed record would
  change that leakage behavior.
- **Impulse probability approaching zero:** finite records may contain no
  outlier, making RMS normalization undefined. The script requires a positive
  bounded rate and checks the seeded baseline has enough events.
- **Very high impulse probability:** the process stops looking sparse. The
  baseline guard limits the editable probability below `0.25`.
- **Infinite record idealization:** white-noise off-zero autocorrelation tends
  to zero. A finite realization only approaches that result; small random
  sidelobes are expected.

## Common interpretation mistakes

- **“Same RMS means same noise.”** It means same average finite-record power,
  nothing more.
- **“A bell-shaped histogram proves whiteness.”** A histogram ignores sample
  order. Low-pass colored Gaussian noise can remain bell-shaped.
- **“Flat-looking time samples prove a flat spectrum.”** Time appearance alone
  cannot locate power reliably; inspect PSD and correlation.
- **“A strong target-frequency line proves detection.”** Co-channel
  interference can create or rotate the same line and bias amplitude or phase.
- **“Impulsive noise must have more RMS power.”** Equal-RMS impulsive noise can
  instead trade many quiet samples for rare high peaks.
- **“One periodogram is the true PSD.”** It is a finite-record estimate with
  variance. Use it here for visible contrasts, not false precision.
- **“Normalization fixes hardware overload.”** Digital rescaling creates a
  fair software comparison; it cannot recover samples already clipped in an
  ADC or analog front end.

## DSP and radar connection

A radar receiver can face thermal white noise, low-frequency drift or colored
clutter, narrowband leakage or a jammer, and impulsive interference. Equal
integrated power does not imply equal effect on a range-Doppler cell, coherent
integrator, detector, or ADC. Filtering helps when unwanted power occupies a
different band; it cannot separate a co-channel signal without another
distinguishing dimension. Robust clipping or outlier-resistant processing can
help impulses, while ordinary averaging is designed around finite-variance
broadband behavior.

The transferable habit is to pair a power number with distribution, bandwidth,
correlation, and peak behavior before choosing a mitigation.
