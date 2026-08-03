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
When you reach a scaffolded module, implement it through its Portfolio Control
`P##` batch rather than allowing tutor mode to invent ungoverned content.
