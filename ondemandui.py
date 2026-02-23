# python -m pip install tkcalendar
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from tkcalendar import DateEntry
import requests
import threading
from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime
import webbrowser
import time

# ────────────────────────────────────────────────
# Constants & Configuration
# ────────────────────────────────────────────────
BASE_API_URL = "https://api.ms-tech.in/v17/setcommandtogateway"
LOG_VIEWER_URL = "http://172.104.244.42/kptclcommandlogs"
APP_TITLE = "KPTCL Gateway Command Console"
DEFAULT_GEOMETRY = "1280x780"
MIN_WINDOW_SIZE = (100, 100)

DATE_FORMAT_API = "dd-mm-yyyy"
TIME_FORMAT_DISPLAY = "%H:%M"
MAX_HISTORY = 12
DEFAULT_METER_NUMBER = "65"

# ────────────────────────────────────────────────
# Command Metadata
# ────────────────────────────────────────────────
@dataclass
class CommandInfo:
    number: int
    name: str
    requires: str
    option_values: Optional[List[str]] = None
    tooltip: str = ""

COMMANDS = [
    CommandInfo( 1, "Full Load", "date"),
    CommandInfo( 2, "Block Wise", "add_block", tooltip="Date + custom blocks entered by user"),
    CommandInfo( 3, "Config Profile", "option", option_values=["IP","L","B","DL","E"], tooltip="IP,L,B,DL,E"),
    CommandInfo( 4, "Billing", "none"),
    CommandInfo( 5, "Read Scalar", "none"),
    CommandInfo( 6, "Read Events", "none"),
    CommandInfo( 7, "Read OBIS", "none"),
    CommandInfo( 8, "Format Node", "none"),
    CommandInfo( 9, "Instant Profile", "none"),
    CommandInfo(10, "Select Billing", "text", tooltip="Enter Pakets 1_3 2_5 3_4 etc."),
    CommandInfo(11, "Date Load Packet", "daily_date"),
    CommandInfo(12, "Clear All", "none"),
    CommandInfo(13, "Read Daily Load", "daily_date"),
    CommandInfo(14, "EC", "none"),
    CommandInfo(15, "Customized Load", "range"),
    CommandInfo(17, "ESP Restart", "none"),
    CommandInfo(18, "Ethernet Format", "none"),
    CommandInfo(19, "Delete On Demand", "none"),
    CommandInfo(20, "Set ID for Ethernet", "text", tooltip="Enter new Ethernet ID"),
    CommandInfo(21, "Select IP for Ethernet","text", tooltip="Enter IP address"),
    CommandInfo(22, "DL Range", "range"),
    CommandInfo(23, "Read All Data", "none"),
]

# ────────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────────
class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip = None
        widget.bind("<Enter>", self.show)
        widget.bind("<Leave>", self.hide)

    def show(self, event=None):
        if not self.text or self.tip: return
        x = self.widget.winfo_rootx() + 24
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 4
        self.tip = tk.Toplevel(self.widget)
        self.tip.wm_overrideredirect(True)
        self.tip.wm_geometry(f"+{x}+{y}")
        label = tk.Label(self.tip, text=self.text, background="#ffffe0",
                         relief="solid", borderwidth=1, padx=6, pady=3,
                         font=("Segoe UI", 9))
        label.pack()

    def hide(self, event=None):
        if self.tip:
            self.tip.destroy()
            self.tip = None

