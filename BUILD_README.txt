SmartSlice 0.1.1 — Windows executable build package

This ZIP is SOURCE + GitHub Actions build workflow, not a precompiled .exe.

To build on GitHub without installing Python on your PC:
1. Create a new GitHub repository.
2. Upload the contents of this folder, INCLUDING .github/workflows/build-windows.yml.
3. Open the repository's Actions tab.
4. Choose 'Build SmartSlice Windows EXE', click 'Run workflow'.
5. Open the completed workflow run and download the SmartSlice_0.1.1_Windows artifact.
6. Extract SmartSlice_0.1.1.exe and run it on Windows.

The executable is not code-signed. Windows SmartScreen may warn about unknown publishers.

Known functional limitations carried forward from 0.1:
- 3MF setting compatibility with Bambu Studio is UNVERIFIED.
- Existing Bambu 3MF project metadata is NOT preserved.
- Orientation is a simple bounding-box heuristic, not full overhang analysis.
- Filament temperature, flow and printer-specific settings are NOT optimized.
- Do not print without verifying the imported settings in Bambu Studio.
- No slicing or internet requests in the application.
