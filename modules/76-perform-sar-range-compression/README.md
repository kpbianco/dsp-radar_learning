# P76: Perform SAR Range Compression

**Phase 9: SAR, ISAR, Passive Radar, and Capstone**  
**Status:** Scaffolded; implementation batch `P76` is pending

## Guiding question

What information is created before azimuth focusing begins?

## Experiment

Transmit an LFM pulse at each aperture position, simulate several point targets, and matched-filter along fast time.

## Procedure

Display raw data and range-compressed data as aperture position versus range bin. Vary waveform bandwidth and target spacing in range.

## What this should teach

Range compression localizes targets in slant range while preserving the aperture-dependent phase needed for cross-range focusing.

## Completion condition

Targets form clear range histories and range resolution follows chirp bandwidth.

## Start or implement

```bash
./bin/learn start 76
```

If this module is scaffolded, tutor mode may review this brief but must not pretend the experiment is complete. Activate Portfolio Control batch `P76` to add the runnable MATLAB experiment, explanation, walkthrough, checks, validation, and evidence.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Perform SAR Range Compression". The guiding question is: "What information is created before azimuth focusing begins?" Use this experiment: Transmit an LFM pulse at each aperture position, simulate several point targets, and matched-filter along fast time. Have me perform these actions: Display raw data and range-compressed data as aperture position versus range bin. Vary waveform bandwidth and target spacing in range. The main concept I must learn is: Range compression localizes targets in slant range while preserving the aperture-dependent phase needed for cross-range focusing. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Files currently present

- `README.md`
