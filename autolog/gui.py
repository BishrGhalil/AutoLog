"""GUI logic"""

import logging
import threading
import time
import tkinter as tk
from enum import Enum
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Callable, List, Optional, Tuple

import customtkinter as ctk
from jira.exceptions import JIRAError

from autolog.adapters import CSVAdapter
from autolog.issue_parser import IssueKeyParser
from autolog.jira_client import JiraClient
from autolog.keyring_manager import CredentialManager
from autolog.models import ProcessingResult, WorklogEntry

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

COOLDOWN_SEC = 2
COOLDOWN_EVERY = 10
logger = logging.getLogger(__file__)


# Constants
class ColumnID(Enum):
    STARTED = "#1"
    DURATION = "#2"
    ISSUE = "#3"
    STATUS = "#4"
    ERROR = "#5"


STATUS_DISPLAY = {
    "pending": "🔄 Pending",
    "success": "✅ Success",
    "failed": "❌ Failed",
}


class CellTooltip:
    """Displays tooltips for treeview cells with error messages."""

    def __init__(self, widget: ttk.Treeview):
        self.widget = widget
        self.tipwindow = None
        self.text = ""
        widget.bind("<Motion>", self._on_motion)
        widget.bind("<Leave>", self._hide)

    def _on_motion(self, event: tk.Event) -> None:
        col = self.widget.identify_column(event.x)
        row = self.widget.identify_row(event.y)
        if col == ColumnID.ERROR.value and row:
            text = self.widget.set(row, "Error")
            if text and text != self.text:
                self.text = text
                self._show(event.x_root + 20, event.y_root + 10, text)
        else:
            self._hide()

    def _show(self, x: int, y: int, text: str) -> None:
        self._hide()
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(
            tw,
            text=text,
            justify="left",
            relief="solid",
            borderwidth=1,
            background="#ffffe0",
            font=("tahoma", "8", "normal"),
        )
        label.pack(ipadx=1)

    def _hide(self, *args) -> None:
        if self.tipwindow:
            self.tipwindow.destroy()
            self.tipwindow = None
            self.text = ""


class CredentialsFrame(ctk.CTkFrame):
    """Frame containing credential input fields."""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.base_url_entry = ctk.CTkEntry(self, placeholder_text="Jira Base URL")
        self.email_entry = ctk.CTkEntry(self, placeholder_text="Email")
        self.api_key_entry = ctk.CTkEntry(self, placeholder_text="API Key", show="*")
        self._layout()

    def _layout(self) -> None:
        self.base_url_entry.pack(side="left", padx=5, fill="x", expand=True)
        self.email_entry.pack(side="left", padx=5, fill="x", expand=True)
        self.api_key_entry.pack(side="left", padx=5, fill="x", expand=True)

    @property
    def credentials(self) -> Tuple[str, str, str]:
        return (
            self.base_url_entry.get().strip(),
            self.email_entry.get().strip(),
            self.api_key_entry.get().strip(),
        )

    def load_credentials(self, base_url: str, email: str, api_key: str) -> None:
        self.base_url_entry.insert(0, base_url)
        self.email_entry.insert(0, email)
        self.api_key_entry.insert(0, api_key)


class FileSelectorFrame(ctk.CTkFrame):
    """Frame for file selection components."""

    def __init__(self, master, browse_callback: Callable, **kwargs):
        super().__init__(master, **kwargs)
        self.file_entry = ctk.CTkEntry(self)
        self.browse_btn = ctk.CTkButton(self, text="Browse", command=browse_callback)
        self._layout()

    def _layout(self) -> None:
        self.file_entry.pack(side="left", padx=5, fill="x", expand=True)
        self.browse_btn.pack(side="left", padx=5)

    @property
    def file_path(self) -> Path:
        return Path(self.file_entry.get())

    def set_file_path(self, path: str) -> None:
        self.file_entry.delete(0, tk.END)
        self.file_entry.insert(0, path)


