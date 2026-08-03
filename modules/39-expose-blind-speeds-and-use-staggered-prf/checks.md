# Checks: blind speeds and staggered PRF

Guiding question: Why can a moving target vanish in an MTI radar?

Use the baseline figures and console metrics. Give physical explanations; MATLAB syntax is not the learning target.

## Observation checks

1. At the primary first blind speed, what happens to the target-only 4.0 kHz two-pulse output, and what small component can remain in the observed output?
2. Which figure shows that the same physical target survives the 5.3 kHz dwell?
3. What feature remains at zero velocity after max/OR fusion, and why should it remain?

## Interpretation checks

4. Explain why a target moving at about 59.96 m/s can produce identical samples at 4.0 kHz PRF.
5. Why is the first blind-speed spacing \(\lambda f_r/2\), rather than \(\lambda f_r\)?
6. Why are the two PRF dwell outputs compared noncoherently instead of concatenating their samples onto one uniform slow-time axis?
7. Does a missing canceller output prove that no target exists? State the narrower conclusion the radar may draw.

## Prediction checks

8. If the carrier frequency is halved while PRF stays fixed, predict how the blind-speed spacing changes.
9. If PRF 2 is set equal to PRF 1, predict the fused response at every primary blind speed before viewing Figure 5.
10. A target sits at the first 5.3 kHz blind speed. Predict whether the 4.0 kHz dwell has zero or nonzero gain, then verify it in Figure 2.

## Answers and evidence

1. The clean target output is zero because consecutive target samples match. Differenced noise can leave a small residual; it is not recovered target energy.
2. Figure 1's secondary-output panel shows a nonzero target-only result; Figures 2 and 3 show the corresponding gain and threshold recovery.
3. The zero-velocity notch remains because both cancellers intentionally reject stationary echoes.
4. At that velocity, \(f_d=2v/\lambda=4.0\) kHz. Sampling at 4.0 kHz advances phase by exactly \(2\pi\) per pulse, so the complex samples repeat.
5. Monostatic Doppler contains the round-trip factor of two: \(f_d=2v/\lambda\). Setting \(f_d=f_r\) gives \(v=\lambda f_r/2\).
6. Different PRIs create different sample grids and phase increments. Each dwell is coherent internally, but direct coherent concatenation would pretend the combined samples have uniform spacing.
7. No. It shows that the target contribution may lie at or near this canceller's sampled-response null; another PRF or processing path is needed.
8. Halving carrier frequency doubles wavelength, so the blind-speed spacing doubles.
9. The second response duplicates the first, so its nulls coincide and fusion remains zero at every primary blind speed.
10. It is nonzero. The 5.3 kHz first blind speed is not an integer multiple of the 4.0 kHz blind spacing in the plotted interval.

## Short teach-back rubric

A complete teach-back should say all four of these in about a minute:

- target velocity creates monostatic Doppler \(2v/\lambda\);
- the two-pulse canceller subtracts adjacent slow-time samples;
- an integer phase turn per PRI makes a moving target look stationary and defines \(v_k=k\lambda f_r/2\);
- a genuinely different PRF moves the nonzero nulls so max/OR fusion can recover the target, while zero velocity remains intentionally nulled.

Before personal completion, calculate the 4.0 kHz first blind speed and use Figure 1 or 2 to demonstrate its recovery at 5.3 kHz.
