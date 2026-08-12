# DSP & Radar Learning Lab

An interactive, MATLAB-first curriculum for learning DSP and radar through 84 visual experiments. The repository is designed to work in two distinct modes:

- **Tutor mode:** Codex walks you through an already implemented module one observation at a time.
- **Build mode:** Portfolio Control activates one governed batch that implements the next module without silently changing the rest of the curriculum.

The curriculum progresses from sampled sinusoids and FFT intuition through matched filtering, pulse-Doppler processing, CFAR, tracking, arrays, FMCW, SAR, passive radar, and STAP.

## Start learning

Open Codex in this repository and say:

```text
start
```

The repository instructions make `start` run the local learner CLI and begin the tutor protocol. You can also be explicit:

```text
start 17
continue
show status
```

From a shell:

```bash
./bin/learn start
./bin/learn start 17
./bin/learn status
./bin/learn list
```

Project 1 is the initial reference lesson. Project 2 is now implemented, and
Project 3 is now implemented as the latest lesson from its batch.
Project 4 is now implemented as the latest lesson from its batch.
Project 5 is now the latest implemented lesson from its own batch.
Project 6 is now the latest implemented lesson from its own batch.
Project 7 is the latest implemented lesson prior to P08.
Project 8 is the latest implemented lesson before P09 and is its prerequisite.
Project 9 is the latest implemented lesson before P10 and is its prerequisite.
Project 10 completes Phase 1 after P09.
Project 11 is implemented and begins Phase 2 with the FFT bin-frequency map.
Project 12 separates deterministic finite-record leakage from random noise and
compares five explicit window tradeoffs after P11.
Project 13 proves that zero-padding densifies the displayed FFT grid without
narrowing the finite-record response, then compares a four-times-longer record.
Project 14 compares one full-record periodogram with explicit Welch averaging,
including segment-length, overlap, repeated-seed, and averaging-domain effects.
Project 15 builds an explicit short-time Fourier transform and compares window
duration, overlap, transient capture, close-frequency visibility, and the
zero-padding resolution trap.
Project 16 constructs the analytic signal with an explicit FFT Hilbert mask,
then exposes envelope, unwrapped phase, instantaneous frequency, and the
low-amplitude limit where phase-derived frequency becomes unreliable.
Project 17 multiplies a real passband tone by an explicit complex oscillator,
builds its low-pass FIR by hand, preserves signed LO-offset rotation and phase,
and exposes real-input mixer gain plus wrong-side conjugate selection.
Project 18 contrasts conjugate positive/negative complex tones with their
identical real projections, compares real and complex side-of-LO
downconversion, and exposes signed aliasing plus the failure caused by
discarding Q.
Project 19 injects DC offset, unequal I/Q gains, and quadrature-axis error,
then diagnoses their center/image/ellipse signatures and corrects mean, branch
scale, and phase shear in explicit stages.
Project 20 estimates fractional-bin tone frequency and initial phase with
peak-bin, interpolated-FFT, and coherent phase-increment methods, then maps
their bias and spread across SNR and observation duration and rejects
low-coherence estimates.
Project 21 begins Phase 3 by constructing conventional AM explicitly, mapping
single- and multitone baseband components to symmetric carrier sidebands, and
showing why over-modulation folds envelope recovery while coherent detection
retains sign.
Project 22 constructs sinusoidal FM from an explicit phase law, connects phase
slope to instantaneous frequency, compares 98%-occupied line power with
Carson's bandwidth estimate, and exposes Nyquist folding when the intended
frequency excursion exceeds the sample-rate limit.
Project 23 maps seeded bits explicitly to unit-energy BPSK and QPSK points,
shows noise spread and carrier-phase rotation against fixed IQ decision
boundaries, compares bit errors across SNR and phase sweeps, and recovers a
high-SNR phase-reference failure by exact derotation.
Project 24 shapes seeded QPSK symbols with explicit rectangular and
root-raised-cosine pulses, compares time and spectral containment, forms the
conjugate time-reversed matched filter, sweeps roll-off and finite span, and
breaks then recovers symbol timing.
Project 25 passes that pulse-shaped QPSK waveform through explicit delayed FIR
paths, exposes eye closure, constellation ISI, and frequency-selective fading,
then compares causal ZF inversion with regularized MMSE recovery at a deep
spectral null.
Project 26 uses an explicit sample-by-sample LMS predictor to learn an unknown
reference-to-primary FIR coupling, shows coefficient and residual-power
reacquisition after a midpoint path change, separates step-size behavior from
reference quality, and bounds an intentionally unstable update before a clean
deterministic recovery.
Project 27 sends seeded BPSK pulses through independent AWGN trials, forms the
matched-filter decision explicitly, tracks BER with Wilson uncertainty, sweeps
trial count and Eb/N0, and exposes false certainty from repeating one lucky
noise realization before an exact independent-trial recovery.
Project 28 closes Phase 3 with independent target-absent and target-present
known-pulse trials, an explicit matched-filter ROC threshold sweep, an
amplitude-estimator SNR/CRLB sweep, and a detected-only selection-bias failure
followed by deterministic all-trial recovery.
Project 29 begins Phase 4 with the explicit monostatic radar range equation,
thermal-noise and required-SNR margins, RCS/frequency/transmit-power sweeps,
one-at-a-time budget sensitivities, and an anchored inverse-square failure that
recovers the two-way fourth-power range law.
Project 30 sends a finite pulse through explicit zero-extended fractional
delay, locates echoes with lag-by-lag correlation, converts round-trip time to
`c*tau/2` range, sweeps sample rate and fractional delay, separates merged from
visible two-target peaks, and recovers the factor-of-two ranging failure.
Project 31 separates bandwidth-driven two-target resolution from single-target
accuracy using an explicit Gaussian-envelope matched filter, measured response
width, bandwidth and spacing sweeps, SNR-dependent error metrics, and a broken
dense-display peak rule that recovers only when physical bandwidth increases.
Project 32 builds a complex-baseband LFM pulse from its phase law, inserts two
overlapping long echoes, compresses them with an explicit conjugate
time-reversed matched-filter sum, separates bandwidth-controlled width from
duration-controlled energy, and recovers from a mismatched chirp-rate replica.
Project 33 places a weak echo beneath a strong target's LFM sidelobe, constructs
cosine receive weighting explicitly, measures sidelobe, mainlobe-width, SNR,
and visibility tradeoffs, and exposes why lowest-PSLR weighting can fail for a
target inside the widened mainlobe.
Project 34 evaluates the normalized narrowband ambiguity sum explicitly for
equal-duration rectangular, LFM, and seeded phase-coded pulses, compares joint
delay-Doppler surfaces and cuts, sweeps duration, bandwidth, and code length,
and exposes false wraparound response from a circular-delay model.
Project 35 repeats pulses at a fixed PRF, follows an old echo across newer
transmissions, folds its round-trip delay into one listening interval with an
explicit quotient and remainder, sweeps PRF and true range, and rejects a
broken answer that relies on an unavailable transmit-pulse label.
Project 36 samples one complex range bin across coherent pulses, connects
signed radial velocity to pulse-to-pulse phase and a slow-time FFT, sweeps
velocity, carrier, and coherent pulse count, and exposes why magnitude-only
processing loses Doppler sign.
Project 37 arranges range-resolved complex samples as fast-time rows by
slow-time pulse columns, traces independent targets through range and phase,
sweeps range and velocity separately, and exposes why magnitude alone cannot
carry coherent Doppler history.
Project 38 applies explicit first and second differences across those coherent
pulse columns, measures stationary-clutter rejection, moving-target response,
and noise gain, and exposes why differencing range rows is not MTI.
Project 39 maps the two-pulse response into radial velocity, marks the blind
speeds for two PRFs, and shows why separately processed staggered-PRF dwells
recover nonzero blind targets only when their null grids differ.
Project 40 aligns predictable pulse phase before complex addition, contrasts
its pulse-count gain with an explicit phase-insensitive power statistic, and
shows how phase jitter removes coherent benefit until a valid phase reference
is restored.
Project 41 constructs an explicit range- and slow-time-correlated clutter field,
compares nonfluctuating and Swerling I-IV target powers at equal ensemble-average
SNR, and shows why a global white-background threshold becomes range-biased
until the known local background scale is restored.
Project 42 closes Phase 4 by compressing coherent LFM pulse columns into range,
windowing each range row across slow time, and forming a signed range-Doppler
map that separates targets sharing range or velocity while exposing CPI,
window, and wrong-axis tradeoffs.
Project 43 begins Phase 5 with an explicit one-sided Gaussian amplitude
detector, holds one native-unit threshold fixed while noise RMS and a clutter
pedestal change, and exposes hidden background normalization as adaptation
rather than fixed-threshold behavior.
Project 44 forms independent normalized matched-filter H0/H1 banks, sweeps one
threshold into empirical ROC curves at several SNRs, marks a low-`Pfa`
operating point and its million-cell alarm burden, and exposes finite-trial and
tune-on-test false confidence before deterministic recovery.
Project 45 applies an explicit square-law CA-CFAR stencil to a slowly varying
range background, derives its finite-training-cell exponential-noise scale
factor, excludes guards and edge CUTs, and exposes exact scene-scale adaptation
plus the failure caused by averaging power in dB.
Project 46 gives a strong target an explicit finite mainlobe and sidelobes,
sweeps guard width to expose self-masking, sweeps training count to separate
estimate roughness from locality error, and recovers a weaker CUT from one
known contaminated reference by changing the visible stencil geometry.
Project 47 compares a fixed known-noise square-law threshold with finite-N
CA-CFAR on shared homogeneous Monte Carlo trials, measures extra required SNR
at equal `Pd` and `Pfa`, sweeps training count and false-alarm stringency, and
rejects an apparently low-loss detector that quietly overspends false alarms.
Project 48 forms separate leading and lagging square-law reference means at an
abrupt clutter step, calibrates GO and SO independently at equal homogeneous
`Pfa`, sweeps clutter contrast and one-sided target contamination, and exposes
both the high-side SO false-alarm cost and the GO masking cost.
Project 49 sorts all square-law training powers and selects a separately
calibrated ascending rank, compares that OS-CFAR threshold with CA-CFAR while
nearby targets vary in count and strength, and exposes both the finite `N-k`
high-outlier capacity and the false-alarm failure from reusing a multiplier
after changing rank.
Project 50 slides an explicit rectangular CA-CFAR annulus across a seeded
range-Doppler power map, varies range and Doppler training widths independently,
and exposes the invalid edge detections created by zero-padding missing
reference cells before recovering a full-stencil no-decision border.
Project 51 combines a clutter edge, explicit strong-target sidelobes, weak
neighbors, crowded targets, and a smooth noise swell, then compares separately
calibrated CA, GO, SO, and rank-18 OS masks while classifying disagreements from
their training-cell contents and exposing the unfair shared-alpha shortcut.
Project 52 closes Phase 5 by counting valid noise-only CA-CFAR decisions across
seeded Monte Carlo trials, attaching Wilson intervals, sweeping requested Pfa
and training count, and exposing correlated, heavy-tailed, and miscalibrated
departures from the homogeneous exponential model.
Project 53 begins Phase 6 by selecting deterministic local maxima, explicitly
grouping 8-connected threshold cells, filtering small nuisance components, and
forming excess-power weighted range/velocity reports with strength, extent,
and clearly uncalibrated shape-uncertainty fields; a peak-only broken path shows
why local maxima are not yet physical target reports.
Project 54 follows P53 by feeding one already-associated noisy scalar position
report into an explicit fixed-gain alpha-beta predictor. It contrasts position
smoothing with velocity-change lag, coasts through bounded report dropouts,
sweeps alpha and beta independently, and exposes the beta-zero failure that
cannot learn target velocity.
Project 55 follows P54 by propagating position, velocity, and covariance through
an explicit nearly-constant-velocity Kalman filter. It reuses one seeded report
record while sweeping Q and R independently, plots state and innovation
uncertainty with time-varying gains, and exposes separate under-Q and under-R
overconfidence before deterministic recovery.
Project 56 follows P55 by mapping range-bearing reports into Cartesian
corrections with an explicit nonlinear measurement prediction and Jacobian. It
wraps bearing innovations at the `+/-pi` branch cut, visualizes rotating
covariance ellipses, sweeps bearing trust and range-dependent tangential error,
and recovers from deliberately unwrapped angle subtraction.
Project 57 follows P56 by testing every predicted track against every detection
with explicit innovation covariances and squared Mahalanobis distances. It
gates implausible pairs, enforces one-to-one greedy nearest-neighbor assignment,
sweeps gate threshold and covariance scale, and recovers from an ungated
Euclidean clutter assignment.
Project 58 follows P57 by converting associated hit/miss histories into an
explicit track lifecycle. It initiates tentative hypotheses, requires M-of-N
evidence for confirmation, coasts confirmed tracks through bounded dropouts,
deletes stale state, sweeps confirmation and coast policy independently, and
exposes the false-track accumulation caused by immediate confirmation without
practical deletion.
Project 59 follows P58 by driving two established equal-speed tracks through a
crossing, exposing a persistent identity exchange from explicit position-only
greedy association, and adding a normalized velocity feature that lowers the
failure rate across position-noise, update-interval, and closest-approach
sweeps. An independent-nearest broken path reuses one report before exact
one-to-one recovery on the same arrays.
Project 60 follows P59 with an explicit two-model IMM for one target that
alternates between straight motion and acceleration bursts. It exposes state
and covariance interaction, innovation likelihoods, mode probabilities, and
combined estimates; compares against a poorly matched fixed straight model;
sweeps maneuver strength and mode persistence; and recovers exactly from a
zero-support mode lockout on unchanged reports.
Project 61 follows P60 and begins Phase 7 by turning a one-way far-field path
difference into an explicit spatial phase slope across a uniform linear array.
It infers an unambiguous broadside-referenced angle, sweeps angle, physical
spacing, and carrier frequency, and exposes an exact spatial alias before
recovering the source direction with half-wavelength spacing.
Project 62 follows P61 by coherently adding those spatial phases into an
explicit ULA array factor. It measures half-power and first-null beamwidths and
peak sidelobes, sweeps element count and spacing, exposes the Hamming
sidelobe-versus-beamwidth trade, and recovers from an exact equal-height
grating lobe by restoring half-wavelength spacing.
Project 63 follows P62 by applying explicit conjugate steering weights to two
noisy narrowband sources, proving direct snapshot-power averaging equals the
sample-covariance quadratic form, and separating aperture-limited resolution
from SNR- and snapshot-limited scan reliability. Source-separation, array-size,
SNR, and snapshot sweeps lead to an exact wrong-sign mirrored scan that
recovers on unchanged data with the consistent Hermitian convention.
Project 64 follows P63 by phase-aligning two symmetrically squinted receive
beams, forming explicit sum and difference voltages, and calibrating their
signed ratio over a local boresight sector. Beam-squint and receiver-SNR sweeps
separate comparator sensitivity from random precision, while a right-channel
gain mismatch creates a false boresight angle that recovers on unchanged data
with the known inverse calibration.
Project 65 follows P64 by estimating the spatial sample covariance and solving
the explicitly normalized MVDR/Capon weights. It compares a fixed conventional
beam with a data-dependent interference null, varies snapshot count and
diagonal loading independently, refuses a singular sample-starved solve, and
recovers on unchanged data while separating robustness from steering-model
correction.
Project 66 follows P65 by sorting the sample-covariance eigensystem and forming
an explicit MUSIC noise-subspace pseudospectrum. It resolves a reviewed close
pair that remains merged in a conventional Bartlett scan, varies source
spacing, SNR, snapshot evidence, and assumed source count independently, then
recovers a coherent-source rank collapse by spatially smoothing the unchanged
sensor record.
Project 67 follows P66 by applying seeded per-element gain, phase, and position
errors plus explicit banded mutual coupling to one deterministic ULA record.
It compares nominal Bartlett, loaded Capon, and MUSIC processing before and
after a known-source composite channel calibration, scales a fixed channel
error realization, sweeps coupling alone, and recovers from an incorrect
broadside calibration reference on unchanged pilot and operational data.
Every module folder already contains its complete curriculum brief and
ready-to-paste AI prompt. Projects 1–67 have completed their separate governed
implementation batches. Projects 68–84 wait for their own
MATLAB experiment, lesson, walkthrough, checks, validation, and evidence.

