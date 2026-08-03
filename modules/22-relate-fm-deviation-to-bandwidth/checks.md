# P22 Checks

## Guiding question

How does instantaneous frequency motion create an FM spectrum?

Use the figures and `results`; do not answer from MATLAB syntax.

## Observation and prediction checks

1. With `fc=3000 Hz`, `fm=100 Hz`, and `Delta_f=400 Hz`, predict the minimum
   and maximum instantaneous frequency before reading `results`.
   - Expected: 2600 Hz and 3400 Hz.
2. Where are sideband orders `n=-2`, `n=+1`, and `n=+5`?
   - Expected: 2800 Hz, 3100 Hz, and 3500 Hz.
3. Why does the phasor-magnitude plot stay at 1 V while the RF trace appears to
   bunch and spread?
   - Expected: FM changes angle rate/phase slope, not phasor length.
4. If deviation doubles at fixed `fm`, what stays fixed and what grows?
   - Expected: 100 Hz line spacing stays fixed; `beta`, important sideband
     order, and occupied width grow.
5. If `fm` doubles at fixed deviation, what changes?
   - Expected: line spacing doubles, `beta` halves, and Carson width increases.

## Interpretation checks

Correct each false statement:

- "`beta=4 Hz`." False: beta is dimensionless; deviation is 400 Hz.
- "Carson's 1 kHz result is an exact brick-wall edge." False: it is an
  occupied-bandwidth estimate for decreasing, theoretically infinite FM lines.
- "A weak carrier line means the FM amplitude collapsed." False: Bessel-like
  redistribution can move energy from the carrier into sidebands while phasor
  magnitude stays fixed.
- "Increasing deviation pushes adjacent lines farther apart." False: `fm`
  sets their spacing; deviation changes their significant order and weights.
- "A dense zero-padded FFT would prove a narrower physical bandwidth." False:
  display-grid density does not add observation time or change the waveform.

## Broken-case diagnosis and recovery

1. Why is the `fc=8000 Hz`, `Delta_f=5000 Hz` case invalid at 24 ksample/s?
   - Expected: its intended 13 kHz maximum exceeds 12 kHz Nyquist, so phase
     increments and spectrum alias.
2. Why can filtering after sampling not recover the intended upper excursion?
   - Expected: folding has already made distinct analog frequencies share the
     same sampled representation.
3. State one valid recovery.
   - Expected: to protect the stated Carson/98% target, use at least 27.2
     ksample/s for the 500 Hz guard (30 ksample/s demonstrated), or lower
     carrier, deviation, or message rate before sampling. This finite-power
     target does not make ideal sinusoidal FM strictly bandlimited.

## Contract and resource checks

- Invalid logical, complex, nonfinite, noncanonical, out-of-band, oversized
  sample/sweep/figure/storage controls must fail before random allocation, FFT,
  cleanup, or plotting.
- Each sweep has four cases and varies one named physical input.
- The experiment uses explicit `exp`, `cos`, phase difference, `fft`, and line
  power. It needs no modulation, communications, signal-processing, parallel,
  or hardware toolbox and performs no external I/O.
- Because this is a base MATLAB script, Ctrl+C may leave caller-workspace
  variables, partial P22 figures, and incomplete results. A full rerun is the
  bounded P22 recovery and reproduces the private seeded observation without
  changing the global RNG or `.learning/` progress; it cannot restore an
  overwritten pre-existing variable with the same name.

## Teach-back rubric

In two or three sentences, answer the guiding question. A complete answer must
connect phase slope to instantaneous frequency, explain why periodic motion
creates lines spaced by `fm`, distinguish deviation-driven sideband order from
message-frequency spacing, state that Carson's rule is approximate, and name
the Nyquist failure/recovery. Also state why amplitude remains constant while
spectral width changes strongly.
