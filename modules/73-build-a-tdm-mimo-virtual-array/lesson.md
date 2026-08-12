# P73 lesson: Timing Can Masquerade as Geometry

## Guiding question

How do multiple transmit and receive channels create more spatial samples?

## Physical mental model

Imagine four microphones fixed along a line. One transmitter illuminates a
target, so the four receivers provide four spatial samples. Move the
transmitter by four receiver spacings—one spacing beyond the `1.5 lambda`
receive aperture—and illuminate again. The new transmit-to-target-to-receive
paths behave like four more phase centers beyond the first four. TDM-MIMO does
this electronically: only one TX is active per slot, but known TX and RX
positions let the measurements be rearranged as a larger virtual array.

That rearrangement has a condition. The target should present the phase it
would have had if all virtual channels were measured together. Motion between
TX slots adds a temporal phase step. A spatial scanner cannot know that the
step came from time, so it can report the wrong direction until Doppler is
estimated and removed.

P72 is the ordered prerequisite. P61 introduced broadside angle and raw-array
phase, P62 connected aperture to beamwidth, P63 exposed the Hermitian scan,
and P70 showed that approaching motion has negative slow-time phase after the
`tx .* conj(rx)` FMCW mixer.

## From two physical coordinates to one virtual coordinate

Let TX `p` be at `x_tx,p` and RX `q` at `x_rx,q`. For a far-field colocated
radar, the directional path is the sum of the transmit and receive legs. The
virtual location is therefore

```text
x_virtual,pq = x_tx,p + x_rx,q.
```

It is a sum, not an average, and no additional monostatic factor of two belongs
in the position. The round-trip Doppler law already has its own factor two.

The baseline has positions in wavelengths

```text
RX = [0, 0.5, 1.0, 1.5]
TX = [0, 2.0].
```

The first TX produces `[0, 0.5, 1.0, 1.5]`. The second produces
`[2.0, 2.5, 3.0, 3.5]`. Together they form eight unique, contiguous
half-wavelength samples. Four simultaneous RX channels with aperture
`1.5 lambda` have become eight sequential virtual channels spanning
`3.5 lambda`.

This multiplication is not automatic. If TX positions create duplicate sums,
there are fewer unique phase centers than `N_tx N_rx`. If they create gaps,
the virtual array is sparse rather than the filled ULA used here. Channel data
and positions must also be reordered together.

## The dechirped spatial sample

Angles are measured from broadside toward positive x. P61's raw analytic
receive snapshot used positive spatial phase. P73 models a selected FMCW range
bin after the P69-P72 mixer `tx .* conj(rx)`, which conjugates the received
spatial phase. For a stationary target at `theta`, channel `p,q` is

```text
a_pq(theta) = exp(-j 2 pi (x_tx,p+x_rx,q) sin(theta)/lambda).
```

Both signs are legitimate at their stated processing points. Mixing a raw-RX
steering sign with a dechirped measurement sign mirrors the angle.

For candidate angle `psi`, the script constructs the same steering vector and
forms the explicit conventional scan

```text
w(psi) = a(psi)/M,
y(psi,l) = w(psi)^H x(:,l),
P(psi) = mean_l |y(psi,l)|^2.
```

The Hermitian product removes the matching spatial phase. No array or MIMO
toolbox object hides the position sum or coherent addition.

## Why the virtual beam is narrower

A direction change creates more phase change across a larger aperture. That
makes the coherent match fall away faster on either side of the target. In the
reviewed `+18 deg` baseline, the ideal half-power widths are about `27.8 deg`
for the four-RX row and `13.5 deg` for the eight-element virtual row. Doubling
the sample count is useful because this geometry also more than doubles the
aperture; merely duplicating a position would not do that.

The deterministic noisy scans estimate the same stationary angle. The virtual
curve is narrower, but its height is normalized for shape comparison. This is
not a calibrated claim that TDM created free transmit energy or simultaneous
snapshots.

## Sweep 1: target separation

The first controlled sweep places two equal, mutually incoherent ideal targets
symmetrically about broadside and changes only their angular separation:
`[8, 16, 28] deg`. Incoherent powers are added so an arbitrary source phase
does not make one lucky snapshot look resolved.

At `8 deg`, both arrays show one merged maximum. At `16 deg`, the four-RX
response is still merged while the virtual array has two maxima with a visible
midpoint dip. At `28 deg`, both are resolved, though the virtual midpoint is
much deeper. This is resolution from aperture, not from a denser plotted grid.

