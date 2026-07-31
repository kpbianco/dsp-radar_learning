# Walkthrough

## Guiding question

How do amplitude, frequency, and phase appear in time and in the complex plane?

Run `experiment.m` as one script, or run one `%%` section at a time after the
baseline controls have been created. Change only the named control during each
step so the cause remains visible.

## Baseline: connect the time plot to the IQ plot

Use the supplied baseline \(A=1\), \(f_0=5\) Hz, \(\phi=\pi/6\), and
\(f_s=200\) samples/s.

1. In the first figure, compare the real cosine with the I component. They
   should coincide sample for sample.
2. Locate the starting point on the IQ circle. It should be at an angle of
   \(\pi/6\), with I positive and Q positive.
3. Read the printed metrics. Expect 40 samples/cycle, 5 cycles in the
   one-second record, and projection and radius errors near floating-point
   roundoff.

**One observation question:** Following the ordered points and arrow, which
direction does the positive-frequency phasor rotate?

Expected observation: positive frequency rotates counterclockwise on the
I-right, Q-up axes; negative frequency rotates clockwise.

## Sweep 1: amplitude changes size

Run the amplitude sweep with `[0.5 1.0 1.5]`.

- Predict which circle has the largest radius.
- Observe that the radii are 0.5, 1.0, and 1.5 amplitude units.
- Temporarily set the baseline `A` to `0.5` and rerun the baseline sections.
  Peak time-domain amplitude and IQ radius should both halve, while samples per
  cycle and cycles in the record remain unchanged.

Physical connection: receiver gain scales I and Q together; gain alone does
not create a frequency shift.

## Sweep 2: phase changes the starting point

Run the phase sweep with `[0 pi/4 pi/2]`.

- Before looking at the right panel, predict the initial I and Q values for
  \(\phi=\pi/2\).
- Observe that all time traces have the same peak spacing.
- Match each trace's value at \(t=0\) to its colored starting point on the IQ
  circle.

Expected observation: \(\phi=\pi/2\) begins near \(I=0,Q=1\). Phase moves the
starting point around the same-radius circle without changing its rate.

## Sweep 3: frequency changes rotation rate

Run the frequency sweep with `[2.5 5 10]` Hz.

- Count the cycles in the common 0.4-second view: expect 1, 2, and 4 cycles.
- In the lower panel, compare the slopes of angle advanced versus time.
- Observe that the time traces all have the same peak magnitude and begin with
  the same phase.

Physical connection: a frequency or Doppler shift appears as a steady phase
slope in complex I/Q data.

## Broken case: undersampling hides the true rotation

Run the broken-case section with `fs_bad = 8` samples/s.

The 5 Hz tone exceeds the 4 Hz Nyquist limit. The plotted 5 Hz waveform and
the apparent 3 Hz waveform pass through every measurement point, and the
printed sample agreement error should be near roundoff. The samples alone
cannot tell which continuous waveform produced them.

Common mistake: the smooth 3 Hz dashed curve is not a noisy estimate of the
5 Hz tone. It is a different waveform that is exactly indistinguishable at
those sample times.

## Recovery

Restore `fs = 200` and rerun the baseline. If an edited `fs` or `duration`
would create more than 5000 samples, the resource guard stops before allocating
the time vector; reduce one of those controls and rerun.

Then try `fs_bad = 12` and `fs_bad = 20`. Both exceed the strict Nyquist rate
for a 5 Hz tone, so the early Nyquist assertion is expected to stop: those
values no longer create the failure this section is designed to demonstrate.
That stop is recovery evidence, not a new broken result. Finally restore
`fs_bad = 8` and rerun the section so its intentional alias and all assertions
pass. The broken-case controls also stop before allocation unless `fs_bad` is
one finite positive scalar and `duration*fs_bad` is an integer from 2 through
5000 samples.

You are ready for the checks when you can predict time-domain peak height,
starting I/Q position, rotation rate, and rotation direction before rerunning
the relevant section.
