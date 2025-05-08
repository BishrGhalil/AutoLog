# AutoLog

**AutoLog** is a tool that automates the process of logging work entries into Jira from various data sources. Currently, the only supported data source is **CSV**, with support for additional sources planned for future releases.

## Prerequisites

- Python 3.10+
- Jira account with appropriate API access
- CSV file formatted according to the expected schema ([see below](#csv-format))

---

## Installation & Setup

Clone the repository:

```bash
git clone https://github.com/BishrGhalil/AutoLog.git
cd AutoLog
```

Set up your Python environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
```

---

## CSV Format

The input CSV should include the following columns (Kimai format), Order doesn't matter:

| Field                  | Description                                                        |
| ---------------------- | ------------------------------------------------------------------ |
| Date                   | Start time (e.g., 2025-05-07T10:00:00)                             |
| Duration               | Time spent (e.g., 2h, 30m)                                         |
| Activity               | Contains Jira issue key (e.g., [PROJ-123] blah or [PROJ] 123 blah) |
| Description (optional) | Work log comment                                                   |

---

## Running the Tool

```bash
python main.py
```

---

## Development

Standard development steps:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
python main.py
```

Run linters/tests:

```bash
flake8 .
```

---

## Roadmap

- [ ] Docker support
- [ ] Support for Excel data sources
- [ ] Docker support

---

## Contributing

Contributions are welcome. Please fork the repo and create a pull request. Ensure your code is formatted with `black`, `isort`.

---

## License

MIT License. See `LICENSE` file for details.
