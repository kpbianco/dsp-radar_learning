# P20 Checks — Frequency, Phase, and Evidence

## Guiding question

How accurately can frequency and phase be estimated from a finite noisy record?

Use the console metrics and one plot at a time. These checks test
interpretation, not MATLAB syntax.

## Baseline observations

1. What is the FFT spacing for 256 samples at 1024 samples/s? Why can the peak
   bin not print the exact `123.25 Hz` truth?
2. Which estimates lie between FFT bins? Name the different evidence used by
   the interpolated FFT and coherent phase-increment methods.
3. After de-rotation, what does a residual phase slope say about the frequency
   estimate?
4. Why is initial phase reported at sample `n=0`? How would moving the time
   origin change the number?

## Sweep predictions and interpretation

1. Before reading the SNR sweep, predict which quantity should shrink as SNR
   rises: peak-bin grid bias, trial-to-trial spread, or both.
2. Before reading the duration sweep, predict what doubling `N` changes about
   FFT spacing and coherent evidence while per-sample SNR stays fixed.
3. Is a smaller bias the same as a smaller standard deviation? Give an example
   from one displayed estimator.
4. Why must phase bias use a circular mean? Consider estimates just below
   `+pi` and just above `-pi`.
5. A curve is slightly non-monotonic between two durations. Does that prove
   longer observation is harmful? Check fractional-bin position and the finite
   40-trial sample before deciding.

## True or false

1. `fs/N` is the smallest possible frequency-estimation error. **False.** It is
   the unpadded FFT grid spacing; sub-bin information is present in peak shape
   and coherent phase under the single-tone model.
2. Three-bin interpolation creates the same information as a longer record.
   **False.** It models the sampled peak; it does not extend observation time.
3. Frequency error can bias initial phase estimated by coherent de-rotation.
   **True.** The remaining rotation causes partial cancellation and changes the
   sum's angle.
4. The phase-increment method is unambiguous for any analog frequency.
   **False.** Its per-sample rotation is signed only inside the complex Nyquist
   interval.
5. A returned floating-point number is sufficient evidence that the tone was
   measurable. **False.** The low-amplitude case returns a candidate but fails
   the coherence gate.

## Broken-case diagnosis

1. Why does the first-to-last endpoint estimator fail even with zero noise?
   It applies `angle` to a phase change containing many turns, discards whole
   multiples of `2*pi`, and then divides the wrapped remainder by the full
   elapsed time.
2. Why does summing adjacent complex products recover this case? Each true
   adjacent step is within `[-pi, pi)`, and coherent addition reinforces that
   common rotation before one final angle is taken.
3. In the low-amplitude case, should the rejected result be interpreted as
   zero frequency? No. `NaN` means insufficient coherent evidence under the
   stated gate, not a stationary tone.
4. Name two physical recovery actions: increase received amplitude or SNR,
   observe coherently for longer, correct model mismatch, or use an estimator
   designed for the actual signal.

## Malformed input, resource, and recovery checks

- A logical seed, nonfinite SNR, complex frequency, changed sweep vector,
  noninteger record length, trial count above 40, or resource ceiling above the
  canonical value must stop before random, FFT, cleanup, or figure work.
- Ctrl+C is the timeout/cancellation path for this bounded foreground script.
  A full rerun replaces only P20-tagged figures and reconstructs `results` from
  the private seed without touching the global random stream.
- No file, network, audio, device, worker, or persistent data is opened, so
  cancellation cannot leave an external transaction to roll back.

## Teach-back completion

In two or three sentences, answer the guiding question. A complete answer must
connect accuracy to both SNR and coherent duration, distinguish FFT-bin,
interpolated-peak, and phase-increment evidence, explain wrapped phase error,
and state why a low-coherence estimate should be withheld. Also name one model
assumption that could invalidate the apparent winner.
