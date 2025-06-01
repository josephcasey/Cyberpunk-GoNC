"Claude Context Inject": {
  "prefix": "claudecontext",
  "body": [
    "### Claude Context: Jo's Dev Environment ###",
    "OS: macOS Big Sur",
    "Python: Always use Python 3 (`python3`, `pip3`)",
    "Install with `pip3 install --user ...`",
    "Use UTF-8 encoding and readable print/logging",
    "Prefer pytest, flake8 or ruff",
    "VSCode terminal usage assumed",
    "Assume & maintain virtualenvs for needed packages",
    "keep all test code in separate copilot-test directory",
    "do not create new files that supercede existing ones",
    "do not handle any git operations",
    "ensure you delete any temporary files created & any test files",
    "avoid sleeping in terminal",
  ],
  "description": "Inject my Claude prompt context"
}
