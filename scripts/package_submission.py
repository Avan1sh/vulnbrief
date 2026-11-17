"""Package only reviewable source/docs/evidence; never include local configuration."""
from pathlib import Path
import zipfile

BASE = Path(__file__).resolve().parents[1]
ROOT_FILES = {"README.md", "pyproject.toml", "requirements-lock.txt", ".gitignore", ".gitattributes",
              ".env.example", "CHANGELOG.md", "CONTRIBUTING.md", "SECURITY.md"}
ALLOWED = {
    "src": {".py", ".html", ".css", ".js", ".mjs"}, "tests": {".py", ".txt"}, "examples": {".json", ".md", ".csv"},
    "docs": {".md", ".txt", ".mmd", ".png", ".pdf"},
    "artifacts": {".md", ".json", ".jsonl"}, "scripts": {".py"},
    ".github": {".md", ".yml"},
    "ui-tests": {".mjs", ".json", ".md"},
}


def package(destination: Path):
    destination.parent.mkdir(parents=True, exist_ok=True)
    paths = [BASE / name for name in sorted(ROOT_FILES)]
    for folder, suffixes in ALLOWED.items():
        paths.extend(p for p in (BASE / folder).rglob("*") if p.is_file()
                     and p.suffix in suffixes and not set(p.parts)&{'__pycache__','node_modules','test-results','playwright-report'})
    with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED) as archive:
        for p in paths:
            if p.exists():
                archive.write(p, "vulnbrief/" + p.relative_to(BASE).as_posix())
    with zipfile.ZipFile(destination) as archive:
        assert all(Path(n).name != ".env" for n in archive.namelist())
        assert archive.testzip() is None
    if destination.stat().st_size > 10_000_000:
        raise ValueError("Submission ZIP exceeds 10 MB")
    print(f"Packaged {len(paths)} files: {destination} ({destination.stat().st_size:,} bytes)")


if __name__ == "__main__":
    package(BASE.parent / "output" / "vulnbrief-v03-submission.zip")
