# P79: Compare SAR Resolution, Aperture Length, and Windowing

**Phase 9: SAR, ISAR, Passive Radar, and Capstone**  
**Status:** Scaffolded; implementation batch `P79` is pending

## Guiding question

What controls range and cross-range resolution and sidelobes?

## Experiment

Image closely spaced point targets while varying waveform bandwidth, aperture length, sampling spacing, and aperture taper.

## Procedure

Measure point-spread width and sidelobes in both dimensions. Deliberately undersample the aperture to create grating-lobe-like aliases.

## What this should teach

Range resolution depends mainly on transmitted bandwidth; cross-range resolution depends on synthetic aperture and geometry; taper trades sidelobes for width.

## Completion condition

You can independently change range and cross-range resolution and explain the resulting point-spread function.

## Start or implement

```bash
./bin/learn start 79
```

If this module is scaffolded, tutor mode may review this brief but must not pretend the experiment is complete. Activate Portfolio Control batch `P79` to add the runnable MATLAB experiment, explanation, walkthrough, checks, validation, and evidence.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Compare SAR Resolution, Aperture Length, and Windowing". The guiding question is: "What controls range and cross-range resolution and sidelobes?" Use this experiment: Image closely spaced point targets while varying waveform bandwidth, aperture length, sampling spacing, and aperture taper. Have me perform these actions: Measure point-spread width and sidelobes in both dimensions. Deliberately undersample the aperture to create grating-lobe-like aliases. The main concept I must learn is: Range resolution depends mainly on transmitted bandwidth; cross-range resolution depends on synthetic aperture and geometry; taper trades sidelobes for width. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Files currently present

- `README.md`
