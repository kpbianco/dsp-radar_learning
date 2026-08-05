# Start Here

1. Open this repository in Codex.
2. Say `start`.
3. Codex will select the first implemented incomplete module and follow its tutor walkthrough.
4. Run the MATLAB script when prompted and describe the indicated plot, not the code syntax.
5. Complete the two parameter changes and the deliberately broken case.
6. Give a two- or three-sentence teach-back before the module is marked complete.

Project 1 is the reference implementation. Project 2 is the next available
lesson after it. Project 3 is the next lesson after P02. Project 4 is the next lesson after P03.
Project 5 is the next lesson after P04.
Project 6 is the next lesson after P05.
Project 7 is the next lesson after P06.
Project 8 is the next lesson after P07.
Project 9 is the next lesson after P08.
Project 10 completes the first-phase sequence after P09.
Project 11 begins Phase 2 after P10 and makes the FFT frequency grid concrete.
Project 12 follows P11 and separates deterministic leakage from random noise.
Project 13 follows P12 and separates FFT display-grid density from true
finite-observation resolution.
Project 14 follows P13 and trades segment-duration frequency resolution for a
lower-variance Welch PSD estimate.
Project 15 follows P14 and uses an explicit spectrogram to trade window-duration
frequency visibility against transient timing while overlap controls report
density.
Project 16 follows P15 and forms an analytic signal explicitly to expose
envelope, phase, and instantaneous frequency while identifying low-amplitude
samples where phase is unreliable.
Project 17 follows P16 and performs explicit complex downconversion, preserving
signed difference frequency, relative phase, and real-input amplitude
bookkeeping while its low-pass FIR selects the desired translated copy.
Project 18 follows P17 and shows that I/Q rotation preserves positive/negative
frequency and side-of-LO while a real projection collapses conjugate directions
into the same cosine; it also exposes the complex-sampling Nyquist limit.
Project 19 follows P18 and maps DC offset, I/Q gain mismatch, and quadrature
error to center spikes, conjugate images, and distorted I/Q trajectories before
correcting mean, branch gain, and phase shear in stages.
Project 20 follows P19 and compares explicit peak-bin, interpolated-FFT, and
coherent phase-increment tone estimates across SNR and observation duration,
including wrapped-phase and low-coherence failure cases.
Project 21 follows P20 and begins Phase 3 by mapping single- and multitone
messages to symmetric AM sidebands, then contrasts envelope and coherent
recovery when over-modulation reverses the signed envelope.
Project 22 follows P21 and relates fixed-envelope phase-slope motion to an FM
sideband ladder, measured and Carson-style bandwidth, and the Nyquist limit.
Project 23 follows P22 and maps BPSK/QPSK bits to IQ geometry, then separates
noise-driven cluster spread from phase-driven rotation and decision-boundary
crossings.
Project 24 follows P23 and turns QPSK points into rectangular and RRC
waveforms, then exposes bandwidth, matched-filter, finite-span, eye-opening,
and symbol-timing tradeoffs.
Project 25 follows P24 and adds explicit delayed channel paths, connecting
frequency-selective fading to eye closure and constellation ISI before
contrasting ZF noise enhancement with MMSE regularization near a deep null.
Project 26 follows P25 and learns an unknown interference coupling with an
explicit LMS update, then exposes step-size convergence, reference-quality,
path-change reacquisition, and guarded-instability behavior.
Project 27 follows P26 and turns repeated BPSK matched-filter decisions into a
statistical experiment, showing trial-count uncertainty, Eb/N0 behavior, the
failure of reused noise, and deterministic independent-trial recovery.
Project 28 follows P27 and closes Phase 3 by sweeping a known-pulse detector
threshold into an ROC, comparing amplitude-estimator bias and variance with a
known-model CRLB across SNR, and exposing detected-only selection bias.
Project 29 follows P28 and begins Phase 4 by applying the monostatic radar
range equation, connecting two-way `R^-4` spreading to noise-floor margin,
one-variable budget changes, and the 16-times-power cost of doubling range.
Project 30 follows P29 by inserting continuous fractional echo delay before
sampling, locating the echo with explicit correlation, converting lag through
`R = c*tau/2`, and contrasting sample-grid precision with two-target peak
separation.
Project 31 follows P30 by holding scene geometry or waveform bandwidth fixed in
turn, measuring the matched-response width, and showing that a precise
single-target estimate does not imply that a close pair is resolvable.
Project 32 follows P31 by encoding a long pulse with a linear frequency sweep,
compressing delayed echoes through explicit matched filtering, and separating
bandwidth-controlled response width from duration-controlled coherent energy.
Project 33 follows P32 by placing a weak target under a strong target's
compressed sidelobes, then trading receive-weighting sidelobe suppression
against mainlobe width and output SNR at several target separations.
Project 34 follows P33 by evaluating explicit zero-filled delay and Doppler
mismatch for rectangular, LFM, and phase-coded pulses, then connecting pulse
duration, swept bandwidth, chip/code length, sidelobes, and LFM coupling to the
visible ambiguity surface.
Project 35 follows P34 by repeating transmissions at a fixed PRF, folding a
distant target's round-trip delay into one listening interval, sweeping PRF
and true range, and exposing the missing transmit-pulse identity behind an
apparently short false range.
Project 36 follows P35 by sampling a coherent target range bin once per pulse,
turning signed radial motion into I/Q rotation, phase slope, and a Doppler FFT,
then separating carrier sensitivity and pulse-count resolution from PRF
aliasing.
Project 37 follows P36 by stacking fast-time range samples into rows and
coherent pulse looks into columns, then changing range and velocity separately
to show which matrix dimension carries each physical effect.
Project 38 follows P37 by differencing coherent pulse columns with transparent
two-pulse and three-pulse cancellers, comparing the stationary-clutter null
against slow-target loss and noise gain, and exposing the wrong-axis failure.
Project 39 follows P38 by mapping the two-pulse response to radial velocity,
marking each PRF's blind-speed grid, and recovering nonzero blind targets with
separately processed staggered-PRF dwells and noncoherent max/OR fusion.
Project 40 follows P39 by comparing phase-aligned complex addition with
phase-insensitive power accumulation, then exposing coherent loss from phase
jitter and recovering it with a valid pulse-by-pulse phase reference.
Project 41 follows P40 by separating stationary white noise from
range-dependent correlated ground clutter, comparing nonfluctuating and
Swerling I-IV target powers at equal ensemble-average SNR, and exposing the
range bias caused by a false global-background assumption.
Project 42 follows P41 and closes Phase 4 by applying an explicit LFM matched
filter down fast-time columns, then a windowed FFT across slow-time rows to
separate targets in range and signed velocity while exposing CPI, window, and
wrong-axis behavior.
Project 43 follows P42 and begins Phase 5 by applying one explicit fixed
amplitude threshold, then changing noise RMS and a clutter pedestal separately
to expose false-alarm and missed-detection drift without hidden retuning.
Project 44 follows P43 by sweeping a normalized matched-filter threshold into
empirical ROC curves at several SNRs, pricing one low-`Pfa` operating point at
scan scale, and exposing finite-trial and tune-on-test false confidence.
Project 45 follows P44 by estimating local square-law background power from
explicit guarded training cells, scaling it for requested `Pfa`, excluding
unsupported edges, and showing that uniform scene-power changes move the
threshold without changing normalized decisions.
Project 46 follows P45 by varying guard and training geometry around an
extended target and a gradual background transition, exposing self-masking,
estimate variance, loss of locality, and a contaminated-reference miss before
a bounded geometry recovery.
Project 47 follows P46 by comparing a known-noise square-law detector with
finite-training CA-CFAR at equal `Pfa` and `Pd`, measuring the horizontal SNR
penalty while training count and requested false-alarm probability change, and
exposing the unfair gain from a miscalibrated adaptive multiplier.
Project 48 follows P47 by separating leading and lagging reference means at a
clutter edge, comparing calibrated greatest-of and smallest-of thresholds, and
showing why edge false-alarm protection and one-sided target contamination
favor different selectors.
Project 49 follows P48 by sorting the combined training powers, selecting and
separately calibrating an ascending order statistic, and comparing it with the
CA mean as nearby interfering targets change in count and strength; it exposes
the finite `N-k` outlier capacity and the failure caused by changing rank
without recalibration.
Project 50 follows P49 by sliding a rectangular guarded CA-CFAR training
annulus across the range-Doppler map, changing range and Doppler extents one at
a time, and distinguishing calibrated interior decisions from an intentionally
broken zero-padded boundary policy.
Project 51 follows P50 by placing CA, GO, SO, and rank-18 OS CFAR on one
combined clutter-edge, sidelobe, weak-neighbor, crowded-target, and nonuniform
noise scene, calibrating each statistic to the same nominal homogeneous Pfa,
and tracing every major mask disagreement back to its training-cell contents.
Project 52 follows P51 by defining one valid noise-only CUT decision per Monte
Carlo trial, measuring false alarms with Wilson intervals, sweeping requested
Pfa and training count, and separating finite-N scaling errors from correlated
and heavy-tailed model mismatch.
Project 53 follows P52 and begins Phase 6 by turning extended range-Doppler
threshold blobs into one report per accepted 8-connected component, using
explicit local maxima, minimum-size filtering, and excess-power centroids while
exposing the false-report failure of treating every peak as a target.
Project 54 follows P53 by predicting scalar position from estimated velocity,
correcting position and velocity from the same innovation, coasting through
missing reports, and using independent alpha and beta sweeps to make the
smoothing-versus-maneuver-lag tradeoff visible.
Project 55 follows P54 by replacing fixed gains with explicit covariance
prediction and correction, then varying Q and R independently to show how
model and measurement uncertainty set Kalman trust and expose overconfidence.
Project 56 follows P55 by replacing the linear report with an explicit
range-bearing prediction and local Jacobian. It wraps angular innovations,
shows range-dependent tangential covariance, and exposes the branch-cut failure
caused by ordinary angle subtraction.
Project 57 follows P56 by comparing each prediction with every report through
its innovation covariance, gating on dimensionless Mahalanobis distance, and
enforcing one-to-one greedy nearest-neighbor links before any update. It shows
why ungated Euclidean proximity can prefer clutter across a narrow uncertainty
axis.
Project 58 follows P57 by turning the associated report stream into explicit
tentative, confirmed, coasting, and deletion states. A 3-of-4 confirmation
window rejects isolated false alarms, a two-scan coast preserves one target ID
through a short dropout, and separate sweeps expose declaration latency versus
false promotion and dropout tolerance versus stale-state retention.
Project 59 follows P58 by holding two confirmed tracks alive through an exact
crossing, showing how position-only greedy association can exchange their
histories, then adding a normalized velocity feature and sweeping measurement
noise, update interval, and closest approach. Its broken path lets both tracks
reuse one report before deterministic one-to-one recovery.
Project 60 follows P59 by mixing explicit straight-motion and
persistent-acceleration Kalman filters for one maneuvering target. Innovation
likelihood moves mode probability, two sweeps expose maneuver-strength and
persistence tradeoffs, and a zero-support broken mode is recovered exactly on
the same reports.
Project 61 follows P60 and begins Phase 7 by sampling one narrowband plane wave
across an explicit ULA. It connects broadside-referenced angle to geometric
delay and spatial phase slope, separates spacing from carrier-frequency
sensitivity, and recovers from an exact spatial-alias failure by restoring
half-wavelength spacing.
Project 62 follows P61 by summing explicit ULA element phasors into normalized
linear and dB patterns. It measures beamwidth and sidelobes, varies aperture
and spacing independently, compares uniform and Hamming illumination, and
removes an exact equal-height grating lobe by restoring half-wavelength
spatial sampling.
Project 63 follows P62 by applying fixed conjugate ULA steering weights to
noisy two-source array data. It compares one look with covariance averaging,
varies source separation, array size, SNR, and snapshot count independently,
and recovers an exact mirrored-angle failure caused by reversing the steering
phase convention.
When you reach a scaffolded module, implement it through its Portfolio Control
`P##` batch rather than allowing tutor mode to invent ungoverned content.
