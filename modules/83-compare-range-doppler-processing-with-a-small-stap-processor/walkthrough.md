# P83 walkthrough: From a Cluttered Doppler Cell to a Joint Notch

## Guiding question

When is Doppler filtering alone insufficient against clutter?

Run `experiment.m` from this module directory. Keep the Command Window visible
and inspect one figure group at a time. The script uses base MATLAB R2016b+
with private deterministic samples and writes no files.

## Baseline transition 1: locate the coupled clutter

Open **P83 angle-Doppler geometry**.

1. Trace the colored ground patches from negative angle/negative Doppler
   through broadside and toward positive angle/positive Doppler.
2. Locate the magenta target at `12.5 deg` and `0.125 cycles/pulse`.
3. Follow its vertical dashed line down to the same-angle clutter ridge.

Expected observation: the target is close to the ridge, and other clutter
angles occupy nearly the same Doppler. A Doppler coordinate by itself does not
identify the source.

The vertical separation is not range. It is normalized Doppler distance from
the local moving-ground return.

## Baseline transition 2: compare the same data two ways

Open **P83 conventional versus STAP maps**.

1. Both panels use the same 4-element by 8-pulse snapshots, the same range
   cells, and the same color limits.
2. Find range cell 25 and normalized Doppler 0.120 in each panel.
3. Locate each panel's global maximum.

Expected observation: strong clutter cells outrank the target in the fixed
beam plus Doppler-bank map. The target owns the clean joint adaptive map.

The map color is normalized output power in dB. It is suitable for comparing
visibility here, but it is not absolute received power, a threshold, `Pd`, or
operational clutter cancellation.

## Baseline transition 3: separate visibility from average SCNR

Open **P83 target visibility and SCNR**.

1. In the left panel compare the two Doppler slices at range cell 25.
2. In the right panel read output SCNR computed from known synthetic target,
   clutter, and noise component powers.

Expected observation: the adaptive slice isolates the target neighborhood and
the small STAP processor gains more than 20 dB of reviewed SCNR over the fixed
processor. This known-component ruler is simulation knowledge; the adaptive
weight itself used only neighboring-range sample covariance.

## Controlled change 1: move away from the ridge

Use the left panel of **P83 ridge and support sweeps**. The target Doppler
offset takes `[0.01 0.03 0.06 0.10]` cycles per pulse. Target angle, power,
clutter record, clean covariance, array, CPI, and loading stay fixed.

Expected observation: very near the ridge, joint target and clutter signatures
are difficult to separate. As offset grows, STAP SCNR rises sharply because
the target pair leaves the learned clutter subspace. The fixed beam plus
Doppler filter improves much less.

Prediction check: at exactly zero offset and the same angle, could any weight
both preserve and null that one vector? No; the two constraints would
contradict each other.

## Controlled change 2: reduce clean training support

Use the right panel. The processor sees prefixes `[8 16 24 36]` of the same
clean neighboring-range record.

Expected observation: the 8-cell covariance is low rank before loading and its
loaded condition number is large. Output SCNR improves as the fixed record
prefix grows to 36 cells.

Do not conclude that arbitrarily distant cells always help. This controlled
scene is homogeneous; real terrain, jammers, and targets can make secondary
cells nonrepresentative.

## Intentionally broken case: contaminate covariance training

Open **P83 contaminated training and recovery**.

1. The left panel was formed after adding a 30 dB target-like component to 25%
   of the clean training snapshots.
2. The measurement at range cell 25 did not change.
3. The target no longer owns the adaptive map and its contrast collapses.

The solver still runs and preserves its exact assumed steering vector. In this
reviewed draw, actual-target output power changes by only about `-0.62 dB`;
known clutter-plus-noise output rises by about `22.86 dB`. The collapsed SCNR
and normalized-map contrast therefore demonstrate lost interference rejection,
not a deep desired-target null.

## Recovery: rebuild from retained clean data

The right panel discards the contaminated covariance and recomputes from the
unchanged clean training matrix. The original CUT and all background range
cells are also unchanged.

Expected observation: the recovered map, target weight, SCNR, and visibility
exactly reproduce the clean baseline. Recovery does not tune around the answer
or mutate an external state.

If a foreground run or graphics render blocks, interrupt with Ctrl+C and rerun
the script. All loops and allocations are bounded. There is no file, network,
worker, timer, GPU, callback, checkpoint, or asynchronous task to cancel.
Startup closes only stale figures tagged `P83` and rebuilds the inputs.

## Connect the result

Complete this sentence aloud:

> Doppler filtering alone is insufficient when moving-platform clutter at
> different angles occupies the target Doppler, because ...

A complete answer should mention coupled spatial and slow-time phase, joint
covariance, target-free neighboring range cells, and the impossibility of
separating identical signatures.

## Completion handoff

Use `checks.md` for observation and prediction checks. Before personal
completion, teach back:

1. why moving ground creates a ridge rather than one zero-Doppler line;
2. why the conventional path is fixed even though it has a spatial beam;
3. how the 32-dimensional sample covariance changes the joint response;
4. why small or contaminated training can make adaptation worse; and
5. what STAP does not improve or validate.

To roll back P83, restore its scaffold README, remove only its four added
lesson artifacts, tests, and evidence, return only P83's manifest/catalog state
to scaffolded, and derive the public frontier from that state. Preserve P82,
P84 identity and any later metadata/status, learner state, governed contracts,
and all forbidden paths.

Repository validation is static/simulated unless an actual MATLAB command,
version, output, and artifacts are retained. It does not establish physical
radar/HIL, field, RT1/RT2, Unreal, signing, deployment, or production evidence.
