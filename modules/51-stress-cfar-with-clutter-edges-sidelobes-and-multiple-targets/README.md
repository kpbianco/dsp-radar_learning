# P51: Stress CFAR with Clutter Edges, Sidelobes, and Multiple Targets

**Phase 5: Detection and CFAR**  
**Status:** Scaffolded; implementation batch `P51` is pending

## Guiding question

Where do standard CFAR assumptions break?

## Experiment

Create a scenario combining a clutter edge, a strong target with sidelobes, weak neighboring targets, and nonuniform noise.

## Procedure

Run CA, GO, SO, and OS variants with the same nominal Pfa. Compare masks and classify each miss or false alarm by cause.

## What this should teach

No CFAR variant is universally best; detector choice depends on background homogeneity and target density.

## Completion condition

You can explain every major detector disagreement using the training-cell contents.

## Start or implement

```bash
./bin/learn start 51
```

If this module is scaffolded, tutor mode may review this brief but must not pretend the experiment is complete. Activate Portfolio Control batch `P51` to add the runnable MATLAB experiment, explanation, walkthrough, checks, validation, and evidence.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Stress CFAR with Clutter Edges, Sidelobes, and Multiple Targets". The guiding question is: "Where do standard CFAR assumptions break?" Use this experiment: Create a scenario combining a clutter edge, a strong target with sidelobes, weak neighboring targets, and nonuniform noise. Have me perform these actions: Run CA, GO, SO, and OS variants with the same nominal Pfa. Compare masks and classify each miss or false alarm by cause. The main concept I must learn is: No CFAR variant is universally best; detector choice depends on background homogeneity and target density. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Files currently present

- `README.md`
