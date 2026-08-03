# P34 lesson: Plot and Interpret the Ambiguity Function

Guiding question: **How does a waveform respond to simultaneous delay and Doppler mismatch?**

## A matched filter asks a two-coordinate question

P33 examined a delay cut through one LFM response. A moving target also shifts
carrier phase during the pulse, so a receiver replica can be wrong in delay,
Doppler, or both. The narrowband ambiguity function records the coherent match
for every pair:

\[
\chi(\tau,\nu)=\int s(t)s^*(t-\tau)e^{-j2\pi\nu t}\,dt.
\]

The script evaluates the discrete version directly:

\[
\chi[k,\nu]=\sum_n s[n]s^*[n-k]e^{-j2\pi\nu n/F_s}.
\]

Only samples shared by `s[n]` and the zero-filled shifted copy `s[n-k]`
contribute. Dividing the magnitude by waveform energy makes the origin equal
to one, so shapes can be compared without mistaking pulse energy for
resolution.

Imagine sliding a replica left and right while also spinning it at a trial
Doppler. A bright ambiguity cell means both settings let many complex samples
point in nearly the same direction. A dark cell means the overlap is small or
the phasors cancel.

## Read a surface through two cuts

The zero-Doppler cut, `|chi(tau,0)|`, is the familiar matched-filter delay
response. Its mainlobe describes delay discrimination, while its sidelobes
show where a strong target can leak into another delay.

The zero-delay cut, `|chi(0,nu)|`, asks how quickly coherent response is lost
when delay is correct but Doppler is wrong. Its width is Doppler tolerance,
not the radar's Doppler-estimation resolution across a train of pulses.

The full surface matters because the two cuts do not show whether the peak
moves when both coordinates are wrong. A single number cannot summarize a
waveform's range resolution, sidelobes, tolerance, and coupling.

## Three equal-duration waveforms, three shapes

### Rectangular pulse

Every sample has the same phase. At zero Doppler, overlap falls linearly with
delay, producing a broad triangular cut. At zero delay, the finite coherent
duration produces a sinc-like Doppler cut. Increasing duration therefore
widens the delay response but narrows the Doppler response. The surface has a
thumbtack's opposite: a broad delay-Doppler pedestal centered at the origin.

### LFM chirp

For

\[
s(t)=e^{j\pi Kt^2}, \qquad K=B/T,
\]

a delayed copy differs by an approximately constant frequency `K*tau` over
the overlap. The ambiguity sum becomes coherent near

\[
\nu=K\tau, \qquad \tau=\nu/K.
\]

This creates the diagonal LFM ridge. Wide bandwidth makes the zero-Doppler
delay mainlobe narrow, but a Doppler mismatch can move the response to a
biased delay. That movement is delay-Doppler coupling, not a second target.

### Binary phase-coded pulse

The seeded code flips phase by 180 degrees at chip boundaries. A shifted
replica crosses different polarities, so most off-origin terms cancel. Chip
duration sets the fine delay scale, while total code duration controls much of
the zero-delay Doppler width. Code sidelobes depend on the actual polarity
pattern; adding chips is not a guarantee that every sidelobe falls.

## The three one-variable sweeps

The duration sweep changes only the rectangular pulse length. Full -3 dB
delay width grows with duration, while full -3 dB Doppler width shrinks. This
is the time-frequency trade for an unmodulated pulse.

The bandwidth sweep holds LFM duration fixed. More swept bandwidth narrows the
zero-Doppler delay response. Because `K=B/T` grows, the ridge displacement
`tau=nu/K` at the fixed +120 kHz probe becomes smaller. Better zero-Doppler
delay resolution does not remove coupling; it changes its slope.

The code-length sweep holds chip duration and the seeded code prefix fixed.
More chips increase total coherent duration, narrowing the zero-delay Doppler
cut, while the delay mainlobe remains on the chip-duration scale. The plotted
peak sidelobe can move non-monotonically because code pattern matters as well
as length.

## Broken case: circular shift invents overlap

Propagation delay does not wrap the end of a pulse back to its beginning. A
linear shift must insert zeros. The broken calculation instead maps every
shifted index modulo the record length. For a constant rectangular pulse, this
leaves all samples overlapped at every delay, so even the most extreme plotted
delay has normalized magnitude one. The correct zero-filled overlap there is
only `1/N`.

Recovery restores the explicit overlap bounds, reconstructs the private
phase-code stream from seed 3401, and asserts exact equality of the code,
waveform, and complete ambiguity surface. The failure is a boundary-condition
error, not surprising Doppler tolerance.

## Assumptions and limiting cases

- The signals are finite, deterministic, unit-amplitude complex-baseband
  waveforms. Magnitude is normalized by energy; absolute received power is not
  modeled.
- Delay is sampled in `1/Fs = 0.1` microsecond steps. A denser plot would
  interpolate the display but would not add waveform bandwidth.
- Doppler uses the narrowband multiplicative phasor model. Wideband time
  scaling, acceleration, pulse-to-pulse processing, and range migration are
  outside this experiment.
- At the origin every nonzero waveform has normalized magnitude one. That
  fact alone says nothing about off-origin resolution or sidelobes.
- For a very short pulse, the rectangular delay cut is narrow but Doppler
  tolerance is broad. For a long pulse the directions reverse.
- For `B -> 0`, LFM approaches an unmodulated rectangular pulse and loses its
  narrow zero-Doppler delay response. Increasing bandwidth is bounded by the
  sample rate and analog system, not by plot resolution.
- A longer random code narrows its Doppler cut, but its exact delay sidelobes
  remain a property of the chosen sequence.
- The surfaces do not include noise, clutter, multipath, target fluctuation,
  propagation, detection thresholds, RF impairments, or antenna effects.

## Common interpretation mistakes

- A narrow zero-Doppler delay cut does not imply tolerance to every Doppler.
- The diagonal LFM ridge is coupling between two mismatch coordinates, not a
  target trajectory or a range-Doppler map of a scene.
- Ambiguity delay is replica mismatch. Converting it to monostatic range would
  use `Delta R = c*tau/2`; no range conversion is needed to compare waveforms.
- Normalized magnitude hides energy differences. It is appropriate for shape
  comparison but not a link-budget or detection-SNR result.
- Phase-code sidelobes are deterministic structure, not random noise.
- A circular correlation may be appropriate for a deliberately periodic
  signal model, but it is wrong for this isolated zero-extended pulse.
- A finer Doppler grid makes the picture smoother; it does not lengthen the
  coherent observation or improve physical Doppler discrimination.

## Dependencies and concept connection

P33 established that a matched-filter peak has width and sidelobes. P34 adds
the Doppler phasor explicitly and asks how that entire delay response changes
under simultaneous mismatch. It uses base MATLAB and keeps the defining sum,
zero-filled overlap, normalization, and resource bounds visible. P35 will add
pulse repetition and unambiguous-range aliasing; this single-pulse surface is
not yet a pulse-Doppler data cube.

Completion means you can point to the main lobe and explain which waveform is best for a chosen delay/Doppler requirement.
