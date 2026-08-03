# P25 Walkthrough: Create and Equalize a Multipath Channel

## Guiding question

How do delayed copies distort symbols even when noise is small?

Run `experiment.m` once from this module directory. It uses a private seed, so
a full rerun reconstructs the same symbols and noise without changing the
MATLAB global random stream.

## 1. Read the channel before the receiver

Start with **P25 Channel impulse and fading**. The baseline impulse response
has paths at 0, 1, and 2 symbol periods. Name those delays from the stem plot
before looking at any equalized result.

Now inspect the solid frequency response. Delayed paths rotate by different
amounts across frequency, so the magnitude is not flat. Compare it with the
dashed broken response, but do not diagnose the failure yet.

Expected observation: the baseline has frequency-selective peaks and dips but
no nearly erased band. The broken channel approaches a deep null near
`f/R_s=0`.

## 2. Follow one processing transition at a time

Open **P25 Waveform and eye closure**. The first plot overlays the transmitted
I waveform and the multipath-plus-noise waveform over 14 symbol periods. The
received curve is not merely a noisier copy: its shoulders move because old
pulses are being added.

In the eye plot, compare the blue direct-path traces with the red multipath
traces at time zero. The red opening closes because the previous one and two
symbols contribute different values to the present sample.

Then open **P25 Baseline equalization**:

1. Unequalized points show data-dependent constellation smearing.
2. ZF uses the explicit causal inverse and pulls the moderate channel toward
   an impulse.
3. MMSE uses the noise variance as regularization and accepts a small residual
   in exchange for slightly lower noise gain.

Use the printed EVM percent, SER, and equalizer noise gain in dB. EVM measures
distance from the transmitted QPSK point; it is not the same as SER.

## 3. Sweep one: change only one echo magnitude

Open **P25 Echo gain sweep**. The one-symbol echo magnitude takes
`[0, 0.25, 0.50, 0.75]`; its delay and phase, the other paths, symbols, noise,
pulse, and equalizer length stay fixed.

Expected observation: unequalized EVM generally grows as the delayed copy
becomes stronger. The minimum channel magnitude also changes because path
cancellation is frequency dependent. MMSE suppresses much of the ISI, but its
result is not independent of channel severity.

Physical interpretation: echo magnitude controls how much a previous symbol
is added now. The lower plot explains why gain alone is not the whole story:
phase cancellation determines the weakest spectral region.

## 4. Broken case: force a deep null

The intentionally broken channel is `h=[1, -0.999]`: a one-symbol echo almost
equals and opposes the direct path at zero frequency. In **P25 Broken ZF and
MMSE recovery**, first inspect only the ZF constellation and its printed noise
gain.

The 31-tap causal ZF cancels 30 postcursor samples, but its inverse taps decay
so slowly that they carry large energy and leave a long trailing residual.
The deep null makes the result noisy and smeared even though input `E_s/N_0`
is 18 dB. This is the required equalization failure.

## 5. Sweep two: regularize one channel

Keep the broken channel and the same data/noise fixed. Change only `lambda`
through `[0.001, 0.01, 0.03, 0.10]`.

- Moving right lowers equalizer noise gain.
- Too little regularization tries too hard to invert the null.
- Too much shrinks the filter and leaves channel distortion.
- The recovery selects the tested value nearest the known noise variance.

Expected observation: the EVM has a middle region better than aggressive ZF.
The MMSE constellation is still imperfect; that is the cost of not amplifying
the near-null noise.

## 6. Recovery and concept connection

Recovery changes only the equalizer rule, not the received record: use the
regularized taps near `lambda = 10^(-18/10)`. Confirm that both EVM and noise
gain fall relative to causal ZF. Then connect the views:

`delayed taps -> frequency cancellation -> eye closure/constellation ISI -> inverse-filter noise gain`.

For a communications link this is symbol interference. In radar, the same
convolution can represent unwanted coupling, ringing, or unresolved echoes;
deconvolution faces the same null limitation.

## Operational recovery, isolation, and rollback

- The run is bounded to 480 symbols, 8 samples/symbol, 3 paths, 31 equalizer
  taps, 4 cases per sweep, 5 tagged figure groups, and a conservative 750000
  stored-numeric-value budget. There is no worker, timer, network, external
  transaction, or persistent output to time out.
- If a run appears stuck, use **Ctrl+C**. A full rerun deletes only figures
  tagged `P25` and reconstructs deterministic P25 variables from its private
  seed. It cannot restore caller workspace variables overwritten before
  cancellation, so use a fresh workspace if that isolation matters.
- P25 does not read or write `.learning/`; learner progress remains isolated
  behind `bin/learn`.
- Base MATLAB is the compatibility target; no toolbox equalizer or pulse
  designer is required.
- Content rollback removes the four implementation artifacts and P25 test and
  evidence files, restores this README to its scaffold wording, and restores
  only P25's manifest status to `scaffolded`. P24 and all canonical identities
  remain unchanged.
