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
Every module folder already contains its complete curriculum brief and
ready-to-paste AI prompt. Projects 1–21 have completed their separate governed
implementation batches. Projects 22–84 wait for their own
MATLAB experiment, lesson, walkthrough, checks, validation, and evidence.

Historical compatibility checkpoints recorded that Projects 6–84 intentionally wait
for separate batches after P05, Projects 7–84 followed that rule after P06, and
Projects 8–84 followed it after P07. Projects 9–84 were the corresponding
checkpoint after P08. Those statements describe their respective checkpoints;
the current implementation frontier is P21.

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
