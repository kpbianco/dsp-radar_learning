# P35 lesson: Create Unambiguous-Range Aliasing

Guiding question: **Why can a distant target appear at a shorter false range?**

## A pulse label can be lost

P34 described the matched response of one finite pulse versus delay and
Doppler mismatch. P35 repeats a pulse every pulse-repetition interval (PRI).
Imagine writing a serial number on each transmitted pulse. A target echo still
contains its delay, but an ordinary periodic waveform does not return that
serial number. If the echo arrives after newer pulses have left, the receiver
cannot know which transmission caused it from arrival time alone.

The pulse repetition frequency (PRF) and PRI are reciprocals:

\[
T_r=\mathrm{PRI}=\frac{1}{\mathrm{PRF}}.
\]

For a monostatic radar, the round-trip delay of a target at true range `R` is

\[
\tau=\frac{2R}{c}.
\]

Only one PRI of fast time is retained after each transmit event. The number of
whole intervals in the delay is the ambiguity order

\[
q=\left\lfloor\frac{\tau}{T_r}\right\rfloor.
\]

Removing those whole intervals leaves the apparent delay

\[
\tau_{\mathrm{app}}=\tau-qT_r,
\qquad 0\leq\tau_{\mathrm{app}}<T_r.
\]

Converting that interval to range gives the unambiguous range and the folded
report:

\[
R_u=\frac{cT_r}{2}=\frac{c}{2\,\mathrm{PRF}},
\]

\[
R_{\mathrm{app}}=R-qR_u=\operatorname{mod}(R,R_u),
\qquad 0\leq R_{\mathrm{app}}<R_u.
\]

This is the same kind of lost-integer problem as sampling aliasing, but the
periodic coordinate is round-trip time rather than sinusoid phase. All ranges
`R_app + k*R_u`, for nonnegative integers `k`, produce the same ideal fast-time
location. One apparent range therefore represents a family of possible true
ranges.

## Read the baseline as a pulse-identity story

The baseline uses a 20 kHz PRF, so the PRI is 50 microseconds and
`R_u = 7.494811 km`. The true target is at 18 km. Its round-trip delay is
about 120.083 microseconds: two complete PRIs plus about 20.083 microseconds.
The echo from the first pulse arrives after transmissions at 50 and
100 microseconds have already occurred.

The receiver opens its present listening interval at 100 microseconds and
sees the old echo about 20.083 microseconds later. Without the original pulse
label it reports

\[
q=2, \qquad R_{\mathrm{app}}=18.000-2(7.494811)
\approx 3.010377\ \mathrm{km}.
\]

The absolute timeline and the folded listening-interval plot show the same
arrival using two coordinate systems. The faint private-seed noise makes the
received trace look like a measurement, but the fold equation does not depend
on noise or detection.

## Why the PRF sweep jumps

The first sweep holds the target at 18 km and varies only PRF. Raising PRF
shortens the PRI, so `R_u` decreases smoothly. Apparent range does not have to
decrease smoothly. Whenever the quotient `q` gains another whole interval,
the remainder jumps from near `R_u` to near zero. The result is a sequence of
folded branches, not a monotonic range bias.

For the marked cases:

| PRF (kHz) | Unambiguous range (km) | Ambiguity order | Apparent range (km) |
| ---: | ---: | ---: | ---: |
| 10 | 14.990 | 1 | 3.010 |
| 15 | 9.993 | 1 | 8.007 |
| 20 | 7.495 | 2 | 3.010 |
| 25 | 5.996 | 3 | 0.012 |

Two different PRFs can put the same target near the same apparent gate even
though their ambiguity orders differ. Multiple PRFs can help resolve the
integer ambiguity, but this lesson does not implement a multi-PRF estimator.

## Why the true-range sweep is a sawtooth

The second sweep holds PRF at 20 kHz and moves the target from zero through
three unambiguous intervals. Below `R_u`, `q=0` and apparent range equals true
range. Just below each multiple of `R_u`, the report approaches the end of the
listening interval. Just above that boundary, `q` increments and the report
returns near zero. The target did not jump; the coordinate label wrapped.

Targets separated by an integer multiple of `R_u` collide in the same ideal
range gate. A matched filter may resolve close delays inside one interval, but
it cannot recover the missing pulse number by range resolution alone.

## Broken case: use information the receiver never measured

The intentionally broken path follows the echo back to the first transmit
pulse using the simulation's hidden event label, then reports the full 18 km.
That answer is numerically the true range but invalid for the stated fixed-PRF
receiver. The algorithm consumed information that the waveform and measured
fast time do not contain.

Recovery discards the hidden label, recomputes `q` and the remainder, rebuilds
the private-seed receive trace, and asserts exact agreement with the baseline.
It also adds three whole unambiguous intervals to the target and verifies that
the apparent range is unchanged. The issue is observability, not arithmetic
precision.

## Assumptions and limiting cases

- The model is monostatic, stationary, ideal complex baseband, and uses a
  constant `c = 299792458 m/s`. It omits Doppler, acceleration, propagation
  loss, clutter, multipath, antenna effects, target fluctuation, and detection.
- A target with `0 <= R < R_u` has `q=0`, so its apparent and true ranges are
  equal in the ideal model.
- At exactly `R = k*R_u`, the mathematical remainder is zero. A real pulsed
  radar may be transmitting, blanked, or recovering then, so this is not a
  claim that a zero-range echo is detectable.
- Immediately below and above a boundary, an arbitrarily small true-range
  change can cause a nearly `R_u` apparent-range jump.
- Reducing PRF increases unambiguous range. It does not change the speed of
  light, pulse bandwidth, range-cell width, received power, or accuracy within
  a gate. PRF also participates in Doppler ambiguity; P36 begins the
  pulse-to-pulse phase model, and later modules treat that trade more fully.
- The plotted pulse width introduces a near-transmit blind-time scale, but the
  ideal modulo equation does not model transmit/receive switching or minimum
  range.
- The absolute timeline is sampled at 20 MHz for display. Its nearest-sample
  marker can differ from the continuous apparent range by at most half a range
  sample; the printed analytic value is not quantized to that display grid.

## Common interpretation mistakes

- The target did not reflect from a nearer physical location. Only its pulse
  association and range label are ambiguous.
- `R_u` is not range resolution. Bandwidth and matched-response shape govern
  separation within a listening interval.
- A lower PRF does not strengthen an echo or improve delay accuracy by itself.
- Taking the smallest candidate `R_app` as the true range is an assumption,
  not information recovered from one fixed-PRF measurement.
- The ambiguity order is a count of elapsed PRIs, not a Doppler bin, target
  count, or multipath order.
- The folded profile is not P34's ambiguity-function surface and is not yet a
  range-Doppler map.

## Dependencies and concept connection

P30 supplied `R=c*tau/2`; P31 separated resolution from accuracy; P34 showed
the joint mismatch response of one pulse. P35 adds pulse repetition and shows
that good within-pulse delay response does not preserve transmit-pulse
identity. The experiment uses base MATLAB, an explicit quotient/remainder,
bounded loops, tagged figures, and a private seed rather than a toolbox range
conversion or opaque radar object.

Completion means you can calculate the folded apparent range for a target beyond the unambiguous interval.
