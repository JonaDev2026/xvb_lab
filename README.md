# XVB Player — Lab

This repository is the development and testing environment for XVB Player. Changes are tested here before they are potentially transferred to the Stable repository.

## Goals

- Develop and verify support for X11 and Wayland.
- Test changes without affecting the Stable version.
- Prepare and verify packages for the main Linux distributions.
- Move to Stable only changes that have passed testing.

The project maintains a single application built with Python, Tkinter, and libmpv. No parallel interfaces or player rewrites are planned.

## Packages

The repository includes three GitHub Actions workflows:

| Distribution | Package |
|---|---|
| Arch Linux and derivatives | `.pkg.tar.zst` |
| Debian and derivatives | `.deb` |
| Fedora and derivatives | `.rpm` |

Each workflow can be started automatically when a GitHub Release is published, or manually from **Actions**.

Once the build is complete, the package is attached to the corresponding Release. The Debian and Fedora workflows also verify that the version in the tag matches the version declared in `xvb.py`.

## Running from source

```bash
python3 xvb.py
```

XVB Player's Python and system dependencies are required, including Tkinter and libmpv.

## Development workflow

1. Changes are developed and built in Lab.
2. Packages are installed and tested on the relevant distributions.
3. Verified changes can be transferred to the Stable repository.

Lab and Stable are independent repositories. Experimental work does not automatically modify Stable.