# ────────────────────────────────────────────────
# Main Application
# ────────────────────────────────────────────────
class GatewayCommandApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry(DEFAULT_GEOMETRY)
        self.root.minsize(*MIN_WINDOW_SIZE)
        self.root.configure(bg="#f5f5f7")

        self.selected_cmd: Optional[CommandInfo] = None
        self.widgets = {}
        self.sending = False
        self.added_blocks: List[str] = []
        self.last_send_time = 0

        self._setup_style()
        self._build_ui()
        self._select_first_command()
        self.root.bind("<Return>", self._on_enter_key)

    def _setup_style(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TButton", padding=6)
        style.configure("Command.TButton", font=("Segoe UI", 10), padding=8)
        style.configure("Accent.TButton", font=("Segoe UI", 11, "bold"),
                        background="#1e88e5", foreground="white")
        style.map("Accent.TButton", background=[("active", "#1565c0"), ("disabled", "#aaa")])
        style.configure("TLabelframe.Label", font=("Segoe UI", 11, "bold"))

    def _build_ui(self):
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        self._build_header()
        self._build_main_area()
        self._build_log_area()

    def _build_header(self):
        hdr = ttk.Frame(self.root, padding="12 8")
        hdr.grid(row=0, column=0, sticky="ew")

        ttk.Label(hdr, text="Node:").grid(row=0, column=0, padx=(0,4), sticky="w")
        self.node_type = ttk.Combobox(hdr, values=["NSDCU", "NSGW"], state="readonly", width=10)
        self.node_type.grid(row=0, column=1, padx=4)
        self.node_type.current(0)

        ttk.Label(hdr, text="Gateway ID:").grid(row=0, column=2, padx=(16,4), sticky="w")
        self.gwid_entry = ttk.Entry(hdr, width=22)
        self.gwid_entry.grid(row=0, column=3, padx=4, sticky="w")

        ttk.Label(hdr, text="Meter No/Slave ID:").grid(row=0, column=4, padx=(20,6), sticky="w")
        self.meter_entry = ttk.Entry(hdr, width=11)
        self.meter_entry.insert(0, str(DEFAULT_METER_NUMBER))
        self.meter_entry.grid(row=0, column=5, padx=6, sticky="w")

        ttk.Button(hdr, text="Log Viewer", command=lambda: webbrowser.open(LOG_VIEWER_URL)) \
           .grid(row=0, column=6, padx=(20,0))

        hdr.columnconfigure(7, weight=1)

    def _build_main_area(self):
        main = ttk.Frame(self.root, padding=10)
        main.grid(row=1, column=0, sticky="nsew")
        main.grid_rowconfigure(0, weight=1)
        main.grid_columnconfigure(0, weight=3)
        main.grid_columnconfigure(1, weight=2)

        cmd_frame = ttk.LabelFrame(main, text=" Available Commands ", padding=5)
        cmd_frame.grid(row=0, column=0, sticky="nsew", padx=(0,8))

        scroll = tk.Canvas(cmd_frame, highlightthickness=0)
        scbar = ttk.Scrollbar(cmd_frame, orient="vertical", command=scroll.yview)
        inner = ttk.Frame(scroll)
        inner.bind("<Configure>", lambda e: scroll.configure(scrollregion=scroll.bbox("all")))
        scroll.create_window((0,0), window=inner, anchor="nw")
        scroll.configure(yscrollcommand=scbar.set)
        scroll.pack(side="left", fill="both", expand=True)
        scbar.pack(side="right", fill="y")

        self._populate_commands(inner)

        self.param_frame = ttk.LabelFrame(main, text=" Command Parameters ", padding=12)
        self.param_frame.grid(row=0, column=1, sticky="nsew")

        canvas = tk.Canvas(self.param_frame, highlightthickness=0)
        scbar_param = ttk.Scrollbar(self.param_frame, orient="vertical", command=canvas.yview)
        self.param_container = ttk.Frame(canvas)
        self.param_container.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0,0), window=self.param_container, anchor="nw")
        canvas.configure(yscrollcommand=scbar_param.set)
        canvas.pack(side="left", fill="both", expand=True)
        scbar_param.pack(side="right", fill="y")

        send_row = ttk.Frame(self.param_frame)
        send_row.pack(fill="x", pady=(12,0), side="bottom")

        self.copy_btn = ttk.Button(send_row, text="Copy Command", command=self._copy_command)
        self.copy_btn.pack(side="left")

        self.send_button = ttk.Button(send_row, text=" Send Command ", style="Accent.TButton",
                                      command=self._on_send_command)
        self.send_button.pack(side="right")

    def _populate_commands(self, parent):
        parent.configure(padding=6)
        cols = 2
        for c in range(cols):
            parent.columnconfigure(c, weight=1)

        r, c = 0, 0
        for cmd in COMMANDS:
            btn = ttk.Button(
                parent,
                text=f"{cmd.number:2d} {cmd.name}",
                style="Command.TButton",
                command=lambda x=cmd: self._select_command(x)
            )
            btn.grid(row=r, column=c, padx=4, pady=3, sticky="ew")
            ToolTip(btn, cmd.tooltip or cmd.name)
            c += 1
            if c >= cols:
                c = 0
                r += 1

    def _build_log_area(self):
        logf = ttk.Frame(self.root, padding="10 4 10 10")
        logf.grid(row=2, column=0, sticky="nsew")
        self.root.grid_rowconfigure(2, weight=1)

        top = ttk.Frame(logf)
        top.pack(fill="x")
        ttk.Label(top, text="Command Log", font=("Segoe UI", 11, "bold")).pack(side="left")
        ttk.Button(top, text="Clear", command=self._clear_log).pack(side="right")

        self.log = scrolledtext.ScrolledText(
            logf,
            bg="#0d1117",
            fg="#d4d4d4",
            font=("Consolas", 10),
            insertbackground="white"
        )
        self.log.pack(fill="both", expand=True, pady=(6,0))

    def _select_first_command(self):
        if COMMANDS:
            self._select_command(COMMANDS[0])

    def _select_command(self, cmd: CommandInfo):
        self.selected_cmd = cmd
        self.param_frame.configure(text=f" {cmd.name} (Cmd {cmd.number}) ")

        for w in self.param_container.winfo_children():
            w.destroy()
        self.widgets.clear()
        self.added_blocks.clear()

        if cmd.requires == "none":
            ttk.Label(self.param_container, text="No parameters needed", foreground="#666").pack(pady=50)
        elif cmd.requires == "date":
            self._build_date_picker("Reference Date")
        elif cmd.requires == "daily_date":
            self._build_date_picker("Select Date")
        elif cmd.requires == "add_block":
            self._build_block_input_ui()
        elif cmd.requires == "range":
            self._build_range_input_ui()
        elif cmd.requires == "option" and cmd.option_values:
            self._build_option_selector(cmd.option_values)
        elif cmd.requires == "text":
            self._build_text_input(cmd.tooltip or "Value:")
        elif cmd.requires == "confirm":
            self._build_confirm_ui(cmd.name)

    def _build_date_picker(self, label_text="Date", key="date"):
        f = ttk.Frame(self.param_container)
        f.pack(fill="x", pady=6)
        ttk.Label(f, text=label_text).pack(anchor="w")
        de = DateEntry(
            f,
            date_pattern=DATE_FORMAT_API,
            width=14,
            year=2026,
            month=1,
            day=1
        )
        de.pack(anchor="w", pady=(3,0))
        self.widgets[key] = de

    def _build_time_picker(self, label_text="Time", key="time"):
        f = ttk.Frame(self.param_container)
        f.pack(fill="x", pady=6)
        ttk.Label(f, text=label_text).pack(anchor="w")
        time_frame = ttk.Frame(f)
        time_frame.pack(anchor="w", pady=(3,0))

        hour = ttk.Combobox(time_frame, values=[f"{i:02d}" for i in range(24)], width=5, state="readonly")
        hour.current(0)
        hour.pack(side="left")
        ttk.Label(time_frame, text=":").pack(side="left", padx=2)
        minute = ttk.Combobox(time_frame, values=[f"{i:02d}" for i in range(0,60,1)], width=5, state="readonly")
        minute.current(0)
        minute.pack(side="left")

        self.widgets[key] = (hour, minute)

    def _build_range_input_ui(self):
        ttk.Label(self.param_container, text="Load Profile Range", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(8,12))
        self._build_date_picker("Start Date", "start_date")
        self._build_time_picker("Start Time", "start_time")
        ttk.Separator(self.param_container, orient="horizontal").pack(fill="x", pady=12)
        self._build_date_picker("End Date", "end_date")
        self._build_time_picker("End Time", "end_time")
        ttk.Label(self.param_container,
                  text="→ Format example: N|65|15|000010022026_235911022026",
                  foreground="#666").pack(anchor="w", pady=(12,0))

    def _build_block_input_ui(self):
        self._build_date_picker("Reference Date")
        f = ttk.Frame(self.param_container)
        f.pack(fill="x", pady=12)
        ttk.Label(f, text="Enter block/suffix (e.g. _00_14_00_12)").pack(anchor="w")
        self.block_entry = ttk.Entry(f, width=25)
        self.block_entry.pack(side="left", padx=(0,8), pady=(4,0))
        self.block_entry.focus_set()
        ttk.Button(f, text="Add block", command=self._add_custom_block).pack(side="left", pady=(4,0))

        self.block_listbox = tk.Listbox(self.param_container, height=2, width=40)
        self.block_listbox.pack(fill="x", pady=(12,4))

        ttk.Button(self.param_container, text="Clear All", command=self._clear_blocks)\
           .pack(anchor="w", pady=(0,8))

        ttk.Label(self.param_container,
                  text="One separate command will be sent for each added block",
                  foreground="#666").pack(anchor="w", pady=(4,0))

    def _build_text_input(self, label_text: str):
        f = ttk.Frame(self.param_container)
        f.pack(fill="x", pady=20)
        ttk.Label(f, text=label_text).pack(anchor="w")
        entry = ttk.Entry(f, width=32)
        entry.pack(anchor="w", pady=(6,0))
        self.widgets["text"] = entry

    def _build_confirm_ui(self, cmd_name: str):
        ttk.Label(self.param_container,
                  text=f"Execute {cmd_name}?\nThis action may be irreversible.",
                  foreground="#c62828", justify="left").pack(pady=30, anchor="w")
        f = ttk.Frame(self.param_container)
        f.pack(fill="x", pady=10)
        ttk.Label(f, text="Optional reason/note:").pack(anchor="w")
        note = tk.Text(f, height=3, width=40, wrap="word")
        note.pack(anchor="w", pady=(4,0))
        self.widgets["note"] = note

    def _add_custom_block(self):
        block = self.block_entry.get().strip()
        if not block:
            messagebox.showwarning("Empty", "Please type something in the block field")
            return
        if block in self.added_blocks:
            messagebox.showinfo("Duplicate", f"Block '{block}' already added")
            return
        self.added_blocks.append(block)
        self.block_listbox.insert(tk.END, f"→ {block}")
        self.block_entry.delete(0, tk.END)
        self.block_entry.focus_set()

    def _clear_blocks(self):
        self.added_blocks.clear()
        self.block_listbox.delete(0, tk.END)

    def _build_option_selector(self, values: List[str]):
        f = ttk.Frame(self.param_container)
        f.pack(fill="x", pady=20)
        ttk.Label(f, text="Select option:").pack(anchor="w")
        cb = ttk.Combobox(f, values=values, state="readonly", width=20)
        cb.current(0)
        cb.pack(anchor="w", pady=(4,0))
        self.widgets["option"] = cb

    # ─── Core Logic ─────────────────────────────────────────────────
    def _get_gwid(self) -> str:
        raw = self.gwid_entry.get().strip()
        if not raw:
            raise ValueError("Gateway ID is required")
        return f"{self.node_type.get()}{raw}"

    def _get_meter_number(self) -> str:
        val = self.meter_entry.get().strip()
        if not val:
            raise ValueError("Meter number / Slave ID is required")
        return val

    def _format_datetime_range(self) -> str:
        def get_dt(key_date: str, key_time: str) -> str:
            date_obj = self.widgets[key_date].get_date()
            hour_combo, min_combo = self.widgets[key_time]
            hh = int(hour_combo.get())
            mm = int(min_combo.get())
            return (
                f"{hh:02d}"
                f"{mm:02d}"
                f"{date_obj.day:02d}"
                f"{date_obj.month:02d}"
                f"{date_obj.year:04d}"
            )

        start_str = get_dt("start_date", "start_time")
        end_str = get_dt("end_date", "end_time")
        return f"{start_str}_{end_str}"

    def _format_daily_date(self) -> str:
        if "date" not in self.widgets:
            raise ValueError("Date not selected")
        date_obj = self.widgets["date"].get_date()
        return (
            f"{date_obj.day:02d}"
            f"{date_obj.month:02d}"
            f"{date_obj.year:04d}"
        )

    def _build_command_strings(self) -> List[str]:
        if not self.selected_cmd:
            raise ValueError("No command selected")

        meter = self._get_meter_number()
        cmd = self.selected_cmd
        base = f"N|{meter}|{cmd.number}"
        commands = []

        r = cmd.requires
        if r == "none":
            commands.append(base + "|1")
        elif r == "date":
            d = self.widgets["date"].get()
            if not d:
                raise ValueError("Date is required")
            commands.append(base + f"|{d}")
        elif r == "daily_date":
            formatted_date = self._format_daily_date()
            commands.append(base + f"|{formatted_date}")
        elif r == "add_block":
            d = self.widgets["date"].get()
            if not d: raise ValueError("Date is required")
            if not self.added_blocks: raise ValueError("Add at least one block")
            for block in self.added_blocks:
                commands.append(f"{base}|{d}{block}")
        elif r == "option":
            val = self.widgets["option"].get().strip()
            if not val: raise ValueError("Select an option")
            commands.append(base + f"|{val}")
        elif r == "range":
            range_str = self._format_datetime_range()
            commands.append(base + f"|{range_str}")
        elif r == "text":
            val = self.widgets["text"].get().strip()
            if not val: raise ValueError("Value is required")
            commands.append(base + f"|{val}")
        elif r == "confirm":
            note_widget = self.widgets.get("note")
            note = note_widget.get("1.0", tk.END).strip() if note_widget else ""
            suffix = f"|{note}" if note else "|1"
            commands.append(base + suffix)

        return commands

    def _on_send_command(self):
        if self.sending:
            return

        now = time.time()
        if now - self.last_send_time < 0.8:
            return
        self.last_send_time = now

        try:
            gwid = self._get_gwid()
            commands = self._build_command_strings()
        except ValueError as e:
            messagebox.showwarning("Input Error", str(e))
            return

        if not commands:
            messagebox.showwarning("Nothing to send", "Missing required parameters")
            return

        text = "\n".join(commands)
        n = len(commands)
        if not messagebox.askyesno("Confirm Send", f"Send {n} command{'s' if n>1 else ''}?\n\n{text}"):
            return

        self.sending = True
        self.send_button.configure(text=" Sending... ", state="disabled")

        threading.Thread(target=self._send_multiple, args=(gwid, commands), daemon=True).start()

    def _on_enter_key(self, event):
        if not self.sending:
            self._on_send_command()
        return "break"

    def _send_multiple(self, gwid: str, commands: List[str]):
        for cmd_str in commands:
            try:
                resp = requests.get(
                    f"{BASE_API_URL}?gwid={gwid}&command_info={cmd_str}",
                    timeout=15
                )
                resp.raise_for_status()
                result = resp.text.strip() or "(empty)"
            except Exception as e:
                result = f"ERROR: {str(e)}"

            self.root.after(0, self._log_send_result, gwid, cmd_str, result)

        self.root.after(0, self._finish_sending)

    def _log_send_result(self, gwid, cmd, response):
        self._log(f"→ {gwid} | {cmd}")
        self._log(f" ← {response}")
        self._log("─" * 60)

    def _finish_sending(self):
        self.sending = False
        self.send_button.configure(text=" Send Command(s) ", state="normal")

    def _copy_command(self):
        try:
            cmds = self._build_command_strings()
            self.root.clipboard_clear()
            self.root.clipboard_append("\n".join(cmds))
            messagebox.showinfo("Copied", f"{len(cmds)} command{'s' if len(cmds)>1 else ''} copied")
        except ValueError as e:
            messagebox.showwarning("Cannot copy", str(e))

    def _log(self, msg: str):
        ts = datetime.now().strftime("%H:%M:%S")
        self.log.insert(tk.END, f"[{ts}] {msg}\n")
        self.log.see(tk.END)

    def _clear_log(self):
        self.log.delete("1.0", tk.END)


if __name__ == "__main__":
    root = tk.Tk()
    app = GatewayCommandApp(root)
    root.mainloop()

