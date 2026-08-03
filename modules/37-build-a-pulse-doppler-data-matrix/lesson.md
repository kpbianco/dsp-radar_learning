# P37 lesson: Two Clocks Make One Radar Matrix

## Guiding question

What are fast time and slow time in a radar data block?

## The physical picture

A pulsed radar uses two clocks at once. After one pulse is transmitted, the
receiver samples rapidly while echoes arrive. That **fast-time** coordinate
measures delay within the listening interval. The radar then transmits again
and repeats the same fast-time sampling pattern. The repeat number is
**slow time**.

Place one receive record in each matrix column. A row then holds the same
delay cell from every pulse:

```text
                    slow time: pulse index p ->
fast time n       X[n,0]  X[n,1]  X[n,2]  ...
    |              X[n+1,0] ...
    v
delay / range
```

P35 established that delay inside a PRI maps to apparent range. P36 examined
one coherent range cell across pulses. P37 puts all those range cells beside
one another so both coordinates remain explicit.

## One target in two dimensions

For target `k`, the round-trip delay and corresponding row are

```text
tau_k = 2 R_k / c,
n_k   = round(tau_k f_s).
```

With zero-based fast-time index `n`, row `n_k` reports approximately

```text
R_hat = n_k c / (2 f_s).
```

The spacing between adjacent range samples is `c/(2 f_s)`. This is sample-grid
spacing, not necessarily waveform range resolution; P31 separated those two
ideas.

Radial velocity produces monostatic Doppler

```text
lambda = c/f_c,
f_d,k  = 2 v_k/lambda.
```

This module defines positive velocity as approaching. At pulse index `p`, one
ideal target contributes

```text
X_k[n,p] = A_k g[n-n_k]
           exp(j(phi_k + 2 pi f_d,k p/PRF)).
```

The range response `g` spreads an ideal return over a few neighboring samples.
Its center stays at the same row in this no-migration model. Across columns,
the complex angle advances by `2*pi*f_d,k/PRF` per pulse. Summing the targets
and adding complex noise creates the full matrix.

## Read the axes without swapping them

- Hold pulse index fixed and move down a column: you are inspecting one
  receive record in fast time. Echo delay creates peaks at target rows.
- Hold range row fixed and move across columns: you are revisiting one delay
  cell in slow time. Coherent phase evolution contains Doppler.
- A magnitude image emphasizes where energy sits in range, but a constant-
  amplitude moving target can have nearly constant magnitude across columns.
  Its motion is in complex phase, not necessarily in brightness.

The orientation is a convention, but it must be declared and used consistently.
Some systems store pulses in rows. Transposing is harmless only when every axis,
indexing operation, and downstream processor follows the new convention.

## What the sweeps isolate

### Range sweep

Changing only range changes delay and therefore the center row. The pulse
index, phase law, and column count do not change. Finite sample rate quantizes
the reported range to the closest row.

### Velocity sweep

Changing only velocity leaves the delay row fixed while changing phase slope
across pulse columns. A stationary target has flat ideal phase; equal approach
and recession speeds have opposite slopes. The magnitude of all three ideal
sequences remains one.

## Limiting cases and model boundaries

- At zero velocity, the ideal row sample has constant phase across pulses.
- At zero amplitude, a target contributes no visible row or slow-time trace.
- Two targets that quantize to the same row overlap in fast time; their
  slow-time phases may still differ, but separating them requires Doppler
  processing beyond this matrix-building lesson.
- If range changes enough during the coherent dwell, a target migrates between
  rows and the fixed-row model fails. In the baseline the largest omitted
  motion is about `0.112 m`, only `0.015` of a range sample, so holding each
  response in one row is an explicit stop-and-hop approximation.
- Delays beyond this script's recorded fast-time window are not captured;
  delays beyond the PRI alias in range as P35 showed.
- Doppler at or beyond `PRF/2` aliases in slow time as P36 showed.
- Increasing sample rate narrows range-grid spacing but does not by itself
  change waveform bandwidth or true range resolution.
- Increasing pulse count extends the coherent dwell but does not change
  fast-time spacing or the PRF ambiguity interval.

P42 will apply slow-time FFT processing across many rows to form a complete
range-Doppler map. P38 first uses the column direction for simple moving-target
indication.

## Why the broken case fails

The broken matrix is `abs(X)`. Its fast-time peaks still locate energy because
magnitude preserves range-response strength. But `abs` maps every complex
sample to a nonnegative real number, so adjacent samples have zero phase
difference. A moving target's slow-time spectrum is therefore driven toward
zero Doppler.

The target did not stop. The processing chain discarded the observable that
encoded motion. Recovery rebuilds the same complex noise from private seed
3701 and adds it to the retained clean matrix, restoring the exact baseline
samples and phase increment.

## Common interpretation mistakes

- Calling rows “range resolution” confuses sample-grid spacing with the
  waveform's ability to separate two targets.
- Reading brightness changes as Doppler ignores complex phase.
- Treating column number as fast time swaps the two clocks.
- Assuming a transpose changes physics ignores that only indexing convention
  changed; inconsistent labels are the actual failure.
- Ignoring the monostatic factor of two reports the wrong velocity.
- Expecting a fixed-row model to handle large range migration silently extends
  the experiment beyond its assumptions.

## Model and compatibility boundary

The experiment uses idealized seeded, range-resolved complex samples. Base
MATLAB arithmetic exposes delay-to-row mapping, target outer products, phase
progression, matrix orientation, the slow-time FFT, failure, and recovery. It
does not simulate transmit-waveform propagation, matched filtering, clutter,
acceleration, range migration, detection, or operational radar performance.
Static repository checks do not establish MATLAB runtime behavior, rendered
figures, hardware, HIL, field, real-time, deployment, or production results.
