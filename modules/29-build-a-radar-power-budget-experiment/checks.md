# P29 Checks: Build a Radar Power-Budget Experiment

## Guiding question

How quickly does received echo power fall with range?

## Observation checks

1. On the logarithmic range plot, what is the received-power change from 10 km
   to 100 km? Expected: `-40 dB`.
2. Which plotted line separates positive and negative detection margin?
   Expected: the required-SNR threshold `N + required SNR`, not the raw noise
   floor alone.
3. Do the RCS and transmit-power sweeps change the range slope? Expected: no;
   they shift the curve vertically while the exponent remains four.
4. At fixed antenna gains, which frequency curve is strongest? Expected: 3 GHz
   because its wavelength is longest in this stated comparison.

## Prediction checks

1. Predict the echo-power change if range doubles. Expected: divide by 16, a
   loss of about `12.04 dB`.
2. Predict the transmit-power multiplier required to double range with every
   other term fixed. Expected: 16 times.
3. Predict the antenna-gain change that can replace that power increase.
   Expected: `+12.04 dB` in the product `Gt*Gr`; that is `+12.04 dB` in one
   gain term alone, or about `+6.02 dB` in each reciprocal transmit/receive
   gain.
4. Predict the range multiplier from four times the transmit power. Expected:
   `4^(1/4)`, about 1.41.
5. Predict the effect of doubling RCS or halving linear loss. Expected: twice
   the received power, about `+3.01 dB`.
6. Predict the fixed-gain effect of doubling wavelength. Expected: four times
   the received power, about `+6.02 dB`.
7. Could reducing the baseline 6 dB loss alone recover the full 12.04 dB
   range-doubling penalty? Expected: no. The loss factor cannot fall below one;
   another budget term must supply the remaining recovery.

## Interpretation checks

- Explain why `R^-4` contains two spreading losses but only one RCS term.
- Explain why watts use `10 log10` for conversion to dBW and why dBm is 30 dB
  above dBW.
- Explain why positive deterministic margin does not by itself specify
  probability of detection.
- State what must be held fixed before interpreting the frequency sweep. A
  correct answer names antenna gain and distinguishes fixed physical aperture.
- Name two range-equation assumptions that can fail in an operational scene.

## Failure and recovery checks

1. Why can the broken `R^-2` curve agree with the correct curve at 40 km yet be
   wrong? Expected: it is artificially anchored at one point; its slope reveals
   the missing return spreading.
2. What slope identifies the broken model? Expected: `-20 dB/decade` instead of
   `-40 dB/decade`.
3. What proves a clean recovery? Expected: an independently recomputed `R^-4`
   curve exactly matches baseline, the decade slope returns to `-40 dB`, and a
   new private stream exactly reproduces both seeded noise vectors.
4. If a run is interrupted with `Ctrl+C`, why should you rerun from the top?
   Expected: validation, deterministic seed creation, results, and plots form
   one bounded run; partial workspace state is not a completed result.

## Isolation, compatibility, and resource checks

- Confirm the script uses base MATLAB and no toolbox, worker, timer, file,
  network, device, or external transaction.
- Confirm it uses a private seed without changing the global random stream,
  closes only figures tagged `P29`, and never writes `.learning/`.
- Confirm the canonical limits: 239 range points, three RCS cases, three
  frequencies, three transmit-power cases, 4096 finite-noise samples, four
  figure groups, and at most 40,000 conservatively counted numeric values.
- Confirm rollback is local: remove P29-owned artifacts and restore only P29 to
  `scaffolded`, preserving active control state and other modules.

## Completion checklist

- [ ] I can explain the outward and return spreading terms.
- [ ] I can predict the 16-times-power cost of doubling range.
- [ ] I can convert among watts, dBW, dBm, and linear/dB ratios without mixing
      representations.
- [ ] I can interpret the noise floor, required-SNR threshold, and margin.
- [ ] I can state the invariant behind the RCS, frequency, and power sweeps.
- [ ] I can diagnose the broken `R^-2` model from its slope and recover `R^-4`.

## Short teach-back rubric

In two or three sentences, answer: **How quickly does received echo power fall
with range?** A complete teach-back says `R^-4`, gives either the 12.04 dB loss
or factor-of-16 loss for doubled range, and connects that loss to the required
transmit-power or combined-gain recovery. It should also avoid claiming that a
deterministic positive margin guarantees detection.
