# P77 Lesson: Focus SAR with Backprojection

## Guiding question

How does compensating the correct path length focus a point in an image?

## One pixel is one path hypothesis

P76 produced a range-compressed phase history: aperture position indexes rows,
slant range indexes columns, and every complex target ridge retains coherent
carrier phase. Backprojection asks a concrete question at each candidate ground
coordinate `(x,y)`: if a point target were there, which range sample and phase
should every radar position have observed?

For platform cross-range position `x_p`, the flat-ground slant-range hypothesis
is

```text
R_p(x,y) = sqrt((x_p-x)^2 + y^2).
```

The synthetic measurement for target `k` is

```text
s_p(r) = A_k g(r-R_p,k)
         exp(-j 4*pi*(R_p,k-R_ref)/lambda) + n_p(r),
```

where `g` is the visible range-compressed point response and `n` is seeded
complex noise. `R_ref` is one fixed reference shared by synthesis and imaging;
it removes a common carrier rotation without changing focus.

## The transparent backprojection sum

For every pixel, P77 linearly interpolates the complex row at its hypothesized
range, applies the conjugate path phase, and accumulates aperture looks:

```text
I(x,y) = sum_p interp{s_p(r), R_p(x,y)}
                 exp(+j 4*pi*(R_p(x,y)-R_ref)/lambda).
```

The plus sign is compensation for the negative propagation phase. At a true
target coordinate, interpolation lands on its range ridge and phase
compensation makes all terms point nearly the same way in the complex plane.
Their voltage grows approximately with aperture-look count. At a wrong pixel,
either the range sample misses the ridge or residual phase causes cancellation.

This is delay-and-sum beamforming with a curved, range-dependent steering law.
The operation is written in a local base-MATLAB helper, including the
fractional range index, linear interpolation weights, phase factor, and sum; no
toolbox backprojection object hides it.

## Read the partial-aperture sweep

The first sweep changes only the number of centered aperture looks: `21`, `61`,
then `121`. Each image is divided by its look count for fair displayed
amplitude, while the unnormalized true-pixel voltage is retained separately.
More correct looks increase coherent voltage and enlarge the observed angular
span. In the reviewed target cut, the full `-3 dB` cross-range width therefore
shrinks monotonically.

Do not infer that adding arbitrary measurements always sharpens an image. The
looks must be phase coherent, sufficiently sampled, and paired with the correct
platform geometry. P79 owns the fuller aperture-length and window trade study.

## Read the assumed-path-error sweep

The second sweep leaves the measurement unchanged and perturbs only the path
used by the imager. It adds a sinusoidal range-direction platform error across
the assumed aperture:

```text
delta_y[p] = A_error sin(2*pi*(p-1)/(P-1)),
R_assumed = sqrt((x_p-x)^2 + (y+delta_y[p])^2).
```

At `5 GHz`, wavelength is `60 mm`. A `10 mm` one-way range error can therefore
create roughly `4*pi*0.010/0.060 = 2.09 rad` of two-way phase error. Because the
error varies across the aperture, it cannot be removed by one constant phase
rotation. The true-pixel sum loses coherence and the point response defocuses.

The deliberately broken path is the `10 mm` case. Recovery does not regenerate
data or estimate a correction from the blurred image. It reuses the
byte-for-byte retained complex phase history and restores the correct geometry.
The existing full-aperture baseline is the `0 mm` sweep image; only the `5 mm`
and `10 mm` cases require additional wrong-path image formation. Recovery then
performs a fresh correct-path backprojection, and cumulative accounting checks
that all executed pixel-look work equals preflight and stays below the cap.

## Why a constant geometry error needs careful language

A constant path offset multiplies the whole coherent sum by one common phase;
it does not necessarily blur magnitude. Likewise, in this flat two-dimensional
straight-track model, a constant wrong platform height can be absorbed partly
as a biased ground-range coordinate, producing a sharp image at the wrong
location. P77 therefore uses a non-rigid path error for a guaranteed defocus
demonstration. "Wrong geometry" may mean bias, blur, or both depending on
whether its residual error varies across aperture position.

## Range and cross-range point responses

The final image is not judged only by a bright picture. For a selected target,
P77 plots one range cut at the target cross-range and one cross-range cut at the
target range. Interpolated half-power crossings give full `-3 dB` widths in
metres. Local search windows verify both modeled targets focus at their correct
coordinates rather than allowing the stronger target to hide the weaker one.

The range width is mainly inherited from the range-compressed response. The
cross-range width depends on wavelength, slant range, and observed aperture;
for a broadside small-angle approximation,

```text
Delta_x is proportional to lambda*R/L_aperture.
```

P79 will treat the constants, aperture length, and windowing more carefully.

## Limiting cases and common mistakes

- **One aperture position:** range localization remains, but there is no
  synthetic-aperture cross-range discrimination.
- **Zero bandwidth:** the range response broadens, so interpolation cannot
  localize targets finely in range.
- **Correct range, discarded phase:** magnitude-only samples cannot perform a
  coherent backprojection sum.
- **Wrong phase sign:** measured and predicted propagation phase reinforce
  rotation instead of canceling it.
- **Nearest-bin-only sampling:** coarse range quantization can introduce extra
  phase/amplitude error; the script uses visible linear interpolation.
- **Constant path offset:** it may rotate image phase without defocusing image
  magnitude.
- **Constant wrong height:** it may bias ground-range location rather than
  guarantee blur in a flat 2-D scene.
- **Non-rigid path error:** aperture-dependent residual phase spreads and
  cancels the point response.
- **Sparse aperture sampling:** adjacent phase can alias even with exact range
  interpolation.
- **Long aperture:** backprojection follows path-dependent range, but P78 owns
  the dedicated range-cell-migration experiment.
- **Point-target model:** terrain, layover, shadow, antenna pattern,
  propagation loss, extended reflectivity, squint, and autofocus are omitted.

## Dependencies, compatibility, and resources

P18 provides I/Q phase, P30 provides two-way delay, P32 provides compressed
range response, P37 provides matrix orientation, P61-P63 provide coherent
spatial sums, P75 supplies SAR phase history, and P76 is the governed direct
dependency. The script targets base MATLAB R2016b or newer with no optional
toolbox, performs no file/network I/O, creates exactly six tagged figure groups,
caps backprojection work at 5,000,000 pixel-look operations (4,451,590 are
scheduled by the reviewed controls), and caps P77's incremental live workspace
at 5,000,000 eight-byte value equivalents. The script runs the experiment in a
local function workspace, so unrelated caller variables are not charged to the
experiment and a deterministic rerun does not inherit prior working arrays.

## Completion connection

You are ready to continue when you can say: backprojection focuses a pixel by
sampling each range-compressed look at that pixel's predicted slant range,
canceling the corresponding two-way carrier phase, and summing the aligned
complex values; an aperture-varying path error leaves residual phase and
defocuses the point.
