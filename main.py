from autolog import logging_config
from autolog.app import WorklogApp

if __name__ == "__main__":
    logging_config.setup_logging()

    app = WorklogApp()
    app.mainloop()
