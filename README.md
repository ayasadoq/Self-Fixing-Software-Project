# Self-Fixing Software Project

An autonomous, agent-based Python workflow that scans a target codebase for static-analysis issues, applies automated fixes, creates a Git branch and pull request, and updates project documentation.

The project is built with Google's ADK and Gemini APIs, Pylint, Flake8, Black, isort, Pytest, and GitHub integration.

## Features

- Scans the `target_codebase` directory with Pylint and Flake8.
- Applies formatting, import sorting, indentation, whitespace, and docstring fixes.
- Creates an isolated fix branch and commits changes automatically.
- Pushes the branch and optionally creates a GitHub pull request.
- Validates test files and supports AI-generated test coverage suggestions.
- Updates changelogs, API documentation, architecture documentation, and release notes.
- Runs tests across Python 3.8, 3.9, and 3.10 through GitHub Actions.

## Project Structure

```text
.
├── .github/workflows/test.yml       # CI test and coverage workflow
├── auto_pr_creator_agent/           # Applies fixes and creates pull requests
├── bug_hunter_agent/                # Runs Pylint and Flake8 scans
├── docs_updater_agent/              # Generates and updates documentation
├── orchestrator_agent/              # Coordinates the self-fixing workflow
├── target_codebase/                 # Example code inspected by the agents
├── test_validator_agent/            # Analyzes and enhances test coverage
├── requirements.txt                 # Python dependencies
└── README.md
```

## How It Works

1. The orchestrator starts a Bug Hunter scan.
2. Pylint and Flake8 report issues in `target_codebase`.
3. The Auto-PR Creator applies supported fixes and creates a commit on a new branch.
4. The fix branch is pushed to the configured Git remote.
5. A GitHub pull request is created when GitHub API credentials are available.
6. The Docs Updater refreshes repository documentation from recent commit history.

## Requirements

- Python 3.8 or newer
- Git
- A GitHub account with push access to the repository
- A Google Gemini API key for AI-assisted features
- A GitHub token for pull request creation

## Installation

Clone the repository and create a virtual environment:

```bash
git clone https://github.com/ayasadoq/Self-Fixing-Software-Project.git
cd Self-Fixing-Software-Project
python -m venv .venv
```

Activate the environment:

**Windows PowerShell**

```powershell
.venv\Scripts\Activate.ps1
```

**macOS or Linux**

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Configuration

Set the required credentials in your environment before running AI or GitHub features.

**Windows PowerShell**

```powershell
$env:GOOGLE_API_KEY="your-google-api-key"
$env:GITHUB_TOKEN="your-github-token"
```

**macOS or Linux**

```bash
export GOOGLE_API_KEY="your-google-api-key"
export GITHUB_TOKEN="your-github-token"
```

The GitHub integration requires repository push access and, depending on local Git configuration, either HTTPS credentials or an SSH key.

Do not commit API keys or access tokens to this repository.

## Running the Agents

Launch the Google ADK development UI from the repository root:

```bash
adk web
```

Open the ADK interface and select `Self_Fixing_Project_Orchestrator` to begin a workflow.

You can also invoke the individual tools from Python:

```python
from bug_hunter_agent.agent import bug_hunter_scan_code

report = bug_hunter_scan_code()
print(report)
```

## Testing

Run the test suite and coverage report:

```bash
pytest --cov=. --cov-report=term-missing
python -m coverage report --fail-under=80
```

Run the static-analysis scan directly:

```bash
pylint -r n --output-format=json target_codebase
flake8 target_codebase
```

The GitHub Actions workflow runs tests and coverage validation for pull requests and pushes to `main`.

## Adding a Fix

1. Put or update code in `target_codebase`.
2. Run the Bug Hunter scan.
3. Review the reported Pylint and Flake8 issues.
4. Run the Auto-PR Creator through the orchestrator.
5. Inspect the generated branch and pull request before merging.

## Security and Usage Notes

- Automated fixes can modify source files and create branches or commits.
- Test AI-generated changes and pull requests before merging.
- Keep credentials outside the repository and rotate tokens if they are exposed.
- The CI workflow requires a valid Codecov upload configuration to complete successfully.

## Contributing

1. Create a feature branch.
2. Make focused changes and add tests where appropriate.
3. Run the test and static-analysis commands locally.
4. Open a pull request with a clear description of the behavior or fix.

