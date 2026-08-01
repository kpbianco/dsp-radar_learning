# P11 Lesson: Make FFT Bins Concrete

## Guiding question

What frequency does each FFT bin represent?

## Physical mental model

Imagine holding a bank of perfectly timed complex oscillators against one
finite record. Each oscillator turns at a frequency that completes an integer
number of cycles in that record. Multiply the samples by the opposite rotation
and add. A large sum means the record contains a strong projection onto that
oscillator; cancellation means it does not.

Those oscillators are the DFT bins. An FFT computes the same projections more
efficiently; it does not change which frequencies the bins represent.

## The bin-frequency map

For sample rate \(f_s\), record length \(N\), sample index \(n\), and zero-based
bin \(k\),

\[
X[k] = \sum_{n=0}^{N-1} x[n] e^{-j2\pi kn/N},
\qquad
f_k = k\frac{f_s}{N}.
\]

The spacing is therefore

\[
\Delta f = \frac{f_s}{N} = \frac{1}{T},
\]

where \(T=N/f_s\) is the observed record duration. At 1024 samples/s with 64
samples, the spacing is 16 Hz. Zero-based bin 9 represents 144 Hz. MATLAB stores
that value at array index 10 because MATLAB indexing begins at one.

The unshifted FFT array labels bins \(0\) through \(N-1\). Frequencies above
Nyquist wrap into negative frequency: for bins above \(N/2\), use
\((k-N)f_s/N\). For even \(N\), DC and Nyquist are special self-opposed points.
The centered plot simply rearranges the same bins from \(-f_s/2\) to just below
\(+f_s/2\).

## Exact-bin and between-bin tones

A complex tone exactly at \(f_k\) completes an integer number of turns in the
record. Its projection adds coherently in bin \(k\) and cancels at every other
ideal bin. Its normalized bin magnitude is the tone amplitude, and the bin
phase is the tone's starting phase.

A tone at \((k+\delta)\Delta f\), where \(0<\delta<1\), is not one of the basis
oscillators. Its finite record projects onto multiple bins. At a half-bin
offset, the two nearest magnitudes are equal in the ideal noise-free case and
their phases differ by almost \(\pi\) for a long record. That spread is the
rectangular record window's response, not random noise and not two physical
tones.

Phase at a near-zero projection is unstable: tiny noise or roundoff can rotate
an almost-zero complex number anywhere. The baseline plot therefore hides
phase below a stated magnitude threshold. Read phase only after confirming the
associated magnitude is meaningful.

## What changing record length really changes

At fixed sample rate, increasing \(N\) observes the signal for longer and makes
\(\Delta f=f_s/N\) smaller. The experiment keeps a 144 Hz tone fixed:

- \(N=32\): \(\Delta f=32\) Hz, so the tone lies at bin 4.5;
- \(N=64\): \(\Delta f=16\) Hz, so the tone lies exactly at bin 9;
- \(N=128\): \(\Delta f=8\) Hz, so the tone lies exactly at bin 18.

The physical tone did not move. Only the projection grid and observation time
changed. A smaller bin spacing is useful, but it is not permission to call the
largest bin the exact unknown tone frequency. Windowing, noise, multiple tones,
and estimator choice still matter; P12 and P13 examine leakage and zero padding
separately.

## Limiting cases

- At DC, \(k=0\), the basis does not rotate; the bin is the record sum.
- At Nyquist for even \(N\), the basis alternates sign each sample. Positive and
  negative Nyquist are the same sampled sequence.
- With \(N=1\), there is only DC and no frequency discrimination.
- As \(N\) grows at fixed \(f_s\), duration grows and spacing shrinks.
- If \(f_s\) and \(N\) grow in the same ratio, duration and bin spacing stay
  unchanged even though there are more samples and a wider Nyquist interval.
- Exactly at half-bin, neither neighboring bin is the tone frequency; they are
  the two closest projection frequencies.

## Broken case and recovery

The broken axis labels MATLAB array index \(m\) as though it were DFT bin \(k\).
That reports every frequency one bin too high. The 144 Hz peak at array index 10
is mislabeled 160 Hz. Recovery is not a calibration fudge: use \(k=m-1\), then
\(f_k=kf_s/N\), which returns 144 Hz.

## Radar connection and common interpretation mistakes

Fast-time and slow-time radar FFTs use the same map. A range or Doppler cell is
a projection grid point determined by sampling interval and coherent record
length. Confusing array index, bin number, and physical units creates a fixed
range or velocity bias. Treating the peak bin as an exact continuous estimate
can create quantized tracks or biased velocity reports.

Common mistakes are:

- using MATLAB's one-based index directly in \(kf_s/N\);
- using \(f_s/(N-1)\), which belongs to some endpoint-inclusive plot grids, not
  to the DFT basis;
- doubling a complex-tone magnitude as if it were a one-sided real spectrum;
- interpreting phase at bins whose magnitudes are near zero;
- calling off-bin spread noise; and
- claiming a longer FFT changes the physical tone instead of the observation
  grid.

The durable answer is: identify zero-based \(k\), compute \(\Delta f=f_s/N\),
map wrapped bins to signed frequency when needed, and interpret magnitude and
phase as finite-record projections.
