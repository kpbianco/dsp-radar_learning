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
When you reach a scaffolded module, implement it through its Portfolio Control
`P##` batch rather than allowing tutor mode to invent ungoverned content.
