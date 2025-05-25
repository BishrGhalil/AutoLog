## 2.1.0 (2025-05-25)

### Feat

- add update checker

## 2.0.0 (2025-05-25)

### Feat

- **logging**: add console handler
- add support for different providers
- add commitizen integration

## v1.1.0 (2025-05-21)

### Feat

- updated show_error with logfile info
- improved datetime parsing
- improved logging path

### Fix

- match date not only time to detect duplicates
- only create tag if not exists

## v1.0.1 (2025-05-19)

### Feat

- added icon, build workflow

### Fix

- deprecated set-output in actions
- replaced workflow signing logic
- fixed missing run command in workfow
- add find-singtool to path in workflow
- install uv in workflow
- removed version param from workflow dispatch
- build workflow toml parsing

## v1.0.0 (2025-05-11)

### Feat

- add ui screenshot
- refactor, support for duplicates handling
- improved progressbar and status coloring and updating
- improved logging
- status bar text
- exception logging
- add cooldown
- performance improvment by not fetching the issue first
- tree view styling
- pyinstaller support for building executables

### Fix

- set a timeout for jira client
- not updating entries after first n
- align table text to center
- removed wrong datas from spec
- fixed typo in readm

### Refactor

- issue key parsing
- parse issue keys in main app
