# Windows Installation Guide for ExplainFlow

This guide addresses the common "Fatal error in launcher" issue on Windows and provides best practices for installing Python packages.

## The Problem

When running `pip install explainflow` on Windows (especially with Python 3.12+), you may encounter:

```
Fatal error in launcher: Unable to create process using 
'"C:\Users\...\Python312\python.exe" "C:\Users\...\Scripts\pip.exe" install explainflow': 
The system cannot find the file specified.
```

## Root Cause

This is a **Windows pip launcher issue**, not a problem with explainflow specifically. It occurs because:

1. **pip.exe is a launcher** - On Windows, `pip.exe` is a small executable wrapper that calls Python with the pip module
2. **Embedded paths** - The launcher stores the absolute path to Python inside the executable
3. **Path corruption** - This path can become invalid if:
   - Python was moved or reinstalled
   - Multiple Python versions are installed
   - The installation path contains spaces
   - Windows file system case sensitivity issues

## Solutions (Choose One)

### Solution 1: Use `python -m pip` (Recommended)

Always use the module execution syntax on Windows:

```powershell
# Instead of: pip install explainflow
python -m pip install explainflow

# Or with specific Python version
py -3.12 -m pip install explainflow
```

**Why this works**: It bypasses the pip.exe launcher entirely and runs pip as a Python module directly.

### Solution 2: Repair pip

Force-reinstall pip to regenerate the launcher with correct paths:

```powershell
python -m pip install --upgrade --force-reinstall pip
```

After this, `pip install` should work normally.

### Solution 3: Use Virtual Environments (Best Practice)

Virtual environments avoid most path issues and are recommended for all Python projects:

```powershell
# Create a virtual environment
python -m venv myproject_env

# Activate it
.\myproject_env\Scripts\Activate.ps1

# Now pip works normally inside the venv
pip install explainflow
```

### Solution 4: Reinstall Python (Nuclear Option)

If nothing else works:

1. Uninstall Python completely
2. Delete leftover folders:
   - `C:\Users\<YourName>\AppData\Local\Programs\Python`
   - `C:\Python*` (if exists)
3. Reinstall Python with these options:
   - ✅ "Add Python to PATH"
   - ✅ "Install for all users" (optional, installs to `C:\Program Files`)
   - Or install to a simple path like `C:\Python312`

## Verification

After installing, verify explainflow works:

```powershell
python -c "from explainflow import explain; print('ExplainFlow installed successfully!')"
```

## Quick Reference

| Situation | Command |
|-----------|---------|
| Normal install | `python -m pip install explainflow` |
| Upgrade | `python -m pip install --upgrade explainflow` |
| With extras | `python -m pip install explainflow[all]` |
| Fix pip | `python -m pip install --upgrade --force-reinstall pip` |
| Check version | `python -m pip show explainflow` |

## Still Having Issues?

1. Check which Python: `where python`
2. Check pip location: `python -m pip --version`  
3. List installed packages: `python -m pip list`
4. Open an issue with the output of the above commands

## Further Reading

- [Stack Overflow: pip launcher issue](https://stackoverflow.com/q/24627525)
- [Python Docs: Installing packages](https://packaging.python.org/en/latest/tutorials/installing-packages/)
- [Python Docs: Virtual environments](https://docs.python.org/3/library/venv.html)
