from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
from pathlib import Path


def _run(args: list[str], cwd: Path) -> None:
    result = subprocess.run(args, cwd=str(cwd))
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def _venv_python(project_root: Path, venv_dir: str) -> Path:
    venv_path = (project_root / venv_dir).resolve()
    if os.name == "nt":
        python_path = venv_path / "Scripts" / "python.exe"
    else:
        python_path = venv_path / "bin" / "python"
    if not python_path.exists():
        raise FileNotFoundError(str(python_path))
    return python_path


def _venv_tool(project_root: Path, venv_dir: str, tool_name: str) -> Path:
    venv_path = (project_root / venv_dir).resolve()
    if os.name == "nt":
        tool_path = venv_path / "Scripts" / tool_name
    else:
        tool_path = venv_path / "bin" / tool_name
    if not tool_path.exists():
        raise FileNotFoundError(str(tool_path))
    return tool_path


def _has_module(python_path: Path, module_name: str) -> bool:
    result = subprocess.run(
        [str(python_path), "-c", f"import {module_name}"],
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def _pip_install(python_path: Path, packages: list[str], cwd: Path) -> None:
    args = [
        str(python_path),
        "-m",
        "pip",
        "install",
        "--disable-pip-version-check",
        "--upgrade",
        *packages,
    ]
    result = subprocess.run(args, cwd=str(cwd))
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def _ensure_tools(python_path: Path, cwd: Path, install_missing: bool) -> None:
    required: list[tuple[str, str]] = [
        ("black", "black"),
        ("flake8", "flake8"),
        ("nuitka", "nuitka"),
    ]
    extra: list[str] = []
    for module_name, package_name in required:
        if _has_module(python_path, module_name):
            continue
        if not install_missing:
            raise RuntimeError(
                f"Missing module: {module_name}. "
                f"Install it in venv: {python_path}"
            )
        extra.append(package_name)
    if extra:
        _pip_install(python_path, extra, cwd)

    if _has_module(python_path, "flake8") and not _has_module(
        python_path, "flake8_bugbear"
    ):
        if install_missing:
            _pip_install(python_path, ["flake8-bugbear"], cwd)


def _create_requirements(project_root: Path, python_path: Path) -> None:
    requirements_path = project_root / "data" / "requirements.bin"
    requirements_for_linux_path = (
        project_root / "data" / "requirements_for_posix.bin"
    )
    requirements_path.parent.mkdir(parents=True, exist_ok=True)

    result = subprocess.run(
        [str(python_path), "-m", "pip", "freeze"],
        cwd=str(project_root),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "pip freeze failed")

    requirements_path.write_text(result.stdout, encoding="utf-8")

    patterns = [
        re.compile(r"^pywin32", re.IGNORECASE),
        re.compile(r"^pyWinhook", re.IGNORECASE),
        re.compile(r"^win32_setctime", re.IGNORECASE),
    ]
    kept_lines: list[str] = []
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        if any(p.match(line) for p in patterns):
            continue
        kept_lines.append(line)
    requirements_for_linux_path.write_text(
        "\n".join(kept_lines) + ("\n" if kept_lines else ""),
        encoding="utf-8",
    )


def _regenerate_ui(project_root: Path, pyside_uic_path: Path) -> None:
    ui_root = project_root / "ui" / "ui_resource"
    for ui_file in ui_root.rglob("*.ui"):
        ui_code_path = Path(str(ui_file).replace(".", "_") + ".py")
        ui_code_path.parent.mkdir(parents=True, exist_ok=True)
        _run(
            [str(pyside_uic_path), str(ui_file), "-o", str(ui_code_path)],
            project_root,
        )


def _compile_with_nuitka(project_root: Path, python_path: Path) -> None:
    _run(
        [
            str(python_path),
            "-m",
            "nuitka",
            "--mode=standalone",
            "--python-flag=-u",
            "--python-flag=-O",
            "--enable-plugin=pyside6",
            "--output-dir=build",
            "--windows-console-mode=disable",
            "--product-name=usb kvm client",
            "--windows-file-description=a open source usb kvm client",
            "--windows-product-version=1.0.0.0",
            "--windows-icon-from-ico=./icons/main.ico",
            "--include-package=comtypes",
            "--include-package=pygrabber",
            "./usb_kvm_client.py",
            "--include-data-dir=./icons=icons",
            "--include-data-files=./data/requirements.bin=data/requirements.bin",
            "--include-data-files=./data/requirements_for_posix.bin=data/requirements_for_posix.bin",
            "--include-data-files=./data/requirements_runtime_windows.bin=data/requirements_runtime_windows.bin",
            "--include-data-dir=./translate=translate",
            "--include-qt-plugins=multimedia",
            "--quiet",
        ],
        project_root,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--venv",
        default=".venv",
        help="virtual environment directory, default: .venv",
    )
    parser.add_argument(
        "--no-install-tools",
        action="store_true",
        default=False,
        help="do not auto-install missing build tools into venv",
    )
    parser.add_argument(
        "--skip-requirements", action="store_true", default=False
    )
    parser.add_argument("--skip-ui", action="store_true", default=False)
    parser.add_argument("--skip-format", action="store_true", default=False)
    parser.add_argument("--skip-lint", action="store_true", default=False)
    parser.add_argument("--skip-build", action="store_true", default=False)
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parents[1]
    python_path = _venv_python(project_root, args.venv)
    _ensure_tools(python_path, project_root, not args.no_install_tools)

    if not args.skip_requirements:
        _create_requirements(project_root, python_path)

    if not args.skip_ui:
        pyside_uic = _venv_tool(
            project_root,
            args.venv,
            "pyside6-uic.exe" if os.name == "nt" else "pyside6-uic",
        )
        _regenerate_ui(project_root, pyside_uic)

    if not args.skip_format:
        _run(
            [
                str(python_path),
                "-m",
                "black",
                "--safe",
                "--target-version",
                "py312",
                "./",
            ],
            project_root,
        )

    if not args.skip_lint:
        _run(
            [str(python_path), "-m", "flake8", "--config=./flake8.cfg", "./"],
            project_root,
        )

    if not args.skip_build:
        _compile_with_nuitka(project_root, python_path)

        releases_dir = project_root / "releases"
        releases_dir.mkdir(parents=True, exist_ok=True)
        src_dist = project_root / "build" / "usb_kvm_client.dist"
        dst_dist = releases_dir / "usb_kvm_client.dist"
        if dst_dist.exists():
            shutil.rmtree(dst_dist)
        shutil.move(str(src_dist), str(dst_dist))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
