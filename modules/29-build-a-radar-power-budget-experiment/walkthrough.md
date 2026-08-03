# P29 Walkthrough: Build a Radar Power-Budget Experiment

## Guiding question

How quickly does received echo power fall with range?

Run `experiment.m` from this module folder. The script validates every control
and resource ceiling before random generation, allocation, figure cleanup, or
plotting. It retains its values in `results` for inspection.

## 1. Baseline observation: follow the two spreading trips

Read the visible controls first: 100 kW peak transmit power, 35 dBi transmit
and receive gains, 10 GHz carrier, 1 m^2 RCS, and 6 dB lumped loss. Then inspect
the first figure.

- On the linear range axis the curve bends sharply downward.
- On the logarithmic range axis a tenfold range change is a 40 dB loss.
- Compare the reported 40 km echo power with the noise floor and detection
  threshold in the third figure. The zero-margin marker is the range at which
  this simple power criterion changes sign.

Concrete observation question: between 10 km and 100 km, does the echo lose
20 dB or 40 dB?

The seeded finite noise measurement should sit near the analytic `kTBF` value.
It is not used to move the threshold; it makes finite measurement variation
visible without turning one random result into the budget.

## 2. Sweep one variable: target RCS only

In the upper panel of the second figure, only RCS changes through
`[0.1, 1, 10] m^2`. Every tenfold RCS change moves the entire received-power
curve by 10 dB. The curves remain parallel because RCS changes the numerator,
not the `R^-4` exponent.

Prediction before editing: if RCS doubles, should the echo rise by 3 dB or
6 dB? Check the one-at-a-time sensitivity bars after answering.

## 3. Sweep one variable: frequency only, with gains fixed

In the lower panel of the second figure, only carrier frequency changes through
3, 10, and 30 GHz. Both antenna gains remain 35 dBi. Higher frequency means a
shorter wavelength, so this fixed-gain equation gives less received power.

Do not silently switch the invariant. If physical antenna areas were held
fixed, their gains would change with wavelength and this plot would answer a
different question.

## 4. Sweep one variable: transmit power only

The lower panel of the third figure compares 25, 100, and 400 kW. A fourfold
power increase adds 6.02 dB of margin everywhere, yet the printed maximum range
grows by only `4^(1/4)`, about 1.41. Use the zero-margin crossing, not just the
vertical curve shift, to connect power to usable range.

At the 40 km reference point, `results.baseline.required_power_multiplier_at_reference`
states the transmit-power multiplier needed to recover any negative margin.
For the general range-doubling question, inspect
`results.range_doubling.required_power_multiplier`: it is exactly 16.
The same result group also retains the equivalent gain recovery: 16 times one
gain term, or 4 times (`+6.02 dB`) in each reciprocal transmit/receive gain.

## 5. One-at-a-time budget audit

The upper panel of the fourth figure changes transmit power, transmit gain,
receive gain, wavelength, loss, and RCS one at a time. Verify the physical
meaning of each bar:

- `Pt x2`, `Loss /2`, and `RCS x2` each add about 3.01 dB.
- `Gt +3 dB` and `Gr +3 dB` each add exactly 3 dB.
- `Wavelength x2` adds about 6.02 dB at fixed gains.

The bar plot deliberately keeps the reference range fixed. It isolates budget
terms; it is not another range sweep.

## 6. Intentionally broken case: count only one spreading trip

The lower panel anchors an `R^-2` curve to the correct curve at 40 km. At the
anchor they agree, which makes this a useful failure: matching one point can
hide a wrong model. Away from 40 km, the broken curve changes by only
`-20 dB/decade` and badly overstates long-range echo power.

Failure interpretation: the broken calculation remembered the outward
free-space spreading but omitted the echo's return spreading. It is not a
different target or a more efficient radar.

## 7. Recover and connect the concept

Recovery independently recomputes the full monostatic equation with `R^4` and
recreates both finite-noise vectors from the private seed. The recovered curve
must match the baseline exactly and restore `-40 dB/decade`.

Now answer the completion connection in plain language: if range doubles and
all other terms stay fixed, how much transmit power or combined antenna gain is
needed to restore the lost margin, and why? The gain-product answer is
`+12.04 dB`: either one gain term supplies all of it, or reciprocal transmit and
receive gains each increase by about `+6.02 dB`.

## Safe rerun, cancellation, isolation, and rollback

- The script uses base MATLAB only, fixed finite arrays, bounded `for` loops,
  no worker, no timer, and no external transaction. It should finish promptly.
- If execution must be cancelled, use `Ctrl+C`. A clean rerun starts from the
  same validated controls and private seed; partial workspace values are not
  evidence of a complete run.
- The private seed does not replace or advance MATLAB's global random stream.
  Cleanup closes only figures tagged `P29`; unrelated figures stay open.
- The script performs no file, network, device, or `.learning/` write. Learner
  progress remains isolated under `.learning/` through `bin/learn` only.
- Repository rollback removes only P29 implementation artifacts and restores
  only P29's manifest status to `scaffolded`. It must preserve the operator's
  active-batch control state and every other module.
