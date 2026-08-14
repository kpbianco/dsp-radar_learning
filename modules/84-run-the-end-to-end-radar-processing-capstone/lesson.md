# P84 lesson: the seams are the system

## Guiding question

Can I trace a target from waveform generation through detection and tracking without treating any stage as a black box?

The useful mental model is a chain of evidence. Each stage changes the form of
the information, but it cannot invent information discarded upstream. A bright
track is not proof that the waveform resolved two targets, and an empty CFAR
mask does not tell you whether the echo was absent, smeared by a wrong matched
filter, hidden by clutter, or rejected by the threshold.

## 1. Waveform and scene

The transmitted complex-baseband LFM pulse is

\[
s(t)=\exp\{j\pi (B/T)t^2\},\qquad |t|<T/2.
\]

Its instantaneous frequency is `(B/T)t`. A point target at range `R` produces
round-trip delay `tau=2R/c`; approach speed `v` produces
`f_D=2v/lambda`. In the experiment, positive velocity means approaching, so
its range evolves as `R(k)=R(0)-v k T_scan` even though its slow-time phase
rotates in the positive Doppler direction.

The nominal range resolution `c/(2B)` is different from range sample spacing
`c/(2fs)`. Sampling can put many display points across a response without
making two objects physically resolvable. Doppler-bin spacing is

\[
\Delta v=\frac{\lambda\,PRF}{2N_p}.
\]

The scene includes a stationary target, a moving target, a strong/weak pair at
the same Doppler, a step in stationary clutter power, and an echo-like receiver
spur with no target truth. The moving echo is faded before reception on scan 4;
the later coast is therefore a consequence of the scene, not a deleted report.

## 2. Receiver imperfection and calibration

Let `y=x+n` be the scene voltage plus receiver noise. The measured complex
sample is

\[
z=y+\epsilon y^*+d.
\]

The conjugate term creates an image; `d` creates center leakage. Because this
teaching model makes `epsilon` and `d` visible, calibration is the explicit
inverse

\[
\hat{y}=\frac{(z-d)-\epsilon(z-d)^*}{1-\epsilon^2}.
\]

Calibration removes the modeled image/DC terms, not the additive noise already
inside `y`. As `epsilon` tends to zero, the image disappears. When its magnitude approaches
one, the inverse becomes ill-conditioned; the controls reject that limit.

## 3. Pulse compression and range-Doppler processing

The matched-filter impulse response is not merely the waveform played
backward. It is the conjugate time reverse:

\[
h[m]=s^*[N_s-1-m].
\]

The script performs full linear convolution and removes exactly the known
filter delay. It then applies an explicit cosine slow-time window and computes
an FFT across pulse columns—not across range rows. The signed velocity axis
comes from the FFT frequency axis through `v=lambda f_D/2`.

With few pulses, velocity bins are coarse. At `|v| >= lambda PRF/4`, Doppler
aliases. A stationary target lies on the zero-Doppler clutter ridge, so
waveform energy alone does not guarantee separability.

## 4. Threshold, cluster, and score

For a rectangular 2-D CA-CFAR stencil with `N` training cells, the homogeneous
exponential-noise scale is

\[
\alpha=N(P_{fa}^{-1/N}-1),\qquad T=\alpha\frac{1}{N}\sum_{i=1}^N P_i.
\]

All averaging is in linear power. Range and Doppler border cells without a full
stencil are ineligible; they are not padded with zeros. This `Pfa` is a design
value for independent homogeneous exponential cells. Matched-filter
correlation, windowing, target sidelobes, and the clutter edge violate that
model, so the experiment labels its measured ratio an empirical false-cell
rate rather than proof that the requested `Pfa` was achieved.

One target response may cross threshold in several cells. An explicit
8-connected search groups those cells and uses positive threshold excess as a
centroid weight. One report can match at most one truth object. That rule is
essential beside the strong/weak pair: one merged component is not two
detections. The scorer retains all feasible truth/report assignment masks and
uses the maximum-cardinality one-to-one result, so `Pd` and false-report counts
do not depend on the order of truth entries.

## 5. Tracking is prediction plus accountable correction

The tracker state is range and range rate. It predicts
`R^- = R + Rdot*Tscan`, gates reports in range and measured Doppler, then uses
the same innovation to correct position and rate:

\[
R^+=R^-+\alpha e,\qquad \dot R^+=\dot R^-+(\beta/T)e.
\]

No accepted report means predict and coast, not silently reuse the previous
measurement. Truth enters only afterward to compute range RMSE. The declared
initial surveillance sector and positive-Doppler rule initiate the track
without consulting truth.

## Two controlled sweeps

1. The taper sweep blends rectangular and cosine matched replicas while
   retaining the same calibrated receiver record. Strong-target sidelobes can
   fall, but the mainlobe broadens and coherent gain changes; weak-neighbor
   visibility need not improve monotonically.
2. The `Pfa` sweep reuses one range-Doppler power map. Increasing requested
   `Pfa` lowers `alpha`, so threshold crossings can only be added. More reports
   may raise `Pd`, but false cells and false reports can also increase.

## Broken path and limiting cases

The broken matched filter reverses the LFM without conjugating it. Energy no
longer adds with the intended phase, so compression gain and downstream
detections change. Recovery uses the retained calibrated cube and the correct
replica; equality with the baseline is checked cell for cell.

Other useful limits:

- `B -> 0`: nominal range resolution becomes arbitrarily poor.
- target spacing below the compressed mainlobe: clustering can merge objects.
- smaller requested `Pfa`: the CFAR multiplier rises and weak targets are lost.
- guards narrower than a response: target energy contaminates its own training.
- `v=0`: target Doppler overlaps stationary clutter.
- no report: a bounded coast propagates state but adds no new evidence.
- wrong velocity sign: an approaching-target prediction walks away in range.

The experiment is deterministic synthetic analysis, not an operational radar
claim. Static repository checks cannot prove MATLAB execution, numerical
fidelity, figure rendering, real-time behavior, or educational effectiveness.
