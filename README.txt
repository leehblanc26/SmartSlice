SmartSlice 0.1.4 — Windows build package

Upload these files and the .github/workflows/build-windows.yml workflow
to your existing GitHub repository (preserve directory structure).
Go to Actions > Build SmartSlice Windows EXE > Run workflow.
Download the SmartSlice_0.1.4_Windows artifact and extract its EXE.

0.1.4 scope:
- Bambu Studio 3MF project files only; no STL import.
- No trimesh, geometry inspection, rotation, scaling, or repair.
- Only existing project_settings.config JSON keys are modified.
- All other ZIP entries are preserved byte-for-byte when extracted.
- Source file is never overwritten. Output must be a new file.
- Experimental settings: infill density/pattern, wall loops, layer height.
- No printer or filament changes; no web access; no slicing.

LIMITATIONS:
- Bambu Studio may ignore or override some project settings due to
  inherited process profiles, per-object overrides or version differences.
- Tested with synthetic Bambu-like 3MF archives, not yet verified
  against an actual Bambu Studio-generated 3MF.
- Only settings already present in project_settings.config can change.
- This does not preserve the entire compressed ZIP byte-for-byte,
  but every non-target entry's decompressed contents are identical.
- Review all changes in Bambu Studio before printing.

Testing:
python -m unittest discover -s tests -v
GitHub Actions runs tests before building the EXE.
