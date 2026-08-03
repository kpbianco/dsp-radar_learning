# P24 Walkthrough: One Processing Transition at a Time

## Guiding question

Why are symbols filtered before transmission and again at reception?

Run `experiment.m` once without changing its controls. The private seed makes
the symbol and white-noise records repeatable without resetting MATLAB's
global random stream.

## Baseline 1: points become pulses

Look first at **P24 pulse shapes and transmitted waveform**.

1. Compare the abrupt rectangular pulse with the smooth RRC pulse.
2. Follow either I or Q through twelve symbol periods.
3. Notice that RRC contributions overlap across boundaries. Do not label that
   overlap as ISI yet; ISI is judged at decision samples after the full chain.

Expected observation: the rectangular waveform holds abrupt levels, while the
RRC waveform moves smoothly and remembers neighboring symbols.

## Baseline 2: inspect the spectral price

Open **P24 pulse spectra** and compare the curves in normalized frequency
`f/R_s`.

Expected observation: the rectangular pulse has slowly decaying sidelobes.
The finite RRC response is much more concentrated. Read the 99%-power bandwidth
numbers as repeatable FFT estimates, not as exact analog or regulatory
measurements.

## Baseline 3: find the receiver decision instant

Open **P24 matched output and eye**.

1. In the upper plot, separate the sample-rate matched-filter output from the
   one retained symbol-clock sample.
2. In the eye diagram, find time zero. The traces have their largest vertical
   separation there.
3. Connect that time to `rrc_total_group_delay = span*sps` rather than to the
   beginning of the received vector.

Expected observation: the waveform is still continuous at the filter output,
but timing reduces it to one useful statistic per symbol.

## Baseline 4: compare the constellations

Open **P24 constellation before and after timing** from upper left to upper
right.

- Before the receive matched filter, an RRC pulse alone is not a raised-cosine
  Nyquist response. Pulse overlap and unintegrated noise spread the samples.
- After the matched filter and total-delay compensation, clusters move toward
  the four P23 QPSK points. Compare `rrc_pre_filter_evm_pct` with
  `rrc_matched_evm_pct`.
- The rectangular path also reports EVM and SER. Its ideal timing can be clean
  even though its spectrum is poorly contained.

## Sweep 1: change roll-off only

The script evaluates `rolloff_sweep = [0.10 0.25 0.50 1.00]` while keeping
the eight-symbol span, QPSK record, samples per symbol, and FFT method fixed.

Observe the left panel of **P24 parameter sweeps and timing failure** and the
printed `rolloff_sweep_bandwidth_rs` vector.

Expected observation: 99%-power bandwidth grows with beta. At the small-beta
end, the fixed eight-symbol truncation also leaves more ISI-only EVM because
the ideal pulse has longer tails. Do not claim that a larger beta is simply
"better"; it spends bandwidth.

## Sweep 2: change span only

Now inspect `span_sweep_symbols = [2 4 6 8]`. Roll-off remains 0.25 and all
symbols and diagnostics remain fixed.

Expected observation: tap count and group delay rise with span, while the
controlled ISI-only EVM falls sharply. This is the cost/approximation trade:
more of the ideal pulse is retained.

## Broken case: sample halfway between symbols

The lower-left constellation uses the correct RRC matched filter but samples
four samples late, or `+0.5T` at eight samples per symbol.

Before reading the metric, predict whether more SNR alone would repair this
case.

Expected observation: even the noiseless constellation smears and crosses
decision boundaries. `broken_isi_evm_pct` and `broken_ser` diagnose a timing
reference failure, not weak signal power.

## Recovery

The script subtracts the known four-sample offset. It does not change the
symbols, pulse, noise assumption, or decision rule. The lower-right
constellation and `recovered_isi_evm_pct` return exactly to the noiseless
baseline.

Physical interpretation: the matched filter supplies the correct statistic
only when the receiver also selects its peak at the symbol clock.

## Common interpretation mistakes

- Smooth waveform overlap is not automatically ISI; inspect the combined
  pulse at integer symbol offsets.
- The matched filter maximizes sampled SNR in white noise for a known pulse;
  it does not make noise vanish or discover timing by itself.
- The RRC transmit filter alone is not the final raised-cosine response.
- A wider roll-off is not free improvement, and a rectangular spectrum is not
  narrow merely because its main lobe looks compact.
- EVM can expose degradation while SER remains zero.

## Cancellation, isolation, and recovery

The workload is bounded by 320 symbols, eight samples per symbol, four cases
per sweep, five P24-tagged figure groups, and a conservative 500000-value
budget. If a run must be stopped, use **Ctrl+C**. Cancellation may leave
partial P24 figures and workspace variables; MATLAB cannot restore workspace
variables already overwritten by a script. A full rerun reconstructs the
same arrays from the private seed and closes only figures tagged `P24`.

The script does not reset the global random stream, update `.learning/`, open
files or network connections, start a worker or timer, or create an external
transaction. Base MATLAB is the only runtime dependency. No rollback is needed
for a canceled run beyond closing P24 figures or rerunning the script. To roll
back the repository batch, remove the P24-created artifacts/tests/evidence and
restore only P24's manifest status to `scaffolded`; preserve P23 and all
canonical identities.

## Completion connection

You are ready for `checks.md` when you can explain why the transmit filter
controls the time/frequency waveform, why the conjugate time-reversed receive
filter improves the decision statistic, and why correct timing is still
required for an open eye and clean constellation.