## TDM motion phase

For positive approaching velocity, P70's convention gives

```text
f_d = 2v/lambda,
temporal phase at time t = -2 pi f_d t.
```

TX1 is sampled at slot time zero and TX2 at `T_slot`. A moving target therefore
adds the second-group phase

```text
Delta_phi_TDM = -2 pi f_d T_slot.
```

That phase has nothing to do with `x_tx+x_rx`, but an uncompensated spatial
scan treats it as part of the virtual slope. With the dechirped sign convention,
positive approaching motion shifts the naive estimate to a more-positive
angle; receding motion shifts it the other way. The velocity sweep holds the
`2 x 4` geometry, true `+18 deg` angle, SNR, timing, and noise realization
fixed while velocity changes from `-10` to `+10 m/s`.

## Estimate Doppler without mixing TX slots

The script repeats complete two-slot cycles. Compare one channel only with
itself one full cycle later:

```text
r = sum conj(x_i[l]) x_i[l+1],
f_d_hat = -angle(r)/(2 pi T_cycle).
```

The sum uses all channels and adjacent cycles, but it never interprets the
TX1-to-TX2 phase as slow time. Once `f_d_hat` is available, each channel is
rotated back by its known within-cycle slot time:

```text
x_corrected,pq = x_pq exp(+j 2 pi f_d_hat t_p).
```

The common phase from one whole cycle to the next remains. A beam power scan is
insensitive to that common phase, while the unwanted phase difference between
TX groups is removed.

## Broken case and recovery

The broken case uses the already generated `+10 m/s` sweep record. Its true
Doppler is about `5.133 kHz`, and the `40 us` TX separation creates about
`-1.290 rad` between TX groups. Ignoring timing biases the angle by more than
four degrees. Recovery estimates Doppler from repeated same-TX looks and
rotates the unchanged record. It does not regenerate noise, change the target,
or sort samples independently of positions.

The exact Doppler is available in a simulation, but the recovery deliberately
uses the measured estimate. In a real system that estimate can be aliased,
noisy, or associated with the wrong target; compensation is only as reliable
as that information.

## Limiting cases and model boundary

- With one TX, zero velocity, or zero slot separation, there is no inter-TX
  motion-phase discontinuity. One TX also provides no MIMO aperture extension.
- One RX cannot show an RX spatial slope, although separated TX positions can
  still create virtual locations.
- Repeated or gapped position sums are not the reviewed filled virtual ULA.
- Half-wavelength virtual spacing avoids full-field grating lobes except for
  the shared endfire boundary. Larger spacing can make angle nonunique.
- Same-TX Doppler is sampled once per full `80 us` cycle. The reviewed speed
  range remains below its `+/-lambda/(4 T_cycle)` unambiguous limit.
- An inter-TX phase equal to an integer number of cycles can look harmless
  modulo `2 pi`; it does not prove that the target was stationary.
- Compensation assumes one constant radial velocity for the selected target
  and known slot timing. Multiple targets in one range-angle cell require
  association or joint processing.
- The target is stop-and-hop: angle and range do not migrate during the dwell.
  Acceleration, within-chirp range-Doppler coupling, phase noise, leakage,
  channel calibration, coupling, element patterns, multipath, and ADC effects
  are omitted.
- Normalized scan power is neither calibrated received power nor a detection.

## Common interpretation mistakes

- Counting `N_tx N_rx` channel pairs without checking unique position sums.
- Calling the TX/RX sum an average or adding an extra factor two.
- Saying eight virtual samples were measured simultaneously; the two TX groups
  are separated in time.
- Crediting a narrower beam to more plotted angles rather than more aperture.
- Treating the TDM phase step as a calibration error without checking velocity.
- Estimating Doppler from adjacent different-TX slots and thereby mixing time
  with geometry.
- Compensating with truth while describing the Doppler as measured.
- Sorting virtual positions without applying the same permutation to data.

## Dependencies and claim boundary

P72 is the governed prerequisite; P61-P63 and P70 provide the spatial and
temporal foundations. The script uses bounded base-MATLAB arithmetic and a
private deterministic generator, changes no global random state, writes no
file, and starts no network request, timer, worker, or external process.
Static validation and an independent Python oracle do not prove MATLAB parsing
or execution, rendered plots, RF behavior, hardware/HIL, real-time operation,
field performance, or operational radar performance.
