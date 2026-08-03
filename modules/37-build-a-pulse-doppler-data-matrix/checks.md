# P37 checks: Build a Pulse-Doppler Data Matrix

Guiding question: **What are fast time and slow time in a radar data block?**

Use the figures and printed metrics. These checks test physical interpretation,
not MATLAB syntax.

## Observation checks

1. What are the baseline matrix dimensions, and what does each dimension mean?
2. Which rows contain the three target peaks, and what measured ranges do they
   represent?
3. Which target row has flat, positive-slope, and negative-slope phase across
   pulses?
4. Why is velocity sign difficult to read from the magnitude image alone?

Passing observation: you identify 256 fast-time/range rows by 32 slow-time
pulse columns; rows near 61, 121, and 161; the stationary, approaching, and
receding phase slopes; and the missing complex angle in a magnitude view.

## Prediction checks

1. If target range increases while velocity stays fixed, which matrix
   coordinate changes?
2. If velocity reverses while range stays fixed, what happens to the target
   row, ideal magnitude, and phase slope?
3. If sample rate doubles without changing waveform bandwidth, what happens to
   range-grid spacing and true range resolution?
4. If pulse count doubles at fixed sample rate and PRF, which dimension grows,
   and which spacings remain unchanged?

Passing prediction: range moves the fast-time row; velocity reverses only the
slow-time phase slope in this fixed-range model; range-grid spacing halves but
waveform resolution is not automatically improved; and more pulses add
columns without changing fast-time spacing or PRI.

## Interpretation checks

1. Connect `n_k = round((2 R_k/c) f_s)` to a matrix row.
2. Connect `exp(j 2 pi f_d p/PRF)` to samples across pulse columns.
3. Explain why a matrix magnitude plot can show range but hide signed Doppler.
4. Distinguish fast-time sample spacing from waveform range resolution.
5. Explain why orientation is a storage convention but consistent axis labels
   and indexing are an invariant.

Passing interpretation: you mention two-way delay, coherent phase per PRI,
loss of complex angle, sample-grid quantization versus resolution, and the
declared fast-time-row/slow-time-column convention.

## Failure and recovery checks

1. Did the `+12 m/s` target stop when magnitude-only processing moved its
   spectrum toward zero Doppler?
2. What information did `abs(data_matrix)` preserve and discard?
3. What exact state does the private-seed recovery reconstruct?
4. How would a target migrating through range cells violate the fixed-row
   model?

Passing recovery: you reject the false stationary interpretation, preserve
range strength while identifying phase as lost, restore the exact complex
matrix, and explain that migration spreads one target across rows during the
dwell. A clean rerun is the rollback and recovery path.

## Compatibility, isolation, and resource checks

- Confirm controls are finite and consistent before matrix allocation.
- Confirm at most 512 fast-time samples, 128 pulses, 6 targets, 7 sweep cases,
  6 figure groups, and 1,000,000 estimated stored numeric values.
- Confirm the base MATLAB path exposes delay-to-row mapping, the target outer
  products, adjacent phase, axes, and FFT without a radar toolbox black box.
- Confirm private random streams, no background worker or timer, no network or
  external transaction, no global random stream mutation, and no `.learning/`
  write.
- Confirm only figures tagged `P37` are closed and Ctrl+C plus a clean rerun is
  sufficient cancellation and recovery.
- Confirm the synthetic range-resolved matrix is not hardware, HIL, field,
  real-time, deployment, production, or operational-radar evidence.

## Completion checklist

- [ ] I can state which matrix dimension is fast time and which is slow time.
- [ ] I can convert target range to a fast-time row and explain quantization.
- [ ] I can trace one row across pulses as a slow-time complex sinusoid.
- [ ] I can predict the separate effects of range and velocity changes.
- [ ] I can distinguish magnitude visibility from coherent Doppler phase.
- [ ] I can diagnose the magnitude-only failure and recover complex data.

## Short teach-back rubric

Give two or three sentences containing all three ideas:

1. Fast time samples echo delay after each pulse, so a target's range selects a
   row through `n = round((2R/c) f_s)`.
2. Slow time revisits that row once per PRI, so velocity appears as complex
   phase progression across pulse columns.
3. Magnitude preserves range energy but discards signed phase history, so a
   coherent complex matrix must be retained for Doppler processing.

Completion means you can trace one target through raw data to its range bin and slow-time sinusoid. Personal completion is recorded only after this teach-back through the learner CLI under ignored `.learning/` state.
