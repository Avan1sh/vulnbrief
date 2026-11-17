"""Check tracked publication files for private state and common credential patterns.

Uses Git's index so ignored local files remain private. This is a small hygiene
check, not an exhaustive secret scanner or a substitute for human review.
"""
from pathlib import Path, PurePosixPath
import re
import subprocess

BASE = Path(__file__).resolve().parents[1]
PRIVATE_PARTS = {'.venv', '.wheel-check', '.vulnbrief', '__pycache__',
                 '.pytest_cache', 'build', 'dist', 'runs', 'node_modules',
                 'test-results', 'playwright-report'}
TOKEN_PATTERNS = (
    re.compile(rb'gsk_[A-Za-z0-9]{20,}'),
    re.compile(rb'gh[pousr]_[A-Za-z0-9]{30,}'),
    re.compile(rb'github_pat_[A-Za-z0-9_]{40,}'),
    re.compile(rb'sk-(?:proj-)?[A-Za-z0-9_-]{32,}'),
    re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
)


def main():
    tracked = subprocess.check_output(['git', 'ls-files', '-z'], cwd=BASE)
    names = [name for name in tracked.decode('utf-8').split('\0') if name]
    problems = []
    for name in names:
        path = PurePosixPath(name)
        private = (any(part in PRIVATE_PARTS or part.endswith('.egg-info') for part in path.parts)
                   or (path.name.startswith('.env') and path.name != '.env.example')
                   or path.suffix in {'.sqlite3', '.db', '.pyc'}
                   or path.name.startswith('history.sqlite3'))
        if private:
            problems.append(f'Private/generated file is tracked: {name}')
        data = (BASE / name).read_bytes()
        if any(pattern.search(data) for pattern in TOKEN_PATTERNS):
            problems.append(f'Possible credential in tracked file: {name}')
    if not names:
        problems.append('No tracked files to audit')
    for problem in problems:
        print(problem)
    if problems:
        return 1
    print(f'Publication hygiene passed for {len(names)} tracked files. No matched credential values are printed.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
