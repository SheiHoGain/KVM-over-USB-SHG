# Third-Party Notices

This repository is maintained by `SheiHoGain` as a fork of `wevsty/KVM-over-USB`.

The source code in this repository is distributed under the MIT License. It also depends on, and some release artifacts may redistribute, third-party components with their own licenses and copyright notices.

## Upstream Projects

- `wevsty/KVM-over-USB`: direct upstream project for this fork.
- `ElluIFX/KVM-Card-Mini-PySide6`: important upstream source reference mentioned in the project documentation.
- `binnehot/KVM-over-USB`: earlier related upstream project referenced in the project documentation.

## Runtime And Packaging Dependencies

The project source and/or release artifacts may include or depend on components such as:

- PySide6 / Qt / Shiboken6
- Qt Multimedia plugins and related codec backends
- OpenSSL
- NumPy
- OpenCV (`opencv-python-headless`)
- pywin32
- comtypes
- hidapi
- pyserial
- PyYAML
- loguru
- pygrabber
- pych9329

## Release Artifact Notice

If you redistribute the packaged client from `client/releases/`, you should also redistribute:

- this file
- the root `LICENSE`
- any third-party license texts required by bundled dependencies

For complete and authoritative license terms, please refer to the original upstream projects, the corresponding package metadata in your build environment, and any license files bundled into the final release package.
