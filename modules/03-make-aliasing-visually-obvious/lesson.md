# Lesson: Frequency Folding Is Deterministic

## Guiding question

Why does a high-frequency tone appear as a lower-frequency tone after sampling?

## Physical model

A sampler is a clock that records one amplitude every `1/fs` seconds. It does
not count the oscillations that occur between clock ticks. If two continuous
tones land on the same amplitude at every tick, the stored sequence cannot tell
which tone was present.

P02 established that samples are timed measurements rather than a continuous
line. P03 follows that consequence into frequency: a continuous tone can make
several whole turns between measurements without leaving evidence of those
extra turns.

## One equation explains every fold

For a cosine sampled at rate `fs`,

\[
x[n] = A\cos\left(2\pi \frac{f_{in}}{f_s}n+\phi\right).
\]

Adding an integer multiple of `fs` changes the angle by `2*pi*k*n`. That is an
integer number of turns for every integer sample index, so the samples remain
unchanged. Choose the nearest integer multiple of the sample rate:

\[
k=\operatorname{round}(f_{in}/f_s),\qquad
f_{fold}=f_{in}-k f_s.
\]

The signed fold lies between `-fs/2` and `+fs/2`. A real cosine cannot
distinguish positive from negative frequency because cosine is even, so its
displayed apparent frequency is

\[
f_{apparent}=|f_{fold}|.
\]

When the fold is negative, the equivalent positive-frequency cosine uses
phase `-phi`. The baseline therefore maps 700 Hz at 1000 samples/s to signed
-300 Hz, or an apparent 300 Hz cosine with reversed phase. The high and low
continuous curves differ between samples but cross every stored measurement.

## Estimating what the samples appear to contain

The experiment does not hide the answer inside an FFT or toolbox estimator. A
noiseless sampled cosine obeys the recurrence

\[
x[n+1]+x[n-1]=2\cos(\omega)x[n].
\]

The script estimates `cos(omega)` from all interior samples, clips only possible
roundoff beyond `[-1,1]`, and converts `acos(omega)` to hertz. Because `acos`
returns an angle from zero through pi, this estimator necessarily reports an
unsigned frequency from DC through Nyquist. Its triangular output follows the
same folds predicted by the equation above.

This exact recurrence assumes one clean, stationary real cosine. Noise,
multiple tones, changing frequency, or a very short record require a more
general estimator, but they do not change the aliasing relationship created at
the sampler.

## Limiting cases

- **Well below Nyquist:** if `0 < f_input < fs/2`, the nearest fold is the input
  itself. That does not prove the analog input contained no higher alias-family
  member; it uses the prior assumption that the input band was restricted.
- **Exactly at Nyquist:** samples alternate signs. For a real cosine, positive
  and negative Nyquist frequency are the same sequence, and much of phase is
  not identifiable. The sign chosen at this boundary is a convention.
- **At an integer multiple of fs:** the apparent frequency is DC. The sampler
  repeatedly visits the same phase even though the continuous input may be
  oscillating rapidly.
- **Several multiples of fs:** folding repeats. It is a triangular pattern, not
  increasing uncertainty or random corruption.
- **Complex I/Q samples:** signed rotation can be observed, so positive and
  negative discrete-time frequencies remain distinct. Frequencies separated by
  integer multiples of `fs` still alias.

## Why radar engineers care

An ADC can fold an out-of-band interferer into a radar receiver's processing
band. An analog anti-alias filter must restrict input bandwidth before sampling;
digital processing cannot later determine which alias-family member produced
an already ambiguous sequence.

The same mathematics appears in slow time. A pulse-Doppler radar samples target
phase once per pulse, so pulse repetition frequency (PRF) plays the role of
`fs`. Doppler beyond `PRF/2` folds to an apparent lower Doppler and therefore an
ambiguous radial velocity. Frequency folding in this lesson is the small,
visible version of Doppler ambiguity and blind interpretation risk.

## Dependency and compatibility boundary

This module depends on P02's measurement model and requires no toolbox beyond
base MATLAB. Folding, phase correction, and recurrence estimation are explicit
arithmetic. There are no helper functions, external files, hardware inputs,
network requests, or hidden spectral convenience calls.
