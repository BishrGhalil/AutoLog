"""GUI logic"""

import logging
import threading
import tkinter as tk
import webbrowser
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import List, Optional

import customtkinter as ctk
from jira.exceptions import JIRAError

from autolog.__version__ import version
from autolog.constants import (
    APP_HEIGHT,
    APP_MIN_HEIGHT,
    APP_MIN_WIDTH,
    APP_WIDTH,
    STATUS_DISPLAY,
    TABLE_COLUMN_WIDTHS,
    ColumnID,
)
from autolog.keyring_manager import CredentialManager
from autolog.logging_config import LOGGING_FILE
from autolog.models import ProcessingResult, WorklogEntry
from autolog.parsers.file_parsers import get_supported_formats
from autolog.update_helpers import get_latest_release_info, is_update_available
from autolog.widgets import (
    CellTooltip,
    CredentialsFrame,
    FileSelectorFrame,
    OptionsFrame,
)
from autolog.worklog_processor import WorklogProcessor

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

logger = logging.getLogger(__name__)


class WorklogApp(ctk.CTk):
    """Main application window for the Jira AutoLog tool."""

    def __init__(self):
        super().__init__()
        self.title("Jira AutoLog")
        self.minsize(width=APP_MIN_WIDTH, height=APP_MIN_HEIGHT)
        self.geometry(f"{APP_WIDTH}x{APP_HEIGHT}")
        self.entries: List[WorklogEntry] = []
        self.editing_entry: Optional[ctk.CTkEntry] = None
        self.processor: Optional[WorklogProcessor] = None
        self._create_widgets()
        self._load_credentials()
        self._setup_treeview()

        self.after(100, self._check_for_updates)

    def _create_widgets(self) -> None:
        """Initialize and arrange all UI components."""
        self.credentials_frame = CredentialsFrame(self)
        self.credentials_frame.pack(pady=10, padx=10, fill="x")

        self.options_frame = OptionsFrame(self)
        self.options_frame.pack(pady=5, padx=10, fill="x")

        self.file_frame = FileSelectorFrame(self, self._browse_file)
        self.file_frame.pack(pady=10, padx=10, fill="x")

        self._create_results_table()
        self._create_progress_controls()

    def _create_results_table(self) -> None:
        """Configure the treeview for displaying worklog results."""
        treestyle = ttk.Style()
        treestyle.theme_use("default")
        frame_bg_color = self._apply_appearance_mode(
            ctk.ThemeManager.theme["CTkFrame"]["fg_color"]
        )
        input_bg_color = self._apply_appearance_mode(
            ctk.ThemeManager.theme["CTkEntry"]["fg_color"]
        )
        text_color = self._apply_appearance_mode(
            ctk.ThemeManager.theme["CTkLabel"]["text_color"]
        )
        selected_color = self._apply_appearance_mode(
            ctk.ThemeManager.theme["CTkFrame"]["fg_color"]
        )

        treestyle.configure(
            "Treeview",
            background=frame_bg_color,
            foreground=text_color,
            fieldbackground=frame_bg_color,
            borderwidth=0,
        )
        treestyle.configure(
            "Treeview.Heading",
            background=input_bg_color,
            foreground=text_color,
            padding=(16, 8),
            borderwidth=0,
        )
        treestyle.map(
            "Treeview",
            foreground=[("selected", frame_bg_color)],
            background=[("selected", selected_color)],
        )
        treestyle.map("Treeview.Heading", background=[("active", selected_color)])

        columns = ("Started", "Duration", "Issue", "Status", "Error")
        self.tree = ttk.Treeview(self, columns=columns, show="headings")
        for col in columns:
            self.tree.heading(col, text=col, anchor="center")
            self.tree.column(col, width=TABLE_COLUMN_WIDTHS[col], anchor="center")
        self.tree.pack(pady=10, padx=10, fill="both", expand=True)
        self.tooltip = CellTooltip(self.tree)

    def _create_progress_controls(self) -> None:
        """Set up the progress bar and process button."""
        progress_frame = ctk.CTkFrame(self)
        progress_frame.pack(pady=5, padx=10, fill="x")
        self.status_label = ctk.CTkLabel(
            progress_frame, text="Ready", anchor="center", font=("Arial", 14)
        )
        self.status_label.pack(fill="x", expand=True)
        self.progress = ctk.CTkProgressBar(progress_frame, height=10)
        self.progress.set(0)
        self.progress.pack(pady=5, padx=10, fill="x")
        self.progress_color = self._apply_appearance_mode(
            ctk.ThemeManager.theme["CTkProgressBar"]["progress_color"]
        )
        self.process_btn = ctk.CTkButton(
            self, text="Process", command=self._start_processing, state="disabled"
        )
        self.process_btn.pack(pady=10)

    def _setup_treeview(self) -> None:
        """Bind events to the treeview."""
        self.tree.bind("<Double-1>", self._on_cell_double_click)

    def _on_cell_double_click(self, event: tk.Event) -> None:
        """Handle double-click events for editing cells."""
        if self.tree.identify("region", event.x, event.y) != "cell":
            return
        col = self.tree.identify_column(event.x)
        row_id = self.tree.identify_row(event.y)
        if col == ColumnID.ISSUE.value:
            self._handle_issue_cell_edit(row_id, col)

    def _handle_issue_cell_edit(self, row_id: str, column: str) -> None:
        """Enable editing of an issue key cell."""
        if self.tree.set(row_id, "Status") == STATUS_DISPLAY["success"]:
            return
        current_value = self.tree.set(row_id, "Issue")
        index = self.tree.index(row_id)
        entry = self.entries[index]
        x, y, width, height = self.tree.bbox(row_id, column)
        self.editing_entry = ctk.CTkEntry(self.tree, width=width, height=height)
        self.editing_entry.insert(0, current_value)
        self.editing_entry.place(x=x, y=y)
        self.editing_entry.bind("<Return>", lambda e: self._save_edit(row_id, entry))
        self.editing_entry.bind("<FocusOut>", lambda e: self._cancel_edit())
        self.editing_entry.focus_set()

    def _save_edit(self, row_id: str, entry: WorklogEntry) -> None:
        """Save the edited issue key."""
        new_value = self.editing_entry.get()
        self.tree.set(row_id, column="Issue", value=new_value)
        entry.issue_key = new_value.strip()
        entry.status = "pending"
        self.tree.set(row_id, column="Status", value=STATUS_DISPLAY["pending"])
        self.tree.set(row_id, column="Error", value="")
        self._cancel_edit()

    def _cancel_edit(self) -> None:
        """Cancel the current edit operation."""
        if self.editing_entry:
            self.editing_entry.destroy()
            self.editing_entry = None

    def _load_credentials(self) -> None:
        """Populate credential fields with saved values."""
        base_url, email, api_key = CredentialManager.get_credentials()
        if any([base_url, email, api_key]):
            self.credentials_frame.load_credentials(base_url, email, api_key)

    def _browse_file(self) -> None:
        """Open a file dialog and load the selected CSV."""
        filetypes = [["Source File", get_supported_formats()]]
        file_path = filedialog.askopenfilename(filetypes=filetypes)
        if file_path:
            self.file_frame.set_file_path(file_path)
            self._load_entries(Path(file_path))

    def _load_entries(self, file_path: Path) -> None:
        """Initialize processor and load entries from CSV."""
        self.processor = WorklogProcessor(
            self.credentials_frame.credentials,
            self.options_frame.selected_timezone,
        )
        try:
            provider_name = self.file_frame.provider_name
            self.entries, total_hours = self.processor.load_entries(
                file_path, provider_name
            )
        except Exception as e:
            err_str = str(e)
            self._update_status("Failed Loading Entries")
            self._show_error("Error", f"Failed Loading Entries\n{err_str}")
        else:
            if self.entries:
                self._update_status(f"Total: {total_hours}")
                self._update_table()
                self.process_btn.configure(state="normal")
            else:
                self._update_table()
                self._update_status("Couldn't parse any entry")

    def _update_table(self) -> None:
        """Refresh the treeview with current entries."""
        self.tree.delete(*self.tree.get_children())
        for entry in self.entries:
            duration_str = f"{entry.duration // 3600}h {(entry.duration % 3600) // 60}m"
            self.tree.insert(
                "",
                "end",
                values=(
                    entry.started.strftime("%Y-%m-%d %H:%M"),
                    duration_str,
                    entry.issue_key or "⚠️ Missing",
                    STATUS_DISPLAY.get(entry.status, STATUS_DISPLAY["pending"]),
                    "",
                ),
            )

    def _start_processing(self) -> None:
        """Validate credentials and start processing in a background thread."""
        if not all(self.credentials_frame.credentials):
            self._show_error("Error", "Please fill all credentials fields")
            return
        CredentialManager.save_credentials(*self.credentials_frame.credentials)
        self.process_btn.configure(state="disabled")
        self._update_progress(0, self.progress_color)
        self._update_status("Connecting to Jira...")
        self._processing_thread = threading.Thread(
            target=self._process_entries, daemon=True
        )
        self._processing_thread.start()

    def _process_entries(self) -> None:
        """Execute processing and handle results."""
        try:

            def callback(
                idx: int, total: int, entry: WorklogEntry, result: ProcessingResult
            ) -> None:
                self._update_row_status(entry._idx, entry, result)
                self._update_progress((idx + 1) / total)
                self._update_status(f"{idx + 1}/{total}")

            self.processor.process_entries(
                self.entries, callback, self.options_frame.prevent_duplicates_var.get()
            )
            self._update_progress(color="green")
            self._update_status("Finished")
            self._show_results()

        except JIRAError as e:
            self._show_error("Error", f"Jira error: {e.text}")
            self._update_progress(color="red")
        except Exception as e:
            self._show_error("Error", f"Unexpected error: {e}")
            self._update_progress(color="red")
        finally:
            self.process_btn.configure(state="normal")
            self._update_progress(0, self.progress_color)
            self._update_status("")

    def _update_row_status(
        self, idx: int, entry: WorklogEntry, result: ProcessingResult
    ) -> None:
        """Update a treeview row with processing results."""
        row = self.tree.get_children()[idx]
        self.tree.set(row, "Status", STATUS_DISPLAY[entry.status])
        self.tree.set(
            row, "Error", "" if result.success else self._format_error(result.error)
        )

    def _format_error(self, error: Exception) -> str:
        """Format an error message for display."""
        return str(error.text) if isinstance(error, JIRAError) else str(error)

    def _update_progress(self, value: float = None, color: str = None) -> None:
        """Update the progress bar."""
        if value is not None:
            self.progress.set(value)
        if color is not None:
            self.progress.configure(progress_color=color)

    def _update_status(self, message: str) -> None:
        """Update the status label."""
        self.status_label.configure(text=message)

    def _show_results(self) -> None:
        """Display a summary of processing results."""
        total = self.processor.total
        failed_count = len(self.processor.failed_entries)
        success_count = total - failed_count
        message = (
            f"Posted {success_count}/{total} worklogs\n"
            f"{failed_count} failed - double-click to edit keys"
            if self.processor.failed_entries
            else f"Successfully posted {success_count}/{total} worklogs"
        )
        messagebox.showinfo("Processing Complete", message)

    def _show_error(self, title, message, **options):
        detail = options.pop("detail", None)
        logfile_msg = f"Log file:\n{LOGGING_FILE}"

        if not detail:
            detail = logfile_msg
        else:
            detail += f"\n{logfile_msg}"

        messagebox.showerror(title, message, detail=detail, **options)

    def _check_for_updates(self) -> None:
        """
        In a background thread, fetch the latest release.
        If newer than version, prompt the user with Update / Ignore.
        """

        def _worker():
            try:
                info = get_latest_release_info("Bishrghalil/Autolog")
                if is_update_available(version, info["version"]):
                    # run prompt on the main thread
                    def _prompt():
                        msg = (
                            f"A new version {info['version']} is available.\n\n"
                            "Release notes:\n"
                            f"{info['changelog']}\n\n"
                            "View release page?"
                        )
                        if messagebox.askyesno(
                            "Update Available", msg, icon=messagebox.INFO
                        ):
                            webbrowser.open(info["url"])

                    self.after(0, _prompt)
            except Exception as e:
                logger.exception("Update check failed: %s", e)

        threading.Thread(target=_worker, daemon=True).start()
