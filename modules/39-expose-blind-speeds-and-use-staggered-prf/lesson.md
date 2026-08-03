# Lesson: a moving target can look stationary to a sampled canceller

## Guiding question

Why can a moving target vanish in an MTI radar?

## Physical mental model

A two-pulse MTI canceller compares the current echo with the previous echo. Stationary clutter repeats from pulse to pulse, so subtraction removes it. A moving target normally rotates in complex phase between pulses, so its two samples do not cancel.

The trap is that phase is circular. If a moving target advances by exactly one whole turn, or any integer number of turns, between pulse samples, the radar sees the same phase twice. The canceller cannot distinguish that sampled sequence from stationary clutter. Motion has not stopped; the sampling schedule has hidden it.

This module extends [P38](../38-implement-a-two-pulse-and-three-pulse-mti-canceller/), where the slow-time subtraction was introduced.

## From velocity to the canceller null

For a monostatic radar with wavelength \(\lambda\), an approaching target at radial velocity \(v\) has Doppler frequency

\[
f_d=\frac{2v}{\lambda}.
\]

With pulse repetition frequency \(f_r\), the phase change from one pulse to the next is

\[
\Delta\phi=2\pi\frac{f_d}{f_r}.
\]

The experiment applies the two-pulse operation directly:

\[
y[n]=x[n]-x[n-1].
\]

For a unit-amplitude complex Doppler sequence, its gain is

\[
|H|=|1-e^{-j\Delta\phi}|=2\left|\sin\left(\pi\frac{f_d}{f_r}\right)\right|.
\]

The normalized plots divide this maximum gain of two out, so their vertical scale runs from zero to one. A null occurs whenever \(f_d=kf_r\), giving blind velocities

\[
v_k=k\frac{\lambda f_r}{2},\qquad k=0,\pm1,\pm2,\ldots
\]

At 10 GHz, \(\lambda\approx0.02998\) m. For the 4.0 kHz primary PRF, the first positive blind speed is about 59.96 m/s. That target's Doppler is 4.0 kHz, exactly one phase revolution per pulse, so every sampled target phasor repeats.

## Why the second PRF recovers the target

The same physical target observed at 5.3 kHz PRF still has 4.0 kHz Doppler, but now its phase increment is \(2\pi(4000/5300)\), not an integer turn. Its samples differ and the subtraction produces a nonzero output.

P39 forms two coherent dwells, applies the canceller within each dwell, normalizes each amplitude, and then uses the larger amplitude (equivalently, an OR of threshold decisions). This fusion is deliberately noncoherent: samples taken with different pulse intervals are not added as though they shared one uniform slow-time grid.

Staggering moves the nonzero blind-speed nulls; it does not remove the zero-velocity notch. Both PRFs must suppress stationary clutter at \(v=0\). It also does not guarantee unlimited coverage: specially related PRFs can share nonzero nulls, and real radar scheduling introduces range ambiguity, dwell-time, transmitter, and processing tradeoffs not modeled here.

## Read the figures in physical order

1. **Blind target in two dwells:** the 4.0 kHz samples repeat modulo 360 degrees and subtract to zero; the 5.3 kHz samples walk and survive.
2. **Velocity response:** each colored curve has regularly spaced nulls. Their spacings differ because blind speed is proportional to PRF.
3. **Detection coverage:** an OR decision succeeds wherever either dwell exceeds the illustrative threshold.
4. **Second-PRF sweep:** only PRF 2 changes while the target remains at the primary blind speed. Reusing 4.0 kHz gives no diversity.
5. **Broken and recovered:** identical PRFs duplicate the same holes; restoring 5.3 kHz separates them.

## Limiting cases and interpretation cautions

- At \(v=0\), the output is zero for every PRF. That is the desired stationary-clutter notch, not a stagger failure.
- Near a null, gain is small rather than abruptly binary. Detection depends on target amplitude, noise, clutter residue, threshold, and integration.
- A null in MTI amplitude is not proof that no target exists. It is a property of the canceller plus sampling schedule.
- PRF changes the blind-speed spacing; it does not change the target's physical Doppler.
- The displayed threshold is pedagogical, not a CFAR design or a probability-of-detection claim.
- The synthetic point-target model omits acceleration, range migration, clutter decorrelation, transmitter limits, and ambiguous-range scheduling.

## Connection to the next concept

P39 treats each PRF dwell separately and combines its evidence. Later pulse-Doppler processing and detection modules will add coherent/noncoherent integration, clutter models, range-Doppler maps, and adaptive thresholds. The durable idea is already visible: diversity helps only when the second observation moves the failure mechanism.
