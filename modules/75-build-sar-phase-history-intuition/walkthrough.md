# P75 Walkthrough

## Guiding question

Why does moving one antenna create a large synthetic aperture?

Run `experiment.m` from this module directory. Keep the Command Window metrics
visible. Work through one figure at a time; the point is the physical change,
not the MATLAB syntax.

## 1. Baseline geometry, range, and phase

Open **P75 baseline geometry range and phase**.

First inspect the top panel. One antenna occupies successive points along an
80 m track; the stationary point target is at zero cross-range and 1000 m
closest slant range. The markers are not simultaneous hardware elements. They
are coherent looks acquired by the same antenna.

Next inspect slant range. It is smallest at closest approach and rises toward
both ends. Finally inspect phase. The wrapped trace cycles repeatedly, while
the range-referenced unwrapped trace reveals smooth curvature. Observe the
printed `26.656` two-way phase turns: a sub-metre one-way range excursion causes
many cycles because phase responds to the round trip in wavelengths.

## 2. Raw fast-time/aperture record

Open **P75 raw fast-time phase history**.

The top image is magnitude. Its narrow echo ridge follows the small delay
change `tau = 2R/c`. The lower image is the real part of the same complex data.
Alternating bands along platform position are carrier phase, not additional
targets. Fast time says where the echo is in range; aperture position and
coherent phase say how its path changes across the track.

Do not call this a focused SAR image. It is raw phase history before range
compression or two-dimensional image formation.

## 3. Sweep target cross-range only

Open **P75 target cross-range sweep**. The cases are `-20`, `0`, and `+20 m`.
Carrier, closest range, aperture, spatial spacing, and noise assumptions are
unchanged.

Observe where each curve reaches zero relative phase and zero range excess.
The vertex follows the target coordinate. Compare the `-20` and `+20 m` cases:
they share closest range and mirrored curvature, but their samples occur at
different platform positions. This is why equal-range targets can carry
different cross-range information.

## 4. Sweep aperture length only

Open **P75 aperture-length sweep**. The target remains centered while the
track changes through `20`, `40`, and `80 m` at the same `0.2 m` spacing.

The longer aperture sees a greater range excursion, wider angular span, and
more unwrapped two-way phase turns. The printed phase spans should increase
from about `1.667` to `6.666` to `26.656` turns. The antenna itself did not grow;
the coherent spatial record did.

Do not infer that length alone guarantees useful resolution. Sparse position
sampling, phase drift, motion error, and target decorrelation can prevent the
samples from combining coherently.

## 5. Intentionally broken magnitude-only case and recovery

Open **P75 magnitude-only failure and recovery**.

The explicit coherent score tests candidate cross-range paths. In the recovered
panel, the unchanged complex aperture record peaks at the true `0 m` target.
The broken path applies `abs` first. The echo remains strong, but phase curvature
is gone and the best normalized coherent score stays below the reviewed bound.

Recovery means returning to the unchanged I/Q record, not estimating lost phase
from magnitude. If acquisition stored only magnitude, this recovery would be
impossible.

## 6. Connect the concept

P36 used phase progression across time to reveal Doppler. P61-P63 used phase
across physical sensors to steer an array. Here, known platform motion converts
successive coherent looks into spatial samples. P76 will compress fast time;
P77 will reuse path compensation across candidate image points; P78 will treat
range-cell migration; P80 will show why position error blurs coherent focusing.

## Cancellation, rerun, recovery, and rollback

The script starts with no worker, timer, callback, file write, and no background
task. Pressing Ctrl+C cancels only the foreground run. Close partial P75 figures
and rerun from the top; the private seed reproduces the same noise without
changing MATLAB's global random stream.

If a control fails validation, restore the reviewed visible values and rerun
from the top. Repository rollback means restoring P75 to its scaffold README,
removing its four implementation artifacts/test/evidence, and changing only
P75 manifest status back to `scaffolded`. Preserve learner progress, P74, and
whatever status later batches have reached.

## Completion handoff

Use `checks.md`. Give a two- or three-sentence teach-back that mentions known
platform positions, two-way phase curvature, and why two equal-closest-range
targets at different cross-range positions have shifted phase histories.
