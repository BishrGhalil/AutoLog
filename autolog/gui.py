"""GUI logic"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import customtkinter as ctk
from typing import Optional, List
from pathlib import Path
from autolog.models import WorklogEntry, ProcessingResult
from autolog.adapters import CSVAdapter
from autolog.issue_parser import IssueKeyParser
from autolog.jira_client import JiraClient
from autolog.keyring_manager import CredentialManager
import threading

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class WorklogApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Jira Worklog Importer")
        self.geometry("1200x700")
        
        self.base_url: Optional[str] = None
        self.email: Optional[str] = None
        self.api_key: Optional[str] = None
        self.entries: List[WorklogEntry] = []
        self.results: List[ProcessingResult] = []
        self.failed_entries: List[ProcessingResult] = []
        
        self._create_widgets()
        self._load_credentials()
        self._setup_treeview_editing()

    def _create_widgets(self):
        # Credentials Frame
        self.creds_frame = ctk.CTkFrame(self)
        self.creds_frame.pack(pady=10, padx=10, fill="x")

        self.base_url_entry = ctk.CTkEntry(self.creds_frame, placeholder_text="Jira Base URL")
        self.base_url_entry.pack(side="left", padx=5, fill="x", expand=True)

        self.email_entry = ctk.CTkEntry(self.creds_frame, placeholder_text="Email")
        self.email_entry.pack(side="left", padx=5, fill="x", expand=True)
        
        self.api_key_entry = ctk.CTkEntry(self.creds_frame, placeholder_text="API Key", show="*")
        self.api_key_entry.pack(side="left", padx=5, fill="x", expand=True)
        
        # File Selection
        self.file_frame = ctk.CTkFrame(self)
        self.file_frame.pack(pady=10, padx=10, fill="x")
        
        self.file_entry = ctk.CTkEntry(self.file_frame)
        self.file_entry.pack(side="left", padx=5, fill="x", expand=True)
        
        self.browse_btn = ctk.CTkButton(self.file_frame, text="Browse", command=self._browse_file)
        self.browse_btn.pack(side="left", padx=5)
        
        # Entries Table
        self.tree = ttk.Treeview(self, columns=("Date", "Duration", "Issue", "Status", "Error"), show="headings")
        self.tree.heading("Date", text="Date")
        self.tree.heading("Duration", text="Duration (mins)")
        self.tree.heading("Issue", text="Issue Key")
        self.tree.heading("Status", text="Status")
        self.tree.heading("Error", text="Error Message")
        self.tree.column("Error", width=300, stretch=True)
        self.tree.pack(pady=10, padx=10, fill="both", expand=True)
        
        # Progress and Actions
        self.progress = ctk.CTkProgressBar(self)
        self.progress.set(0)
        self.progress.pack(pady=5, padx=10, fill="x")
        
        self.process_btn = ctk.CTkButton(self, text="Process", command=self._start_processing)
        self.process_btn.pack(pady=10) 

    def _setup_treeview_editing(self):
        self.tree.bind("<Double-1>", self._on_cell_double_click)
        self.editing_entry = None

    def _on_cell_double_click(self, event):
        region = self.tree.identify("region", event.x, event.y)
        if region != "cell":
            return

        column = self.tree.identify_column(event.x)
        row_id = self.tree.identify_row(event.y)
        
        if column == "#3":  # Issue Key column
            status = self.tree.set(row_id, "Status")
            if "❌" not in status:
                return  # Only allow editing failed entries
            
            # Get current value and entry index
            current_value = self.tree.set(row_id, "Issue")
            index = self.tree.index(row_id)
            entry = self.entries[index]
            
            # Create editing widget
            x, y, width, height = self.tree.bbox(row_id, column)
            self.editing_entry = ctk.CTkEntry(self.tree, width=width, height=height)
            self.editing_entry.insert(0, current_value)
            self.editing_entry.place(x=x, y=y)
            
            def save_edit(event):
                new_value = self.editing_entry.get()
                self.tree.set(row_id, column="Issue", value=new_value)
                entry.issue_key = new_value.strip()
                entry.status = "pending"  # Add this line
                self.tree.set(row_id, column="Status", value="🔄 Pending")
                self.tree.set(row_id, column="Error", value="")
                self.editing_entry.destroy()
                self.editing_entry = None
            
            self.editing_entry.bind("<Return>", save_edit)
            self.editing_entry.bind("<FocusOut>", lambda e: self.editing_entry.destroy())
            self.editing_entry.focus_set()

    def _update_row_status(self, idx: int, result: ProcessingResult):
        status = "✅ Success" if result.success else "❌ Failed"
        error_msg = str(result.error)[:100] + "..." if result.error else ""
        self.after(0, lambda: self.tree.set(
            self.tree.get_children()[idx],
            column="Status",
            value=status
        ))
        self.after(0, lambda: self.tree.set(
            self.tree.get_children()[idx],
            column="Error",
            value=error_msg
        )) 

    def _load_credentials(self):
        base_url, email, api_key = CredentialManager.get_credentials()
        if base_url:
            self.base_url_entry.insert(0, base_url)
        if email:
            self.email_entry.insert(0, email)
        if api_key:
            self.api_key_entry.insert(0, api_key)

    def _browse_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
        if file_path:
            self.file_entry.delete(0, tk.END)
            self.file_entry.insert(0, file_path)
            self._load_entries(Path(file_path))

    def _load_entries(self, file_path: Path):
        adapter = CSVAdapter()
        self.entries = adapter.parse(file_path)
        # Initialize status for all entries
        for entry in self.entries:
            entry.status = "pending"
        self._update_table()

    def _update_table(self):
        self.tree.delete(*self.tree.get_children())
        for entry in self.entries:
            issue_key = entry.raw_issue_key
            self.tree.insert("", "end", values=(
                entry.date.strftime("%Y-%m-%d"),
                f"{entry.duration//3600}h {(entry.duration%3600)//60}m",
                issue_key or "⚠️ Missing",
                "Pending"
            ))

    def _start_processing(self):
        self.base_url = self.base_url_entry.get().strip()
        self.email = self.email_entry.get().strip()
        self.api_key = self.api_key_entry.get().strip()
        
        if not all([self.base_url, self.email, self.api_key]):
            messagebox.showerror("Error", "Please fill all credentials fields")
            return
        
        CredentialManager.save_credentials(self.base_url, self.email, self.api_key)
        
        thread = threading.Thread(target=self._process_entries)
        thread.start()

    def _process_entries(self):
        try:
            client = JiraClient(self.base_url, self.email, self.api_key)
            client.connect()
            
            self.failed_entries = []
            entries_to_process = [entry for entry in self.entries if entry.status in ("pending", "failed")]
            total = len(entries_to_process)
            
            for idx, entry in enumerate(entries_to_process):
                if entry.status == "pending" and not entry.issue_key:
                    entry.issue_key = IssueKeyParser.parse(entry.raw_issue_key)
                
                result = client.create_worklog(entry)
                entry.status = "success" if result.success else "failed"
                self.results.append(result)
                
                if not result.success:
                    self.failed_entries.append(result)
                
                self._update_progress((idx + 1) / total)
                self._update_row_status(self.entries.index(entry), result)
            
            self._show_results()
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Error", f"Connection failed: {str(e)}"))


    def _update_row_status(self, idx: int, result: ProcessingResult):
        status = "✅ Success" if result.success else "❌ Failed"
        self.after(0, lambda: self.tree.set(self.tree.get_children()[idx], "Status", status))

    def _update_progress(self, value: float):
        self.after(0, lambda: self.progress.set(value))

    def _show_results(self):
        success = sum(1 for r in self.results if r.success)
        total = len(self.results)
        
        if self.failed_entries:
            messagebox.showinfo(
                "Processing Complete",
                f"Posted {success}/{total} worklogs\n"
                f"{len(self.failed_entries)} failed entries - double-click to edit issue keys"
            )
        else:
            messagebox.showinfo("Complete", f"Successfully posted {success}/{total} worklogs") 

