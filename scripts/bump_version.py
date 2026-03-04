from __future__ import annotations

import re
import sys
from pathlib import Path

VERSION_RE = re.compile(r"^\d+\.\d+\.\d+$")


def _replace_version(path: Path, pattern: str, replacement: str) -> None:
    content = path.read_text(encoding="utf-8")
    updated, count = re.subn(pattern, replacement, content, flags=re.MULTILINE)
    if count != 1:
        raise RuntimeError(f"Falha ao atualizar versao em {path}.")
    path.write_text(updated, encoding="utf-8")


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("Uso: python scripts/bump_version.py <major.minor.patch>")

    version = sys.argv[1].strip()
    if not VERSION_RE.match(version):
        raise SystemExit("Versao invalida. Use o formato semantic versioning (ex.: 0.2.0).")

    root = Path(__file__).resolve().parent.parent
    pyproject = root / "pyproject.toml"
    init_file = root / "src" / "amazon_sales_analysis" / "__init__.py"

    _replace_version(pyproject, r'^version = ".*"$', f'version = "{version}"')
    _replace_version(init_file, r'^__version__ = ".*"$', f'__version__ = "{version}"')

    print(f"Versao atualizada para {version}")


if __name__ == "__main__":
    main()