class WorklogApp(ctk.CTk):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self.title("Jira AutoLog")
        self.geometry("1200x700")

        self.entries: List[WorklogEntry] = []
        self.results: List[ProcessingResult] = []
        self.failed_entries: List[ProcessingResult] = []
        self.editing_entry: Optional[ctk.CTkEntry] = None

        self._create_widgets()
        self._load_credentials()
        self._setup_treeview()

    def _create_widgets(self) -> None:
        """Create and arrange all UI components."""
        self.credentials_frame = CredentialsFrame(self)
        self.credentials_frame.pack(pady=10, padx=10, fill="x")

        self.file_frame = FileSelectorFrame(self, self._browse_file)
        self.file_frame.pack(pady=10, padx=10, fill="x")

        self._create_results_table()
        self._create_progress_controls()

    def _create_results_table(self) -> None:
        """Create and configure the results treeview."""

        input_bg_color = self._apply_appearance_mode(
            ctk.ThemeManager.theme["CTkEntry"]["fg_color"]
        )
        frame_bg_color = self._apply_appearance_mode(
            ctk.ThemeManager.theme["CTkFrame"]["fg_color"]
        )
        text_color = self._apply_appearance_mode(
            ctk.ThemeManager.theme["CTkLabel"]["text_color"]
        )
        selected_color = self._apply_appearance_mode(
            ctk.ThemeManager.theme["CTkFrame"]["fg_color"]
        )

        treestyle = ttk.Style()
        treestyle.theme_use("default")

        # Configure main Treeview style
        treestyle.configure(
            "Treeview",
            background=frame_bg_color,
            foreground=text_color,
            fieldbackground=frame_bg_color,
            borderwidth=0,
        )

        # Configure Treeview heading style
        treestyle.configure(
            "Treeview.Heading",
            background=input_bg_color,
            foreground=text_color,
            padding=(16, 8),
            borderwidth=0,
        )

        # Configure style maps
        treestyle.map(
            "Treeview",
            forground=[("selected", frame_bg_color)],
            background=[("selected", selected_color)],
        )

        treestyle.map(
            "Treeview.Heading",
            background=[("active", selected_color)],
        )

        columns = ("Started", "Duration", "Issue", "Status", "Error")
        self.tree = ttk.Treeview(self, columns=columns, show="headings")

        col_widths = {
            "Started": 160,
            "Duration": 100,
            "Issue": 150,
            "Status": 80,
            "Error": 400,
        }

        for col in columns:
            self.tree.heading(col, text=col, anchor="center")
            self.tree.column(col, width=col_widths[col], anchor="center")

        self.tree.pack(pady=10, padx=10, fill="both", expand=True)
        self.tooltip = CellTooltip(self.tree)

    def _create_progress_controls(self) -> None:
        """Create progress bar and process button."""

        # Frame to hold progress components
        progress_frame = ctk.CTkFrame(self)
        progress_frame.pack(pady=5, padx=10, fill="x")

        # Status label
        self.status_label = ctk.CTkLabel(
            progress_frame, text="Ready", anchor="center", font=("Arial", 14)
        )
        self.status_label.pack(fill="x", expand=True)

        # ProgressBar
        self.progress = ctk.CTkProgressBar(progress_frame, height=10)
        self.progress.set(0)
        self.progress.pack(pady=5, padx=10, fill="x")

        self.process_btn = ctk.CTkButton(
            self, text="Process", command=self._start_processing
        )
        self.process_btn.configure(state="disabled")
        self.process_btn.pack(pady=10)

    def _setup_treeview(self) -> None:
        """Configure treeview event bindings."""
        self.tree.bind("<Double-1>", self._on_cell_double_click)

    def _on_cell_double_click(self, event: tk.Event) -> None:
        """Handle double-click events for cell editing."""
        if self.tree.identify("region", event.x, event.y) != "cell":
            return

        col = self.tree.identify_column(event.x)
        row_id = self.tree.identify_row(event.y)

        if col == ColumnID.ISSUE.value:
            self._handle_issue_cell_edit(row_id, col)

    def _handle_issue_cell_edit(self, row_id: str, column: str) -> None:
        """Initiate editing of an issue key cell."""
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
        """Save edited value and update entry."""
        new_value = self.editing_entry.get()
        self.tree.set(row_id, column="Issue", value=new_value)
        entry.issue_key = new_value.strip()
        entry.status = "pending"
        self.tree.set(row_id, column="Status", value=STATUS_DISPLAY["pending"])
        self.tree.set(row_id, column="Error", value="")
        self._cancel_edit()

    def _cancel_edit(self) -> None:
        """Cancel current edit operation."""
        if self.editing_entry:
            self.editing_entry.destroy()
            self.editing_entry = None

    def _load_credentials(self) -> None:
        """Load saved credentials into input fields."""
        base_url, email, api_key = CredentialManager.get_credentials()
        if any([base_url, email, api_key]):
            self.credentials_frame.load_credentials(base_url, email, api_key)

    def _browse_file(self) -> None:
        """Handle file selection dialog."""
        file_path = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
        if file_path:
            self.file_frame.set_file_path(file_path)
            self._load_entries(Path(file_path))

    def _load_entries(self, file_path: Path) -> None:
        """Load and display worklog entries from CSV."""
        adapter = CSVAdapter()
        self.entries = adapter.parse(file_path)
        seconds = 0
        for idx, entry in enumerate(self.entries):
            entry.status = "pending"
            entry.issue_key = IssueKeyParser.parse(entry.raw_issue_key)
            entry._idx = idx
            seconds += entry.duration

        total_hours = f"{seconds // 3600}:{(seconds % 3600) // 60}"
        self._update_status(f"Total: {total_hours}")
        self._update_table()

        self.process_btn.configure(state="normal")

    def _update_table(self) -> None:
        """Refresh the results table with current entries."""
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
        """Validate credentials and start processing thread."""
        base_url, email, api_key = self.credentials_frame.credentials
        if not all([base_url, email, api_key]):
            messagebox.showerror("Error", "Please fill all credentials fields")
            return

        CredentialManager.save_credentials(base_url, email, api_key)
        self.process_btn.configure(state="disabled")
        threading.Thread(target=self._process_entries, daemon=True).start()

    def _process_entries(self) -> None:
        """Process entries through Jira API (run in background thread)."""
        try:
            client = JiraClient(*self.credentials_frame.credentials)
            client.connect()

            self.results.clear()
            self.failed_entries.clear()
            entries_to_process = [
                e for e in self.entries if e.status in ("pending", "failed")
            ]

            total_entries = len(entries_to_process)

            for idx, entry in enumerate(entries_to_process):
                self._update_status(f"{idx}/{total_entries}")
                result = self._process_single_entry(client, entry)
                self._update_progress((idx + 1) / len(entries_to_process))
                self._update_row_status(entry._idx, entry, result)

                should_cooldown = idx % COOLDOWN_EVERY == 0
                if idx != 0 and idx != total_entries and should_cooldown:
                    self._update_status(f"Cooldowing for {COOLDOWN_SEC} seconds")
                    time.sleep(COOLDOWN_SEC)

            self._update_progress(color="green")
            self._show_results()

        except JIRAError as e:
            error = e.text
            self.after(
                0, lambda: messagebox.showerror("Error", f"An error occurred: {error}")
            )
            logger.error(e)

        except Exception as e:
            error = str(e)
            self.after(
                0, lambda: messagebox.showerror("Error", f"An error occurred: {error}")
            )
            logger.exception(e)
        finally:
            self.after(0, lambda: self.process_btn.configure(state="normal"))

    def _process_single_entry(
        self, client: JiraClient, entry: WorklogEntry
    ) -> ProcessingResult:
        """Process a single worklog entry and return result."""

        result = client.create_worklog(entry)
        entry.status = "success" if result.success else "failed"
        self.results.append(result)

        if not result.success:
            self.failed_entries.append(result)

        return result

    def _update_row_status(
        self, idx: int, entry: WorklogEntry, result: ProcessingResult
    ) -> None:
        """Update UI row with processing result."""
        row = self.tree.get_children()[idx]
        status = STATUS_DISPLAY["success" if result.success else "failed"]

        self.after(0, lambda: self.tree.set(row, "Status", status))
        if not result.success:
            error_msg = self._format_error(result.error)
            self.after(0, lambda: self.tree.set(row, "Error", error_msg))

    def _format_error(self, error: Exception) -> str:
        """Format error message for display."""
        return str(error.text) if isinstance(error, JIRAError) else str(error)

    def _update_progress(self, value: float = None, color: str = None) -> None:
        """Update progress bar value."""

        if value is not None:
            self.after(0, lambda: self.progress.set(value))
        if color is not None:
            self.after(0, lambda: self.progress.configure(fg_color=color))

    def _update_status(self, message: str) -> None:
        """Update the status label text."""
        self.after(0, lambda: self.status_label.configure(text=message))

    def _show_results(self) -> None:
        """Show final processing results summary."""
        success_count = sum(1 for r in self.results if r.success)
        total = len(self.results)
        message = (
            f"Posted {success_count}/{total} worklogs\n"
            f"{len(self.failed_entries)} failed entries - "
            "double-click to edit issue keys"
            if self.failed_entries
            else f"Successfully posted {success_count}/{total} worklogs"
        )
        self.after(0, lambda: messagebox.showinfo("Processing Complete", message))
