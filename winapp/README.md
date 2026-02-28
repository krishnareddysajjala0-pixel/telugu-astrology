This folder contains a minimal C# console app that demonstrates direct C integration (P/Invoke) with the Swiss Ephemeris DLL (swedll).

Goal
- Replace the Python `swisseph` usage with direct integration of the Swiss Ephemeris C library in a native Windows application (C#).

What you must do manually
1. Download the Swiss Ephemeris C sources from the official source (Astrodienst) or the distribution that contains the Windows build scripts.
2. Build the Swiss Ephemeris DLL for Windows (32-bit or 64-bit) using Visual Studio or MinGW. The produced DLLs are commonly named `swedll32.dll` or `swedll64.dll` (we use `swedll.dll` as a placeholder).
3. Place the built DLL (`swedll.dll`) next to the compiled C# executable (or in a folder on PATH).

How this sample works
- `SwissEphemerisPInvoke.cs` contains P/Invoke declarations for commonly used functions: `swe_set_ephe_path`, `swe_set_sid_mode`, `swe_julday`, `swe_calc_ut`, `swe_houses`, and `swe_get_ayanamsa_ut`.
- `Program.cs` demonstrates how to call these functions and reproduce the same calculations currently done in `app.py` (Julian day, planet longitudes, houses, ayanamsa).

Build and run
- Use the .NET SDK (recommended .NET 6/7/8). From this folder:

```powershell
dotnet build
dotnet run --project winapp.csproj
```

Replace the DLL
- If you have `swedll64.dll` or `swedll32.dll`, copy it as `swedll.dll` into the output folder (`bin/Debug/netX/`).

Notes
- The constant values for flags (e.g., `SEFLG_SWIEPH`, `SEFLG_SIDEREAL`) are not embedded here; check `swephexp.h` or `sweph.h` in the Swiss Ephemeris source and match them. The sample uses placeholders and documents where to set them.
- For a full native GUI app, this sample is a starting point; the calculation logic can be ported into a WinForms/WPF or native C++ GUI.

Publish (packaged Windows release)
- A convenience PowerShell script `publish-win.ps1` is included to publish a Win-x64 release and copy the Swiss Ephemeris DLL into the publish folder.

Usage:
```powershell
cd winapp
# default: Release + win-x64 (framework-dependent)
.\publish-win.ps1

# Produce a single-file self-contained x64 exe (no .NET required on target)
.\publish-win.ps1 -Configuration Release -Runtime win-x64 -SingleFile

# Or specify configuration/runtime
.\publish-win.ps1 -Configuration Release -Runtime win-x64
```

The script will run `dotnet publish` and copy `swedll.dll` (or `swedll64.dll`) from the `winapp` folder or `winapp\sweph\sweph\bin` into the publish output folder `winapp\publish\win-x64\Release`.

If the script cannot find a Swiss Ephemeris DLL, place `swedll.dll` next to `publish-win.ps1` or copy the appropriate `swedll*.dll` into `winapp\sweph\sweph\bin` and re-run the script.

ZIP package
- After publishing, the script now creates a ZIP archive of the publish folder named `winapp-<runtime>-<configuration>.zip` next to the `publish` folder (for example `winapp-win-x64-Release.zip`). This makes distribution easier — unzip next to the native `swedll.dll` if needed.
