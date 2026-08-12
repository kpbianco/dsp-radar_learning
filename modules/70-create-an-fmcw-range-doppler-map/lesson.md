# P70 lesson: Two Clocks Make a Range-Doppler Map

## Guiding question

How do fast-time beat frequency and chirp-to-chirp phase separate range and velocity?

## Physical mental model

Imagine writing one short musical recording in each column of a notebook. The
pitch heard down a column says how far away a target is. The phase at the same
pitch as you move across columns says how quickly the target is approaching or
receding. FMCW range-Doppler processing reads both directions without confusing
their clocks.

P17 established complex mixing, P36 connected pulse-to-pulse phase with signed
Doppler, P37 fixed the fast-time-row/slow-time-column convention, P42 built the
analogous pulsed-radar map, and P69 established the ideal FMCW beat-to-range
law. P69 is the governed prerequisite for this lesson.

## One matrix, two physical coordinates

The script arranges one dechirped FMCW dwell as

```text
z[n,m],
```

where row index `n` is a sample within one chirp and column index `m` is the
chirp number. With chirp slope `S = B/T`, chirp repetition interval `T_r`, and
wavelength `lambda = c/f_c`, the reviewed target model is

```text
z_q[n,m] = a_q exp(j 2 pi (f_b,q n/fs - f_d,q m T_r) + j phi_q),
f_b,q = S(2R_q/c),
f_d,q = 2v_q/lambda.
```

For one target, the same laws are `f_b = S(2R/c)` and
`f_d = 2v/lambda`.

Positive velocity means approaching. P70 preserves P69's `tx .* conj(rx)`
mixer order: it makes the up-chirp range beat positive, while an approaching
carrier Doppler produces negative dechirped slow-time phase slope. Therefore
the plotted physical axis uses `v = -lambda f_slow/2`. The equation is
deliberately separable: range controls the tone down a column, while velocity
controls coherent phase across columns.
This is a stop-and-hop teaching model. It holds target range fixed within and
across this short coherent processing interval except for the explicit Doppler
phase. P71 will restore within-chirp Doppler and show range-Doppler coupling.

## Stage 1: beat frequency becomes range

Each chirp column contains the sum of target beat tones. The first transform is
performed down matrix rows:

```text
Y[k,m] = sum_n w_r[n] z[n,m] exp(-j 2 pi k n/N_s).
```

The script constructs `w_r[n]` as a Hann window, calls the base-MATLAB FFT
along dimension 1, retains the nonnegative beat-frequency half, and maps it to
range with

```text
R[k] = c f_b[k]/(2S).
```

This operation does not combine chirps. The output still has one complex
column per chirp, which is why Figure 2 shows a range-by-chirp matrix rather
than a finished target map. Targets 1 and 2 share `20 m`, so range processing
alone cannot separate them. Their complex column histories are different and
must remain intact.

For the full `40 us` record, the beat-frequency grid maps to

```text
Delta R = c fs/(2 S N_s) = c/(2B) = 1 m.
```

The equality occurs because the full sampled observation spans the complete
reviewed chirp duration. The `1 m` bin grid is also the familiar ideal FMCW
bandwidth scale here, but FFT bin spacing should not be treated as a universal
two-target-resolution guarantee.

## Stage 2: chirp phase becomes signed velocity

At one range row, a moving target is a complex tone across chirps. The second
transform acts across columns:

```text
Z[k,l] = sum_m w_d[m] Y[k,m] exp(-j 2 pi l m/N_c).
```

The centered Doppler and velocity coordinates are

```text
f_slow[l] = l/(N_c T_r),
v[l] = -lambda f_slow[l]/2.
```

Figure 3 first shows the ideal slow-time phases for the two targets at `20 m`.
One slopes downward and the other upward. The lower panel applies the FFT to
their shared range row and produces two signed velocity peaks. Figure 4 then
shows all three targets: targets 1 and 2 share range but differ in velocity;
targets 2 and 3 share velocity but differ in range. Both dimensions are needed
to make all three coordinates distinct.

`fftshift` only centers negative and positive slow-time frequency for display.
It does not create velocity sign. The complex phase progression and the
declared `tx .* conj(rx)` mixer convention determine the sign conversion.

## Sweep 1: coherent chirp count controls Doppler spacing

