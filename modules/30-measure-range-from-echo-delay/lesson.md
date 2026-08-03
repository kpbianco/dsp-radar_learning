# P30 Lesson: Measure Range from Echo Delay

## Guiding question

How does round-trip delay become target range?

## Physical model: use a clock as a ruler

A monostatic radar transmits from and receives at the same site. If a pulse
leaves at time zero, reaches a target at range (R), and returns after delay
\(\tau\), the wave traveled (2R):

\[
2R=c\tau, \qquad R=\frac{c\tau}{2}.
\]

The factor of two is geometry, not a calibration adjustment. Using
`R = c*tau` treats the measured round-trip time as a one-way trip and reports
twice the target range. P29 asks whether the echo has enough power to observe;
P30 assumes an observable echo and asks where its delayed copy occurs.

## From received samples to delay

The transmitted pulse is a known sequence (s[m]). For each candidate
nonnegative lag \(\ell\), the experiment aligns it with the received fast-time
record (x[n]) and forms

\[
r_{xs}[\ell]=\sum_m x[\ell+m]s^*[m].
\]

Products add coherently when the pulse and echo align, so the correlation
magnitude peaks near the echo start. The script evaluates this sum explicitly
and cross-checks it against convolution with the reversed conjugate pulse. It
does not use `xcorr`, a circular shift, or a toolbox detector.

If the selected integer lag is \(\hat\ell\) and the sample rate is \(f_s\),

\[
\hat\tau=\frac{\hat\ell}{f_s}, \qquad
\hat R=\frac{c\hat\ell}{2f_s}.
\]

One lag step therefore corresponds to

\[
\Delta R_{sample}=\frac{c}{2f_s}.
\]

At 20 MHz it is about 7.49 m. A nearest-bin integer estimate is within half a
bin for a clean isolated peak; noise, interference, ambiguity, clipping, or a
bad time reference can violate that simple bound.

## Why the echo is inserted before quantizing its lag

Real propagation delay is continuous. The baseline delay is 120.35 samples,
so the experiment evaluates a zero-extended piecewise-linear transmitted pulse
at `n - 120.35`. Rounding to 120 samples during echo creation would silently
move the simulated target onto the receiver grid and erase the phenomenon the
fractional-delay sweep is meant to reveal. Zero extension also prevents an
unphysical echo from wrapping from the end of the capture back to its start.

The maximum correlation bin gives an integer estimate. A three-point
parabolic fit uses the local peak shape to return a sub-sample value. That
interpolation can reduce grid quantization for this clean model, but it does
not create new samples, bandwidth, or target-separation information. Its bias
depends on the actual peak shape and its variance grows with noise.

## Sample rate versus waveform width

The first sweep holds the physical delay and one-microsecond pulse duration
fixed while changing only sample rate. Doubling (f_s) halves the range-bin
step, so the same continuous delay lands on a finer numerical grid. This is a
sampling effect.

The pulse's autocorrelation has a finite mainlobe. Two positive echoes closer
than that useful width can add into one broad or distorted peak even when the
sample grid is fine. The separation sweep keeps both echo amplitudes and the
pulse fixed, changing only the second delay. Its 0.5 and 1.0 microsecond cases
produce one visible local peak under the stated rule; 1.5 microseconds produces
two. This is waveform-limited separation behavior, not proof of a universal
radar resolution number. P31 separates resolution from accuracy in detail.

## What noise and amplitude do here

Correlation integrates aligned pulse samples, so an isolated delayed copy can
remain locatable when individual received samples look noisy. The private
seed makes the baseline repeatable without changing MATLAB's global random
stream. The sample-rate, fractional-delay, and separation sweeps are noise-free
on purpose: each sweep isolates one mechanism instead of mixing sample-grid
behavior with a lucky noise realization.

Echo amplitude scales correlation height. It does not change the delay-to-range
equation. If the echo becomes too weak, a noise or sidelobe peak can win and
the estimator can make a large error rather than a graceful half-bin error.
P28's detector statistics and P29's power budget determine when an echo can be
trusted; P30 does not turn correlation height into probability of detection.

## Assumptions and limiting cases

- The transmit timestamp, receive sample clock, and propagation speed are
  known and share one time reference.
- The target is stationary during the pulse, the path is monostatic, and the
  synthetic record contains no clutter, multipath, Doppler, dispersion,
  receiver saturation, or timing jitter.
- The capture is long enough for every echo and the complete finite pulse.
- At zero delay the ideal monostatic range is zero, but a practical radar may
  be blind while transmitting or recovering from leakage.
- A delay outside the recorded window cannot be recovered by this script.
- An integer-lag estimate cannot distinguish delays that map to the same bin.
- Parabolic refinement needs a peak with two neighbors and nonzero curvature;
  an edge peak or flat plateau must be rejected rather than divided by zero.
- The linear fractional-delay model is transparent and adequate for this
  lesson, but it is not an RF channel or a bandlimited fractional-delay filter.

## Common interpretation mistakes

1. Forgetting the return trip and using `c*tau`.
2. Calling a lag in samples a delay in seconds without dividing by (f_s).
3. Confusing the 7.49 m sample step at 20 MHz with one-way distance or with a
   universal pulse range resolution.
4. Rounding the simulated delay before sampling and then claiming sub-sample
   performance.
5. Treating a parabolic peak coordinate as new waveform information.
6. Using circular shift, which can wrap delayed energy into early fast time.
7. Calling two merged positive echoes one precisely measured target without
   checking the correlation shape.
8. Treating this seeded synthetic result as hardware timing calibration,
   detection probability, or operational radar validation.

## Dependencies and concept connection

P08 introduced explicit correlation and its lag convention. P29 connected
range to echo power; a weak echo can make the largest correlation peak
unreliable. P30 adds the physical clock conversion and continuous-delay
sampling model. P31 will use this distinction to separate how finely one peak
can be located from whether two peaks can be separated.

The runtime path is base MATLAB only and uses bounded loops and finite arrays.
No toolbox, file, network, hardware, worker, timer, or external transaction is
part of the experiment.
