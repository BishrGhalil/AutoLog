import sys
import tkinter as tk
from pathlib import Path
from tkinter import ttk
from typing import Callable, Optional, Tuple

import customtkinter as ctk
import pytz
from customtkinter import ThemeManager

from autolog.constants import ColumnID


class FileSelectorFrame(ctk.CTkFrame):
    """Frame for file selection components."""

    def __init__(self, master: ctk.CTk, browse_callback: Callable[[], None], **kwargs):
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


class CellTooltip:
    """Displays tooltips for treeview cells with error messages."""

    def __init__(self, widget: ttk.Treeview):
        self.widget = widget
        self.tipwindow: Optional[tk.Toplevel] = None
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

    def __init__(self, master: ctk.CTk, **kwargs):
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


class ScrollableDropdown(tk.Toplevel):
    def __init__(
        self,
        master,
        values,
        callback,
        fg_color,
        text_color,
        font,
        widget_scaling,
        width,
    ):
        super().__init__(master)
        self.withdraw()  # Hide the window initially to prevent automatic opening
        self.overrideredirect(True)  # Remove window decorations
        self.callback = callback
        self.values = values
        self.fg_color = fg_color
        self.text_color = text_color
        self.font = font
        self.widget_scaling = widget_scaling
        self.width = width

        # Set geometry with the specified width and a fixed height
        self.geometry(f"{int(self.width)}x200")

        # Frame to hold the listbox and scrollbar
        self.frame = tk.Frame(self, bg=self.fg_color)
        self.frame.pack(fill="both", expand=True)

        # Listbox for options
        self.listbox = tk.Listbox(
            self.frame,
            bg=self.fg_color,
            fg=self.text_color,
            font=self.font,
            selectbackground=self.fg_color,
            selectforeground=self.text_color,
            selectmode="single",
            highlightthickness=0,
            height=10,  # Show up to 10 items, scroll beyond that
            borderwidth=0,
        )
        self.scrollbar = ctk.CTkScrollbar(
            self.frame, orientation="vertical", command=self.listbox.yview
        )
        self.listbox.config(yscrollcommand=self.scrollbar.set)

        # Populate the listbox with values
        for value in self.values:
            self.listbox.insert(tk.END, value)

        self.listbox.pack(side="left", fill="both", expand=True, padx=8, pady=8)
        self.scrollbar.pack(side="right", fill="y")

        # Bindings for selection and focus loss
        self.listbox.bind("<<ListboxSelect>>", self.on_select)
        self.bind("<FocusOut>", self.on_focus_out)

    def on_select(self, event):
        selection = self.listbox.curselection()
        if selection:
            value = self.listbox.get(selection[0])
            self.callback(value)
            self.destroy()  # Destroy the dropdown after selection

    def on_focus_out(self, event):
        self.destroy()  # Destroy the dropdown when it loses focus

    def open(self, x, y):
        # Adjust y-position based on platform (consistent with CTkOptionMenu)
        if sys.platform == "darwin":
            y += self.widget_scaling * 8
        else:
            y += self.widget_scaling * 3
        self.geometry(f"+{int(x)}+{int(y)}")
        self.deiconify()  # Show the window
        self.focus_set()


class ScrollableCTkOptionMenu(ctk.CTkOptionMenu):
    def __init__(self, *args, **kwargs):
        # Extract and store dropdown settings with defaults from the theme
        self._dropdown_fg_color = kwargs.pop(
            "dropdown_fg_color", ThemeManager.theme["DropdownMenu"]["fg_color"]
        )
        self._dropdown_text_color = kwargs.pop(
            "dropdown_text_color", ThemeManager.theme["DropdownMenu"]["text_color"]
        )
        self._dropdown_font = kwargs.pop("dropdown_font", ctk.CTkFont())
        super().__init__(*args, **kwargs)
        # Note: We do NOT create self._dropdown_menu here

    def configure(self, **kwargs):
        """Override configure to handle dropdown settings."""
        if "values" in kwargs:
            self._values = kwargs.pop(
                "values"
            )  # Update values, dropdown will use them when created
        if "dropdown_fg_color" in kwargs:
            self._dropdown_fg_color = kwargs.pop("dropdown_fg_color")
        if "dropdown_text_color" in kwargs:
            self._dropdown_text_color = kwargs.pop("dropdown_text_color")
        if "dropdown_font" in kwargs:
            self._dropdown_font = kwargs.pop("dropdown_font")
        super().configure(**kwargs)  # Let parent handle remaining kwargs

    def cget(self, attribute_name):
        """Override cget to return stored dropdown settings."""
        if attribute_name == "dropdown_fg_color":
            return self._dropdown_fg_color
        elif attribute_name == "dropdown_text_color":
            return self._dropdown_text_color
        elif attribute_name == "dropdown_font":
            return self._dropdown_font
        else:
            return super().cget(attribute_name)

    def _open_dropdown_menu(self):
        """Create a new ScrollableDropdown instance each time the dropdown is opened."""
        # Apply current theme settings
        fg_color = self._apply_appearance_mode(self._dropdown_fg_color)
        text_color = self._apply_appearance_mode(self._dropdown_text_color)
        font = self._apply_font_scaling(self._dropdown_font)
        widget_scaling = self._get_widget_scaling()
        width = self._apply_widget_scaling(
            self._desired_width
        )  # Use desired width, scaled

        # Create a new dropdown instance
        dropdown = ScrollableDropdown(
            master=self,
            values=self._values,
            callback=self._dropdown_callback,
            fg_color=fg_color,
            text_color=text_color,
            font=font,
            widget_scaling=widget_scaling,
            width=width,
        )
        # Position it below the option menu
        x = self.winfo_rootx()
        y = self.winfo_rooty() + self._apply_widget_scaling(self._current_height)
        dropdown.open(x, y)


class OptionsFrame(ctk.CTkFrame):
    """Frame for configuring processing options."""

    def __init__(self, master: ctk.CTk, **kwargs):
        super().__init__(master, **kwargs)
        self.prevent_duplicates_var = ctk.BooleanVar(value=True)
        self.timezone_var = ctk.StringVar(value="Asia/Damascus")
        self._build_widgets()
        self._layout()

    def _build_widgets(self) -> None:
        self.tz_label = ctk.CTkLabel(self, text="CSV Timezone:")
        self.tz_selector = ScrollableCTkOptionMenu(
            self, values=pytz.common_timezones, variable=self.timezone_var, width=300
        )
        self.checkbox = ctk.CTkCheckBox(
            self, text="Prevent duplicate entries", variable=self.prevent_duplicates_var
        )

    def _layout(self) -> None:
        self.tz_label.pack(side="left", padx=5)
        self.tz_selector.pack(side="left", padx=5)
        self.checkbox.pack(side="right", padx=10)

    @property
    def selected_timezone(self) -> str:
        return self.timezone_var.get()
