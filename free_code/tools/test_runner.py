"""Test runner auto-detection and execution."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Optional, Tuple


def detect_test_framework(project_root: Optional[str] = None) -> Optional[str]:
    """Auto-detect the test framework for the current project.

    Returns one of: pytest, jest, go, cargo, unittest, or None.
    """
    root = Path(project_root) if project_root else Path.cwd()

    # Python: pytest
    if (root / "pytest.ini").exists() or (root / "pyproject.toml").exists():
        # Check if pytest is mentioned in pyproject.toml
        pyproject = root / "pyproject.toml"
        if pyproject.exists():
            text = pyproject.read_text(errors="replace")
            if "pytest" in text:
                return "pytest"
    if (root / "setup.cfg").exists():
        text = (root / "setup.cfg").read_text(errors="replace")
        if "pytest" in text:
            return "pytest"
    # Check for test files
    for pattern in ["test_*.py", "tests/"]:
        if list(root.glob(pattern)):
            return "pytest"

    # JavaScript: jest
    if (root / "jest.config.js").exists() or (root / "jest.config.ts").exists():
        return "jest"
    pkg_json = root / "package.json"
    if pkg_json.exists():
        text = pkg_json.read_text(errors="replace")
        if "jest" in text:
            return "jest"
        if '"test"' in text:
            return "npm_test"

    # Go
    if list(root.glob("*_test.go")) or list(root.glob("**/*_test.go")):
        return "go"
    if (root / "go.mod").exists():
        return "go"

    # Rust
    if (root / "Cargo.toml").exists():
        return "cargo"

    return None


def get_test_command(
    framework: Optional[str] = None,
    path: Optional[str] = None,
    project_root: Optional[str] = None,
) -> Tuple[str, str]:
    """Get the test command for a framework.

    Returns (command, description).
    """
    if framework is None:
        framework = detect_test_framework(project_root) or "pytest"

    target = path or ""

    commands = {
        "pytest": (f"python -m pytest {target} -v".strip(), "pytest"),
        "jest": (f"npx jest {target} --verbose".strip(), "jest"),
        "go": (f"go test {target or './...'} -v".strip(), "go test"),
        "cargo": (f"cargo test {target}".strip(), "cargo test"),
        "npm_test": ("npm test", "npm test"),
        "unittest": (f"python -m unittest {target or 'discover'} -v".strip(), "unittest"),
    }

    cmd, desc = commands.get(framework, (f"python -m pytest {target} -v".strip(), "pytest"))
    return cmd, desc


def run_tests(
    path: Optional[str] = None,
    framework: Optional[str] = None,
    _project_root: Optional[str] = None,
) -> str:
    """Run tests and return the output.

    Args:
        path: Specific test file or directory.
        framework: Override test framework detection.
    """
    if framework is None:
        framework = detect_test_framework(_project_root)
        if framework is None:
            return "Error: Could not detect test framework. Specify --framework."

    cmd, desc = get_test_command(framework, path, _project_root)

    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=300,
            cwd=_project_root,
        )
        output_parts = []
        if result.stdout:
            output_parts.append(result.stdout)
        if result.stderr:
            output_parts.append(result.stderr)
        output = "\n".join(output_parts)

        if result.returncode == 0:
            output = f"[{desc}] PASSED\n\n{output}"
        else:
            output = f"[{desc}] FAILED (exit code {result.returncode})\n\n{output}"

        # Truncate
        if len(output) > 50000:
            output = output[:25000] + "\n\n... (truncated) ...\n\n" + output[-25000:]
        return output
    except subprocess.TimeoutExpired:
        return f"Error: Tests timed out after 300s"
    except OSError as e:
        return f"Error running tests: {e}"
