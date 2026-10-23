# Contributing

Thank you for taking the time to contribute to this project. Below are the guidelines for keeping contributions consistent and the codebase healthy.

---

## Getting started

1. **Fork** the repository on GitHub.
2. **Clone** your fork:
   ```bash
   git clone https://github.com/<your-username>/weather-forecast-peshawar.git
   ```
3. Set up the development environment following the [README quick start](../README.md#quick-start).
4. Create a **feature branch** from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```

---

## Making changes

- Keep changes focused. One pull request = one logical change.
- Match the existing code style — Python follows PEP 8, JavaScript uses React functional components with hooks.
- Add or update tests for every functional change (see [Testing](#testing) below).
- Do not introduce new dependencies without discussion in an issue first.

---

## Testing

All tests must pass before opening a PR.

```bash
cd tests
pip install -r requirements-test.txt
pytest
```

Expected: **30 passed, 0 failed.**

The test suite covers:
- All public and admin API endpoints
- Admin token auth and disabled-admin mode
- Model input/output shape contract
- Prediction determinism and physical output bounds

---

## Commit messages

Use a short present-tense subject line:

```
Add Magnus formula dew-point calculation
Fix forecast window advancing logic
Update requirements to pinned versions
```

Avoid vague messages like `fix stuff` or `update`.

---

## Pull request checklist

Before submitting:

- [ ] `python -m pytest -q tests` passes
- [ ] No hardcoded secrets, API keys, or tokens
- [ ] Model artifacts are not accidentally committed (`.gitignore` covers `*.keras`, `*.pkl`, `*.npy`)
- [ ] Environment variables documented in `.env.example` if new ones are added
- [ ] README or relevant doc updated if behaviour changes

---

## Reporting bugs

Open a GitHub Issue and include:

1. What you expected to happen
2. What actually happened
3. Steps to reproduce
4. Python/Node version and OS
5. Relevant lines from `predictions.log` if it is a backend issue

---

## Suggesting features

Open a GitHub Issue tagged `enhancement`. Describe the problem you are trying to solve, not just the solution — this helps discussion converge on the right approach.

---

## Code of conduct

Be respectful. This is a research project from UET Peshawar — all contributors and reviewers are expected to engage constructively and professionally.
