# P42 lesson: Create a Full Range-Doppler Map

Guiding question: **How do matched filtering and slow-time FFT combine to separate targets?**

## Physical model: one matrix, two clocks

A pulsed radar records samples during each listening interval and repeats that
measurement over many coherent pulses. In this lesson, matrix row (r) is a
fast-time sample and column (p) is a pulse:


\[
x[r,p].
\]

Fast time measures echo delay inside one pulse. Slow time measures phase change
from pulse to pulse. They are different clocks carrying different physics.
Figure 1 deliberately shows the raw matrix before either coordinate is turned
into a target location.

For target (q), the complex-baseband echo is modeled as

\[
x_q[r,p]=a_q\,s[r-d_q]\exp\!\left(j\phi_q+j2\pi f_{d,q}\frac{p}{f_{PRF}}\right),
\]

where (d_q\) is delay in samples and

\[
R_q=\frac{c\,d_q}{2F_s},\qquad
f_{d,q}=\frac{2v_q}{\lambda}.
\]

Positive radial velocity means approaching in this module, so it produces
positive Doppler frequency. The scene keeps range migration below one range
cell during the coherent processing interval (CPI); each target therefore
stays in one range neighborhood while its phase rotates across columns.

## Stage 1: match along fast time

The transmitted LFM samples are (s[m]). Their matched filter is the conjugate
time reverse

\[
h[m]=s^*[N_s-1-m].
\]

For each pulse column, the script evaluates the base-MATLAB convolution

\[
y[r,p]=\sum_m x[m,p]h[r-m].
\]

Only the row dimension is involved. At the correct delay the waveform phase
history aligns and adds; at other delays it mostly cancels. The convolution
contains a fixed (N_s-1) filter delay, so the script selects the aligned
samples before assigning the range axis. Figure 2 shows long raw echoes become
narrow range responses while their pulse-to-pulse complex phase remains.

The sample-grid spacing and waveform resolution are not the same:

\[
\Delta R_{sample}=\frac{c}{2F_s},\qquad
\Delta R_{resolution}\approx\frac{c}{2B}.
\]

Increasing sample rate makes a denser coordinate grid. Increasing waveform
bandwidth narrows the physical matched-filter response.

## Stage 2: transform along slow time

After range compression, hold one range row fixed. A moving target supplies a
complex tone across pulses. The Doppler transform is

\[
Z[r,k]=\sum_{p=0}^{N_p-1}w[p]y[r,p]
       \exp\!\left(-j2\pi\frac{kp}{N_p}\right).
\]

This operation is performed across matrix columns, MATLAB dimension 2. The
centered axes are

\[
f_k=\left(k-\frac{N_p}{2}\right)\frac{f_{PRF}}{N_p},\qquad
v_k=\frac{\lambda f_k}{2}.
\]

Figure 3 isolates the range shared by targets 1 and 2. Range compression alone
puts both in the same row; their different slow-time phase slopes create two
velocity peaks. In Figure 4, targets 2 and 3 share velocity but remain separate
because their matched-filter delays occupy different rows. This is the visible
answer to the guiding question: neither 1-D operation can perform both
separations, while their ordered 2-D combination can.

Stationary clutter uses the same complex coefficient on every pulse in this
idealized scene. It therefore concentrates near zero Doppler. White noise is
independent across fast and slow time and spreads across the map.

## Sweep 1: CPI length controls the Doppler grid

The first sweep holds waveform, PRF, scene, and window family fixed while
using 16, 32, then 64 pulses. Its FFT and velocity spacings are

\[
\Delta f_d=\frac{f_{PRF}}{N_p},\qquad
\Delta v=\frac{\lambda f_{PRF}}{2N_p}.
\]

The approximate CPI duration is (T_{CPI}=N_p/f_{PRF}). A longer CPI makes
the bins closer and helps distinguish nearby Dopplers. It does not narrow the
matched-filter range response because bandwidth did not change. Zero-padding
could make a smoother display, but it would not replace a longer coherent
observation.

## Sweep 2: windowing trades sidelobes for width

A rectangular slow-time window retains all samples at equal weight. Its narrow
mainlobe comes with prominent Doppler sidelobes. A Hann window tapers the CPI
ends, reducing discontinuity and sidelobes while widening the mainlobe. The
script divides each spectrum by the window sum so coherent gain does not
masquerade as target-strength change.

Figure 6 uses one deliberately fractional-bin tone to expose that tradeoff.
Its reported sidelobe metric excludes a fixed five-bin neighborhood around the
peak; it is an instructional comparison, not a universal radar specification.
Windowing does not change a target's true velocity, and lower sidelobes do not
mean improved resolution in every scene.

## Intentionally broken processing and recovery

The broken case applies `fft(...,1)` to the range-compressed matrix. Dimension
1 is fast time. Its output coordinate is fast-time frequency, while the other
axis remains pulse index. Labeling that result with range and velocity would be
a physical error even though MATLAB returns a perfectly finite matrix.

Recovery restores the Hann multiplication across columns and `fft(...,2)`.
The recovered complex map is compared sample for sample with the baseline.
This failure is useful because array size alone cannot prove that a matrix is a
range-Doppler map; the operations and axis meanings must agree.

## Assumptions, limiting cases, and model boundary

- Targets are nonfluctuating point scatterers over one CPI. Their integer
  sample delays remain fixed; acceleration and range migration are omitted.
- All target ranges are inside one unambiguous PRI and all Dopplers satisfy
  \(|f_d|<f_{PRF}/2\). Beyond those limits, peaks alias in range or velocity.
- If (B\to0), the range response approaches a long unmodulated-pulse
  response. If (N_p=1), there is no pulse history from which to estimate
  Doppler.
- If target Doppler lies exactly on an FFT bin, a rectangular window has no
  leakage in the ideal noiseless tone limit. Fractional-bin Doppler exposes the
  normal finite-CPI sidelobe pattern.
- If (v=0), the target and stationary clutter occupy zero Doppler and cannot
  be separated by velocity alone.
- The clutter is a finite set of coherent stationary scatterers with a mild
  range taper. It is not terrain-calibrated, compound-Gaussian, antenna-shaped,
  or a measured clutter spectrum.
- The map is normalized for visualization. It is not calibrated power, a
  detector, CFAR output, probability of detection, or operational target
  report. P43 begins fixed-threshold detection and P50 later applies 2-D CFAR.

## Common interpretation mistakes

- A bright map cell is not automatically a target; sidelobes, clutter, and
  noise also create energy.
- FFT bin spacing is not guaranteed two-target resolution, and sample spacing
  is not range resolution.
- `fftshift` centers the display; it does not create negative velocities. The
  sign comes from preserved complex slow-time phase.
- Applying a 2-D FFT blindly is not the processing chain. Range uses a known
  waveform correlation; Doppler uses a slow-time Fourier transform.
- Window comparisons must account for coherent gain and mainlobe width, not
  only the lowest visible sidelobe.
- Transposing a plot can make it look plausible while silently swapping the
  physical axes.

## Dependencies and connection

[P32](../32-perform-lfm-pulse-compression/) established LFM pulse compression,
[P36](../36-measure-doppler-from-pulse-to-pulse-phase/) established signed
slow-time Doppler, [P37](../37-build-a-pulse-doppler-data-matrix/) fixed the
matrix convention, and [P41](../41-model-ground-clutter-and-swerling-targets/)
separated clutter memory from white noise. P42 combines those permanent facts
into the input map used by later detection lessons.

The script requires base MATLAB only. It uses a private seed, bounded arrays,
and no external I/O, timer, worker, hardware, or persistent state.