Historical compatibility checkpoints recorded that Projects 6–84 intentionally wait
for separate batches after P05, Projects 7–84 followed that rule after P06, and
Projects 8–84 followed it after P07. Projects 9–84 were the corresponding
checkpoint after P08. Those statements describe their respective checkpoints;
the current implementation frontier is P67.

## Module layout

```text
modules/01-build-a-sinusoid-and-a-complex-phasor/
├── README.md          # question, experiment, procedure, concept, completion
├── experiment.m       # added when the module is implemented
├── lesson.md          # added when the module is implemented
├── walkthrough.md     # added when the module is implemented
└── checks.md          # added when the module is implemented
```

## Implement the next module

This repository is governed by `kpbianco/portfolio-control`. Once the companion control-plane PR is merged and its submodule is initialized:

```bash
portfolio status dsp-radar-learning
portfolio go dsp-radar-learning --max-batches 1
```

Each `P##` batch may edit only its own module plus shared harness files explicitly named by the batch contract. A module is not considered implemented merely because a script exists: it must include a visual experiment, concept explanation, guided parameter sweeps, a deliberately broken case, interpretation checks, deterministic validation, and retained evidence.

## Verify the repository

```bash
./scripts/agent-verify.sh
```

The default CI verifies curriculum completeness, folder identity, tutor CLI behavior, and static contracts. It does **not** claim that MATLAB executed unless named MATLAB or compatible runtime evidence is retained separately.
