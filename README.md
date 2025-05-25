<div align="center">
  <a href="https://github.com/BishrGhalil/AutoLog">
    <img alt="AutoLog.Logo" width="200" height="200" src="./assets/icon.png">
  </a>
  <h1>AutoLog</h1>
  <p>
    automates the process of logging work entries into Jira.
  </p>
  <a href="https://github.com/BishrGhalil/AutoLog/releases/latest">
    <img src="https://img.shields.io/github/v/release/BishrGhalil/AutoLog">
  </a>
  <a href="https://github.com/BishrGhalil/AutoLog/releases/latest">
    <img src="https://img.shields.io/github/release-date/BishrGhalil/AutoLog">
  </a>
  <a href="https://github.com/BishrGhalil/AutoLog/tree/dev">
    <img src="https://img.shields.io/github/last-commit/BishrGhalil/AutoLog">
  </a>
  <a href="https://github.com/BishrGhalil/AutoLog/releases/">
    <img src="https://img.shields.io/github/downloads/BishrGhalil/AutoLog/total">
  <a href="https://github.com/BishrGhalil/AutoLog/blob/dev/LICENSE">
    <img src="https://img.shields.io/github/license/BishrGhalil/AutoLog">
  </a>
</div>


## About
**AutoLog** is a tool that automates the process of logging work entries into Jira from various data sources. Currently, Both **Odoo**, and **Kimai** providers are implemented with support for both **CSV** and **Excel** file types.

<img src=".github/ui.png" alt="UI" width="70%"/>

## Prerequisites
- Jira account with appropriate [API access](https://support.atlassian.com/atlassian-account/docs/manage-api-tokens-for-your-atlassian-account/#Create-an-API-token).
- Worklog file exported from the supported providers.

---

# Usage:

## Download
You may download the executable from the [releases page](https://github.com/BishrGhalil/AutoLog/releases)

## Run from source code
Clone the repository:

```bash
git clone https://github.com/BishrGhalil/AutoLog.git
cd AutoLog
```

Set up your Python environment:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python main.py
```

---

## Development

```bash
python3 -m pip install uv
uv sync
pre-commit install
uv run main.py
```

Use [commitizen](https://commitizen-tools.github.io/commitizen/):

for committing
```bash
cz c
```

for bumping:
```bash
cz bump
```

Run linters:

```bash
ruff check .
```

Build executable:

```bash
pyinstaller --noconfirm --clean autolog.spec
```

[Signing the executable](https://gist.github.com/PaulCreusy/7fade8d5a8026f2228a97d31343b335e)

---

## Roadmap

- [X] Cooldown
- [X] Windows Executable
- [X] Code signing for Windows
- [ ] Async requests

---

## Contributing

Contributions are welcome. Please fork the repo and create a pull request.

---

## License

MIT License. See `LICENSE` file for details.
