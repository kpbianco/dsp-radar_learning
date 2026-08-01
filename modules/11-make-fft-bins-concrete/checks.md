# P11 Checks: Make FFT Bins Concrete

## Guiding question

What frequency does each FFT bin represent?

Use the figures and `results` structure. These checks test interpretation, not
MATLAB syntax.

## Baseline observation checks

1. With \(f_s=1024\) samples/s and \(N=64\), what is \(\Delta f\)?
   - Expected: 16 Hz.
2. Where is zero-based bin 9 stored, and what frequency does it represent?
   - Expected: MATLAB index 10; +144 Hz.
3. Why are most baseline phase points hidden?
   - Expected: their projection magnitudes are below 0.05 V, so noise or
     roundoff makes phase unstable and physically uninformative.
4. What does the explicit DFT-versus-`fft` assertion establish?
   - Expected: both compute the same finite-record projections; it is not a
     MATLAB runtime claim from repository static tests.

## Predict, then verify

1. Predict the two nearest magnitudes before inspecting the 0.5-bin case.
   - Expected: nearly equal and about \(2/\pi\approx0.637\) V for the ideal
     unit complex tone.
2. Keep 144 Hz and 1024 samples/s fixed but change \(N\) from 64 to 128.
   Predict \(\Delta f\) and the new exact bin.
   - Expected: 8 Hz spacing and zero-based bin 18.
3. If \(f_s\) doubles while \(N\) stays fixed, what happens to bin spacing?
   - Expected: it doubles. The record duration halves.
4. If both \(f_s\) and \(N\) double, what happens to bin spacing and duration?
   - Expected: both remain unchanged; Nyquist coverage increases.

## Interpretation checks

1. Does a half-bin tone contain two physical tones because two bins are large?
   - No. One finite-record tone projects onto multiple discrete basis
     sinusoids.
2. Is the largest FFT bin always an exact continuous-frequency estimate?
   - No. It identifies the strongest grid projection; off-bin tones, windows,
     noise, and nearby signals can bias that report.
3. Why is there no factor of two in the complex-tone magnitude scaling?
   - A complex exponential occupies one signed-frequency bin. Doubling is a
     convention used when folding a real signal's two-sided energy into a
     one-sided display.
4. Why is \(f_s/(N-1)\) the wrong spacing here?
   - DFT bases complete integer turns over \(N\) sample intervals in the
     periodic extension, giving \(f_s/N\). Endpoint-inclusive plotting grids
     answer a different question.
5. How do bins above \(N/2\) get signed labels?
   - Use \((k-N)f_s/N\). Centering reorders values; it does not create bins.

## Failure classification

1. The broken panel reports 160 Hz while the samples and peak array index are
   unchanged. Is this spectral leakage, aliasing, or metadata error?
   - Metadata error: the one-based index was used as zero-based \(k\).
2. What is the minimal recovery?
   - Subtract one from the MATLAB index before multiplying by \(f_s/N\).
3. If a run is cancelled, what needs restoration?
   - No persistent data. Press Ctrl+C, restore the bounded visible controls if
     they were edited, and rerun; unrelated figures and the global RNG remain
     isolated.

## Teach-back completion

In two or three sentences, answer the guiding question and include:

- \(f_k=kf_s/N\) with zero-based \(k\);
- why a tone halfway between bins spreads across projections; and
- why changing \(N\) changes the grid and duration, not the physical tone.

Completion is earned when the explanation keeps MATLAB index, DFT bin, and
physical frequency distinct and correctly diagnoses the broken case. As an
extension, choose one negative-frequency complex tone and predict its unshifted
and centered bin labels before running it.
