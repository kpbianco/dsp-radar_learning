# P22 Walkthrough

## Guiding question

How does instantaneous frequency motion create an FM spectrum?

Run `experiment.m` once without editing it. It uses a private seed, closes only
figures tagged `P22`, and leaves the important arrays and metrics in `results`.

## 1. Baseline: follow the motion before the spectrum

The baseline holds `fc=3000 Hz`, `fm=100 Hz`, `Delta_f=400 Hz`, and amplitude
`Ac=1 V`. In the first figure, inspect one transition at a time:

1. The normalized message moves from -1 to +1.
2. Instantaneous frequency follows it from 2600 to 3400 Hz. The direct phase
   finite difference should nearly cover the designed trace; its small error is
   the one-sample derivative approximation.
3. The complex phasor magnitude stays at 1 V while its angle changes speed.
4. The RF cycles bunch and spread. Seeded receiver noise changes the observation
   slightly, but it is not used to define the clean occupied bandwidth.

Expected observation: the message changes phase slope and cycle spacing, not
transmitted phasor magnitude.

## 2. Baseline spectrum: connect repetition to line spacing

Open the second figure. The spectral lines are spaced by `fm=100 Hz` around the
3 kHz carrier. With `beta=Delta_f/fm=4`, several pairs carry visible energy.
The lower panel sums clean, bin-centered line power symmetrically until it
contains 98%.

Compare `results.occupied_bandwidth_hz` with
`results.carson_bandwidth_hz`. They should be close enough to support Carson's
width intuition, but do not describe the red boundaries as exact FM edges. An
ideal sinusoidal FM spectrum has infinitely many decreasing sidebands.

## 3. Sweep 1: change deviation only

The third figure holds `fc`, `fm`, amplitude, sampling, record length, and
measurement rule fixed. Only

```text
Delta_f = [50 200 400 800] Hz
```

changes. As deviation rises, `beta` rises from 0.5 to 8 and more sideband orders
become important. Compare `deviation_sweep_occupied_bandwidth_hz` with
`deviation_sweep_carson_bandwidth_hz`.

Expected observation: sideband spacing remains 100 Hz, but energy reaches more
orders and occupied width grows. Do not say that the lines moved farther apart;
that would confuse deviation with message frequency.

## 4. Sweep 2: change message frequency only

The fourth figure restores and holds `Delta_f=400 Hz`. Only

```text
fm = [50 100 200 400] Hz
```

changes. Adjacent lines spread farther apart while `beta` falls from 8 to 1.

Expected observation: Carson width grows because message bandwidth grows, even
though fewer sideband orders may be substantial. This is why `beta` alone is
not a bandwidth formula.

## 5. Broken case: sample an impossible design

The fifth figure intentionally asks the 24 ksample/s record to represent

```text
fc = 8000 Hz, Delta_f = 5000 Hz,
fi,max = 13000 Hz, Nyquist = 12000 Hz.
```

The intended phase slope crosses Nyquist. The 24 ksample/s wrapped phase slope
and sampled spectrum fold instead of representing the intended 13 kHz motion.
`broken_nyquist_margin_hz` is negative, and the 98%-bandwidth method is not
interpreted for this invalid record. The green trace reconstructs the same
phase law at the bounded 30 ksample/s recovery rate and follows the intended
motion without wrapped phase increments. The recovery also measures the 98%
line-power cluster through order `+/-51`: its upper edge is 13.1 kHz, matching
the one-tone Carson estimate and leaving 1.9 kHz below the 15 kHz Nyquist limit.

Recovery: require

```text
fs >= 2*(fc + Delta_f + fm + guard)
```

The extra `fm` covers the Carson/98%-occupied target beyond the maximum
instantaneous frequency. The script calculates a 27.2 ksample/s minimum for a
500 Hz guard and demonstrates 30 ksample/s with 6000 samples. Ideal sinusoidal
FM has still-smaller lines beyond any finite edge, so this recovery protects the
named 98% engineering target rather than claiming a perfectly bandlimited
waveform. Lowering carrier, deviation, or message rate before capture would also
recover margin. Do not try to repair aliased samples after capture.

## Common interpretation mistakes

- `Delta_f` is hertz; `beta=Delta_f/fm` is dimensionless.
- The derivative of phase in rad/s must be divided by `2*pi` to obtain hertz.
- `fm` sets sideband spacing; deviation controls how many orders matter.
- Carson's result is total width about the carrier, not an upper RF frequency.
- A small carrier line can be a Bessel redistribution, not amplitude dropout.
- FFT leakage or a display threshold is not a physical occupied-band edge.
- Constant envelope refers to the transmitted phasor. Added receiver noise can
  perturb observed voltage without changing the FM construction.

## Cancellation, recovery, and isolation

The base MATLAB script has fixed sample, sweep, figure, and numeric-storage
ceilings and no worker, timer, network, file, device, or external transaction.
Like any script, it assigns variables in the caller workspace. Ctrl+C can leave
those workspace variables, partial P22-tagged figures, and incomplete `results`;
a full rerun deterministically recreates P22 values and replaces only
P22-tagged figures, but it cannot restore a pre-existing caller variable that
used the same name. It does not alter MATLAB's global random stream or learner
progress. Rollback removes only P22 artifacts/status/catalog/test evidence and
restores P22 to `scaffolded`; P21 and canonical later identities remain
unchanged.

## Completion connection

Before using `checks.md`, explain aloud: repeated phase-slope motion creates a
sideband ladder, deviation and message rate broaden it in different ways, and
sampling must cover the complete intended frequency excursion with margin.