The first sweep reuses prefixes of the same deterministic range data and holds
PRF, wavelength, targets, fast-time processing, and window family fixed. For
`N_c = 16, 32, 64`,

```text
T_CPI = N_c T_r,
Delta f_d = 1/(N_c T_r),
Delta v = lambda/(2 N_c T_r).
```

Longer coherent observation makes the velocity bins closer and the equal-range
pair easier to distinguish. Range spacing does not change because the
fast-time record did not change. Zero-padding a short slow-time record could
draw more points, but it would not replace the missing coherent chirps.

## Sweep 2: retained fast-time samples control observed sweep

The second sweep keeps sample rate, chirp slope, chirp count, scene, and slow
processing fixed while retaining the first `128`, `256`, then `512` measured
samples. The observation duration and swept bandwidth are

```text
T_obs = N_s/fs,
B_obs = S T_obs,
Delta R = c/(2 B_obs).
```

The cases therefore observe `37.5`, `75`, and `150 MHz` of the same slope and
produce `4`, `2`, and `1 m` range grids. The two positive-velocity targets are
only `3 m` apart. They are blurred together in the shortest record and become
visibly distinct as the actual fast-time observation grows. This is not an
ADC-rate sweep: `fs` remains fixed, and each longer case contains more measured
time and more swept bandwidth.

## Intentionally broken phase loss and recovery

The broken path applies

```text
abs(Y[k,m])
```

before the Doppler FFT. Magnitude still identifies range neighborhoods, but it
removes whether the complex phasor rotated clockwise or counterclockwise from
chirp to chirp. An isolated moving target therefore collapses near zero
velocity; equal-range mixtures may also create difference-frequency ghosts.
Those artifacts are not target Dopplers.

Recovery does not regenerate noise or retune a threshold. It reuses the exact
unchanged complex `Y[k,m]`, applies the same slow-time window, and transforms
dimension 2. The recovered array is checked sample for sample against the
baseline map. Complex phase is measurement information, not optional plotting
decoration.

## Limiting cases and model boundary

- With one chirp, there is no chirp-to-chirp phase history and no Doppler
  estimate.
- With a very short fast-time record, close beat tones occupy one broad
  finite-observation response even if the plotted axis is densely interpolated.
- A target beat at or above `fs/2` aliases to an incorrect range. The reviewed
  targets remain well inside the `256 m` dechirped Nyquist limit.
- A Doppler at or beyond half the chirp repetition frequency aliases to an
  incorrect velocity. The reviewed targets remain inside about `+/-19.5 m/s`.
- At zero velocity, slow-time phase is constant and the target lies at zero
  Doppler with stationary leakage or clutter.
- If two targets share both range beat and Doppler phase rate, this 2-D map
  cannot separate them without another diversity dimension.
- Target ranges are fixed over the `3.2 ms` CPI. Acceleration and range-cell
  migration are absent.
- The beat model omits the within-chirp Doppler term so range and velocity are
  cleanly separable. P71 deliberately breaks this approximation to expose
  coupling; P72 uses opposite chirp slopes to disentangle it.
- The map is normalized voltage magnitude, not calibrated received power, a
  detector, CFAR output, or target report.

Static repository validation and a standard-library numerical oracle verify
the deterministic model contract and expected coordinates. They do not
execute MATLAB, inspect rendered figures, or establish RF, bench,
hardware/HIL, real-time, field, or operational performance.

## Common interpretation mistakes

- Treating rows and columns as interchangeable loses the physical clock behind
  each FFT.
- Taking magnitude before Doppler processing destroys signed velocity phase.
- Calling `fftshift` the source of negative velocity confuses display order
  with complex phase direction.
- Calling range-bin spacing guaranteed target resolution ignores window shape,
  SNR, and separation criteria.
- Calling more plotted FFT points more measurement confuses interpolation with
  a longer sample or chirp record.
- Claiming the sample-count sweep changes ADC rate is wrong; this sweep retains
  more samples at one fixed `fs`.
- Adding within-chirp Doppler to this separable baseline and still using
  `R = c f_b/(2S)` without qualification anticipates the P71 coupling failure.
- Calling bright map cells detections exceeds this lesson; no threshold or
  false-alarm control is applied.
