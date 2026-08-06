# P65 walkthrough: Observe, Adapt, Mismatch, Recover

Guiding question: How can a beamformer place data-dependent nulls on interference?

Run `experiment.m` once from this module directory. The script creates five
figures and retains the numerical record in `p65_results`.

## Baseline observation 1: the covariance contains spatial structure

Look only at **P65 covariance structure**.

The covariance magnitude is not diagonal because the two plane waves create
correlated phase relationships across sensors. Its eigenvalue plot has a large
interference-dominated direction above the receiver-noise floor.

Expected observation: the matrix has organized off-diagonal magnitude and a
wide eigenvalue spread. This is the information MVDR uses; it is not given the
interferer angle as an optimization input.

## Baseline observation 2: fixed beam versus adaptive null

Open **P65 conventional and MVDR patterns**. Both curves cross `0 dB` at the
`3 deg` desired look because both obey unit response there.

Expected observation: near the `30 deg` interferer, MVDR makes a substantially
deeper response than the conventional fixed beam. The MVDR curve may look less
smooth or place other ripples differently because its weights came from this
finite data record.

Then inspect **P65 output component powers**. Compare desired, interference,
and receiver-noise bars before reading the output-SINR annotation.

Concept connection: the improvement comes from reducing interference power
while preserving the assumed desired response. Null depth alone is incomplete;
an extreme weight norm could also amplify noise.

## Sweep 1: snapshot count

Open **P65 snapshot sweep**. The points use `[4 8 16 32 64 128 256]`
snapshots as nested prefixes of the same generated record. Only the amount of
covariance evidence changes.

Expected observations:

- the raw covariance is singular or poorly conditioned at the shortest counts;
- fixed diagonal loading keeps every reviewed solve finite;
- the learned interferer response fluctuates rather than improving at every
  point; and
- the long-record output SINR is better than the most sample-starved result.

One-variable change: edit only `snapshot_sweep = [4 8 16 32 64 128 256];`
within the reviewed bounds. Do not regenerate a different random record for
each point; that would mix snapshot-count effects with lucky-scene effects.

## Sweep 2: diagonal loading under steering mismatch

Open **P65 loading, mismatch, and recovery**. The top panels hold eight
snapshots, the true source at `3 deg`, and the assumed constraint at `6 deg`.
Only dimensionless loading `alpha` changes.

Expected observations:

- almost zero loading gives weak response at the true desired direction and
  poor output SINR;
- moderate loading improves true-direction response and white-noise behavior;
- excessive loading moves toward conventional behavior and weakens the
  data-adaptive interferer null.

There is no universal best `alpha`; the plot shows one deterministic mismatch
tradeoff, not an automatic loading-selection algorithm.

## Broken case: self-nulling

The bottom-left pattern compares three weight vectors made from the same
four-snapshot covariance:

- **broken:** wrong look direction and almost no loading;
- **loaded:** the same wrong look direction with moderate loading; and
- **recovered:** moderate loading with the correct steering vector.

Expected observation: the broken pattern preserves the wrong `6 deg`
constraint but depresses the true `3 deg` source. Loading broadens robustness;
correcting the steering model restores exact unit response at truth.

Common interpretation mistake: saying that loading learned the correct angle.
It did not. It reduced sensitivity to mismatch. Only the corrected steering
vector moves the hard constraint back to `3 deg`.

## Recovery

The recovered weight reuses the same sample-starved covariance, applies the
reviewed positive load, and restores the constraint to the true `3 deg`
steering vector. No source, noise, or snapshot is regenerated.

## Failure interpretation checklist

- No null near the interferer: check covariance evidence, steering convention,
  and whether the interferer moved.
- Desired response below `0 dB`: check whether the constraint used the true
  steering vector; the unit-response assertion applies to the assumed vector.
- Huge noise gain: suspect an ill-conditioned solve or insufficient loading.
- A shallower null after heavy loading: expected robustness/adaptivity tradeoff,
  not necessarily an implementation failure.
- A short-record point outperforming a neighbor: finite-record fluctuation;
  judge trends and component powers, not one lucky null sample.

## Cancellation, rerun, and resource behavior

Pressing `Ctrl+C` stops the foreground script. There is no worker, timer,
network request, file output, checkpoint, or partial persistent state. Rerun
the script to reconstruct the same bounded private record. Startup closes only
figures tagged `P65`, so unrelated figures and MATLAB's global random state are
preserved.

The reviewed ceilings are 16 elements, 512 snapshots, 1,001 scan samples,
eight sweep cases, 30,000 private values per request, 600,000 working numeric
values, and five tagged figures. Input validation rejects malformed or
oversized controls before data and plots are constructed.

When these observations make sense, use `checks.md` and give the short
teach-back. Do not mark the module complete from plot production alone.
