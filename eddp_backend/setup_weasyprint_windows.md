# WeasyPrint Windows Setup Guide

## Problem
WeasyPrint requires GTK/Pango/Cairo native libraries on Windows. The installed GTK-Runtime at `C:\Program Files\Gtk-Runtime\bin` is incompatible (missing required Pango symbols).

## Solution: Install MSYS2 with Compatible GTK

### Step 1: Install MSYS2

1. Download MSYS2 installer from: https://www.msys2.org/
2. Run the installer and install to `C:\msys64` (default location)
3. Complete the installation

### Step 2: Install GTK Dependencies

Open **MSYS2 MINGW64** terminal and run:

```bash
# Update package database
pacman -Syu

# Install GTK3 and dependencies required by WeasyPrint
pacman -S mingw-w64-x86_64-gtk3 mingw-w64-x86_64-pango mingw-w64-x86_64-cairo mingw-w64-x86_64-gdk-pixbuf2 mingw-w64-x86_64-gobject-introspection
```

### Step 3: Set Environment Variable

Add the MSYS2 bin directory to your system:

**Option A: System-wide (Recommended)**
1. Press `Win + X` and select "System"
2. Click "Advanced system settings"
3. Click "Environment Variables"
4. Under "System variables", find "Path" and click "Edit"
5. Add new entry: `C:\msys64\mingw64\bin`
6. Move it to the top of the list
7. Click OK on all dialogs

**Option B: Just for this project**
Create a `.env` file in the backend directory with:
```
WEASYPRINT_DLL_DIRECTORIES=C:\msys64\mingw64\bin
```

### Step 4: Restart Backend

After installing and setting environment variables, restart your backend server for changes to take effect.

## Alternative: Quick Install Script

Run the PowerShell script `install_gtk_for_weasyprint.ps1` (requires admin rights).

## Verification

Run the debug script to verify installation:
```cmd
cd eddp_backend
python debug_pdf.py
```

## Troubleshooting

### Issue: "libpango-1.0-0.dll not found"
- Ensure MSYS2 is installed at `C:\msys64`
- Verify GTK packages are installed in MSYS2
- Check that `C:\msys64\mingw64\bin` is in your PATH or WEASYPRINT_DLL_DIRECTORIES

### Issue: "missing required symbol"
- The GTK runtime is outdated or incompatible
- Uninstall old GTK runtimes from Program Files
- Use MSYS2 version (most up-to-date)

### Issue: Still not working after installation
1. Completely close VS Code and any Python processes
2. Reopen VS Code
3. Restart the backend server
4. Try again
