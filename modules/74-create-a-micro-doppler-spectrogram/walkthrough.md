# Walkthrough: read periodic motion around a bulk ridge

## Guiding question

How do rotating or swinging target parts produce time-varying Doppler around bulk motion?

Run `experiment.m` from this module directory. It targets base MATLAB R2016b
or newer and uses no optional toolbox. Work through one figure or processing
transition at a time.

## 1. Establish the physical baseline

Read the printed controls before interpreting color:

- carrier: `24 GHz` (`lambda = 12.5 mm`);
- slow-time sample rate and dwell: `4.8 kHz` and `4 s`;
- torso velocity: `+1.2 m/s` approaching;
- limb velocity: torso speed plus an opposite-phase `+/-2.0 m/s` swing;
- swing rate: `1.5 Hz`;
- seeded input SNR: `25 dB`.

The physical predictions are

```text
bulk Doppler = 2(1.2)/0.0125 = +192 Hz
limb excursion = 2(2.0)/0.0125 = +/-320 Hz.
```

The limb tracks therefore range from about `-128 Hz` to `+512 Hz`, while the
torso stays near `+192 Hz`.

## 2. Observe raw composite phase

Inspect only the first panel of `P74 baseline phase spectrum and spectrogram`.
The overall slope comes from bulk approach. Fine curvature and occasional
abrupt changes come from coherent limb addition and cancellation.

Observation question: where the curve changes sharply, did the torso suddenly
teleport or can several phasors briefly cancel? Use the latter interpretation.
Do not turn composite unwrapped phase into an unquestioned limb-velocity
estimate.

## 3. Observe the dwell-wide Doppler spectrum

Move to the second panel. Locate the strong bulk neighborhood and the wider
sideband energy. The FFT accumulates the whole dwell. It shows that the target
contains more than one constant Doppler, but it has discarded the time at
which each limb velocity occurred.

Do not label every spectral line as a separate target. Periodic phase
modulation can create a comb from one moving component.

## 4. Observe the baseline spectrogram

Now inspect the third panel. The explicit STFT uses a `512`-sample (`106.7 ms`)
Hann window, `384`-sample overlap, and `2,048`-point FFT. White overlays show
the known component Dopplers.

Find:

1. the near-horizontal torso ridge around `+192 Hz`;
2. periodic limb energy above and below that ridge;
3. repeated crossings at the bulk velocity; and
4. the difference between a physical window response and the dense zero-padded
   frequency grid.

The raw dechirped phasors rotate negatively for approach, consistent with
P70-P73. The script reverses both STFT rows and their frequency axis, so this
display uses positive physical Doppler for approach.

## 5. Sweep one physical variable: swing speed

Inspect `P74 swing-speed sweep`. Only peak swing speed changes through
`[1, 2, 3] m/s`. Carrier, bulk speed, swing rate, amplitudes, STFT settings,
and the deterministic additive-noise samples and scale remain fixed.

Expected extents around the unchanged `+192 Hz` torso ridge are `+/-160`,
`+/-320`, and `+/-480 Hz`. Faster swing widens the track but does not move the
bulk ridge or change the `1.5 Hz` repetition rate.

Interpretation mistake: wider hertz spread here is not a higher carrier; the
carrier is held at `24 GHz`.

## 6. Sweep one physical variable: carrier frequency

Inspect `P74 carrier-frequency sweep`. Only carrier changes through
`[10, 24, 77] GHz`. Every physical velocity, scatterer amplitude, swing rate,
STFT setting, and deterministic additive-noise samples and scale remains fixed.

Both bulk Doppler and limb excursion grow in hertz in direct proportion to
carrier. The physical velocity does not change. If each frequency axis were
converted with its own wavelength, the tracks would overlay in `m/s`.

Interpretation mistake: do not compare hertz widths at different carrier
frequencies as if they directly proved different limb speeds.

## 7. Sweep one processing variable: window duration

Inspect `P74 STFT-window sweep`. These panels use the exact same baseline
measurement and the same `2,048`-point FFT grid. Only the Hann window changes:

- `192` samples (`40 ms`, native `1/T = 25 Hz`);
- `512` samples (`106.7 ms`, native `1/T = 9.375 Hz`);
- `1,536` samples (`320 ms`, native `1/T = 3.125 Hz`).

The short window follows turning motion more locally but has a broader local
frequency response. The long window narrows stationary response while mixing
more of each curved swing into one frame. The fixed zero-padding makes clear
that display-bin spacing is not the physical resolution control.

## 8. Run the intentionally broken case

Inspect the top panel of `P74 magnitude-only failure and recovery`. The broken
operation is explicit:

```matlab
magnitude_only_record = abs(broken_complex_measurement);
```

The strongest integrated energy moves near zero because the shared bulk phase
rotation was discarded. Some relative amplitude beating can survive, but it
does not preserve absolute signed Doppler.

## 9. Recover without changing the measurement

Inspect the lower panel. Recovery applies the same explicit STFT to the saved
complex record. The script asserts that the broken measurement was not mutated
or regenerated and that the bulk peak returns near `+192 Hz`.

State the conceptual connection: P18's I/Q rotation direction becomes P36's
signed Doppler, and the P15 STFT localizes that rotation in slow time at the
selected P70 range cell.

## 10. Cancellation, timeout, recovery, and rollback

The run is synchronous and bounded. It starts no worker, timer, file
transaction, network request, or external persistent state. If a local run
takes unexpectedly long, press `Ctrl+C`; partial workspace arrays and figures
may remain, but no background task needs cancellation. Close the five tagged
figure groups and rerun from the top for deterministic recovery.

Malformed controls fail before large STFT allocations. After correcting a
control, rerun from the top; private random state is derived only from visible
seeds. To roll back a local exploratory edit, restore the visible baseline
value and rerun. Repository rollback is separate: remove P74 implementation
artifacts/tests/evidence and restore only P74's manifest/catalog status to
scaffolded, preserving P73, later module identities, `.learning/`, and
operator-managed contract activation.

## 11. Finish with a teach-back

In about six sentences, explain:

1. how bulk and component velocity enter integrated coherent phase;
2. why the dwell-wide spectrum loses timing;
3. what the torso ridge and periodic side tracks mean;
4. how speed and carrier sweeps differ;
5. what the STFT window trades; and
6. why magnitude-only processing fails and unchanged I/Q recovers.

Do not claim that this bounded simulation validates a person, rotor, RF
sensor, physical radar, hardware/HIL system, real-time path, field operation,
or deployed classifier.
