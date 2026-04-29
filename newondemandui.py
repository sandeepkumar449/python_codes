# # python -m pip install tkcalendar
# import tkinter as tk
# from tkinter import ttk, messagebox, scrolledtext
# from tkcalendar import DateEntry
# import requests
# import threading
# from dataclasses import dataclass
# from typing import Optional, List
# from datetime import datetime
# import webbrowser
# import time

# # ────────────────────────────────────────────────
# # Constants & Configuration
# # ────────────────────────────────────────────────
# BASE_API_URL_NSDCU = "https://api.ms-tech.in/v17/setcommandtogateway"  # NSDCU
# BASE_API_URL_NSRT = "https://api.ms-tech.in/v14/setcommandtogateway"  # NSRT
# BASE_API_URL_NSGW = "https://api.ms-tech.in/v2/setcommandtogateway"  # NSGW

# API_MAP = {
#     "NSDCU": BASE_API_URL_NSDCU,
#     "NSRT":  BASE_API_URL_NSRT,
#     "NSGW":  BASE_API_URL_NSGW,
# }

# #LOG_VIEWER_URL = "http://172.104.244.42/kptclcommandlogs"
# LOG_VIEWER_URL_NSDCU = "http://172.104.244.42/kptclcommandlogs"
# LOG_VIEWER_URL_NSRT  = "http://172.104.244.42/rdprcommandlogs"
# LOG_VIEWER_URL_NSGW  = "http://172.104.244.42/commandlogs"

# LOG_VIEWER_MAP = {
#     "NSDCU": LOG_VIEWER_URL_NSDCU,
#     "NSRT":  LOG_VIEWER_URL_NSRT,
#     "NSGW":  LOG_VIEWER_URL_NSGW,
# }

# APP_TITLE = "KPTCL/RDPR ON DEMAND COMMAND CONSOLE"
# DEFAULT_GEOMETRY = "1180x700"
# MIN_WINDOW_SIZE = (100, 100)


# DATE_FORMAT_API = "dd-mm-yyyy"
# TIME_FORMAT_DISPLAY = "%H:%M"
# MAX_HISTORY = 12
# DEFAULT_METER_MAP = {
#     "NSDCU": "65",
#     "NSRT":  "NSRT",
#     "NSGW":  "NSTG",
# }
# # ────────────────────────────────────────────────
# # Command Metadata
# # ────────────────────────────────────────────────
# @dataclass
# class CommandInfo:
#     number: int
#     name: str
#     requires: str
#     option_values: Optional[List[str]] = None
#     tooltip: str = ""


# COMMANDS_NSDCU = [
#     CommandInfo( 1, "Full Load", "date"),
#     CommandInfo( 2, "Block Wise", "add_block", tooltip="Date + custom blocks entered by user"),
#     CommandInfo( 3, "Config Profile", "option", option_values=["IP","L","B","DL","E"], tooltip="IP,L,B,DL,E"),
#     CommandInfo( 4, "Billing", "none"),
#     CommandInfo( 5, "Read Scalar", "none"),
#     CommandInfo( 6, "Read Events", "none"),
#     CommandInfo( 7, "Read OBIS", "none"),
#     CommandInfo( 8, "Format Node", "none"),
#     CommandInfo( 9, "Instant Profile", "none"),
#     CommandInfo(10, "Select Billing", "text", tooltip="Enter Pakets 1_3 2_5 3_4 etc."),
#     CommandInfo(11, "Date Load Packet", "daily_date"),
#     CommandInfo(12, "Clear All", "none"),
#     CommandInfo(13, "Read Daily Load", "daily_date"),
#     CommandInfo(14, "EC", "none"),
#     CommandInfo(15, "Customized Load", "range"),
#     CommandInfo(17, "ESP Restart", "none"),
#     CommandInfo(18, "Ethernet Format", "none"),
#     CommandInfo(19, "Delete On Demand", "none"),
#     CommandInfo(20, "Set ID for Ethernet", "text", tooltip="Enter new Ethernet ID"),
#     CommandInfo(21, "Select IP for Ethernet","text", tooltip="Enter IP address"),
#     CommandInfo(22, "DL Range", "range"),
#     CommandInfo(23, "Read All Data", "none"),
# ]

# COMMANDS_NSRT = [
#     CommandInfo( 0, "Relay ON/OFF", "relay", option_values=["0", "1"], tooltip="0 OFF | 1 ON"),
#     CommandInfo( 1, "Full Load", "date"),
#     CommandInfo( 2, "Block Wise", "add_block", tooltip="Date + custom blocks entered by user"),
#     #CommandInfo( 3, "Config Profile", "option", option_values=["IP","L","B","DL","E"], tooltip="IP,L,B,DL,E"),
#     CommandInfo( 4, "Billing", "none"),
#     CommandInfo( 5, "Read Scalar", "none"),
#     CommandInfo( 6, "Read Events", "none"),
#     CommandInfo( 7, "Read OBIS", "none"),
#     CommandInfo( 8, "Format Node", "none"),
#     CommandInfo( 9, "Instant Profile", "none"),
#     CommandInfo(10, "Select Billing", "text", tooltip="Enter Pakets 1_3 2_5 3_4 etc."),
#     CommandInfo(11, "Date Load Packet", "daily_date"),
#     CommandInfo(12, "Clear All", "none"),
#     CommandInfo(13, "Read Daily Load", "daily_date"),
#     CommandInfo(14, "EC", "none"),
#     CommandInfo(15, "Customized Load", "range"),
#     CommandInfo(16, "Read Water Meter", "none"),
#     CommandInfo(17, "ESP Restart", "none"),
#     CommandInfo(18, "Delete On Demand", "none"),
# ]

# COMMANDS_NSGW = [
#     CommandInfo( 1, "Full Load", "date"),
#     CommandInfo( 2, "Block Wise", "add_block", tooltip="Date + custom blocks entered by user"),
#     #CommandInfo( 3, "Config Profile", "option", option_values=["IP","L","B","DL","E"], tooltip="IP,L,B,DL,E"),
#     CommandInfo( 4, "Billing", "none"),
#     CommandInfo( 5, "Read Scalar", "none"),
#     CommandInfo( 6, "Read Events", "none"),
#     CommandInfo( 7, "Read OBIS", "none"),
#     CommandInfo( 8, "Format Node", "none"),
#     CommandInfo( 9, "Instant Profile", "none"),
#     CommandInfo(10, "Select Billing", "text", tooltip="Enter Pakets 1_3 2_5 3_4 etc."),
#     CommandInfo(11, "Date Load Packet", "daily_date"),
#     CommandInfo(12, "Clear All", "none"),
#     CommandInfo(13, "Read Daily Load", "daily_date"),
#     CommandInfo(14, "EC", "none"),
#     CommandInfo(15, "Customized Load", "range"),
# ]



# # ────────────────────────────────────────────────
# # Helpers
# # ────────────────────────────────────────────────
# class ToolTip:
#     def __init__(self, widget, text):
#         self.widget = widget
#         self.text = text
#         self.tip = None
#         widget.bind("<Enter>", self.show)
#         widget.bind("<Leave>", self.hide)

#     def show(self, event=None):
#         if not self.text or self.tip: return
#         x = self.widget.winfo_rootx() + 24
#         y = self.widget.winfo_rooty() + self.widget.winfo_height() + 4
#         self.tip = tk.Toplevel(self.widget)
#         self.tip.wm_overrideredirect(True)
#         self.tip.wm_geometry(f"+{x}+{y}")
#         label = tk.Label(self.tip, text=self.text, background="#ffffe0",
#                          relief="solid", borderwidth=1, padx=6, pady=3,
#                          font=("Segoe UI", 9))
#         label.pack()

#     def hide(self, event=None):
#         if self.tip:
#             self.tip.destroy()
#             self.tip = None

# # ────────────────────────────────────────────────
# # Main Application
# # ────────────────────────────────────────────────
# class GatewayCommandApp:
#     def __init__(self, root: tk.Tk):
#         self.root = root
#         self.root.title(APP_TITLE)
#         self.root.geometry(DEFAULT_GEOMETRY)
#         self.root.minsize(*MIN_WINDOW_SIZE)
#         self.root.configure(bg="#f5f5f7")

#         self.current_node = tk.StringVar(value="NSDCU")

#         self.selected_cmd: Optional[CommandInfo] = None
#         self.widgets = {}
#         self.sending = False
#         self.added_blocks: List[str] = []
#         self.last_send_time = 0

#         self._setup_style()
#         self._build_ui()
#         self._select_first_command()

#         self.root.bind("<Return>", self._on_enter_key)

#     def _setup_style(self):
#         style = ttk.Style()
#         style.theme_use("clam")
#         style.configure("TButton", padding=6)
#         style.configure("Command.TButton", font=("Segoe UI", 10), padding=8)
#         style.configure("Accent.TButton", font=("Segoe UI", 11, "bold"),
#                         background="#1e88e5", foreground="white")
#         style.map("Accent.TButton", background=[("active", "#1565c0"), ("disabled", "#aaa")])
#         style.configure("TLabelframe.Label", font=("Segoe UI", 11, "bold"))

#     def _build_ui(self):
#         self.root.grid_rowconfigure(1, weight=1)
#         self.root.grid_columnconfigure(0, weight=1)

#         self._build_header()
#         self._build_main_area()
#         self._build_log_area()

#     def _open_log_viewer(self):
#         selected_node = self.node_type.get()
#         log_url = LOG_VIEWER_MAP.get(selected_node)

#         if not log_url:
#             print("Invalid Node Selected")
#             return

#         webbrowser.open(log_url)

#     def _update_meter_default(self, event=None):
#         selected_node = self.node_type.get()

#         # ---- Update Label Text ----
#         if selected_node == "NSDCU":
#             self.meter_label_var.set("Meter No/Slave ID:")
#         else:
#             self.meter_label_var.set("NODE ID NO :")

#         # ---- Update Default Entry Value ----
#         if selected_node in DEFAULT_METER_MAP:
#             self.meter_entry.delete(0, tk.END)
#             self.meter_entry.insert(0, DEFAULT_METER_MAP[selected_node])

#     def _build_header(self):
#         hdr = ttk.Frame(self.root, padding="12 8")
#         hdr.grid(row=0, column=0, sticky="ew")

#         ttk.Label(hdr, text="Node:").grid(row=0, column=0, padx=(0,4), sticky="w")

#         self.node_type = ttk.Combobox(
#             hdr,
#             values=["NSDCU", "NSGW", "NSRT"],
#             state="readonly",
#             width=10,
#             textvariable=self.current_node
#         )
#         self.node_type.grid(row=0, column=1, padx=4)
#         self.node_type.current(0)

#         self.node_type.bind("<<ComboboxSelected>>", self._on_node_change)

#         ttk.Label(hdr, text="Gateway ID:").grid(row=0, column=2, padx=(20,6), sticky="w")
#         self.gwid_entry = ttk.Entry(hdr, width=22)
#         self.gwid_entry.grid(row=0, column=3, padx=4, sticky="w")

#         self.meter_label_var = tk.StringVar()
#         self.meter_label = ttk.Label(hdr, textvariable=self.meter_label_var)
#         self.meter_label.grid(row=0, column=4, padx=(20,6), sticky="w")

#         self.meter_entry = ttk.Entry(hdr, width=22)
#         self.meter_entry.grid(row=0, column=5, padx=6, sticky="w")

#         self._update_meter_default()

#         ttk.Button(hdr, text="Log Viewer", command=self._open_log_viewer)\
#             .grid(row=0, column=6, padx=(20,0))

#         hdr.columnconfigure(7, weight=1)

#     def _on_node_change(self, event=None):
#         self._update_meter_default()
#         self._populate_commands(self.cmd_inner, self.current_node.get())
#         self._select_first_command()

#     def _build_main_area(self):
#         main = ttk.Frame(self.root, padding=10)
#         main.grid(row=1, column=0, sticky="nsew")
#         main.grid_rowconfigure(0, weight=1)
#         main.grid_columnconfigure(0, weight=3)
#         main.grid_columnconfigure(1, weight=2)

#         cmd_frame = ttk.LabelFrame(main, text=" Available Commands ", padding=5)
#         cmd_frame.grid(row=0, column=0, sticky="nsew", padx=(0,8))

#         scroll = tk.Canvas(cmd_frame, highlightthickness=0)
#         scbar = ttk.Scrollbar(cmd_frame, orient="vertical", command=scroll.yview)

#         self.cmd_inner = ttk.Frame(scroll)
#         self.cmd_inner.bind(
#             "<Configure>",
#             lambda e: scroll.configure(scrollregion=scroll.bbox("all"))
#         )

#         scroll.create_window((0,0), window=self.cmd_inner, anchor="nw")
#         scroll.configure(yscrollcommand=scbar.set)
#         scroll.pack(side="left", fill="both", expand=True)
#         scbar.pack(side="right", fill="y")

#         # Initial population
#         self._populate_commands(self.cmd_inner, self.current_node.get())

#         # Parameter frame (unchanged)
#         self.param_frame = ttk.LabelFrame(main, text=" Command Parameters ", padding=12)
#         self.param_frame.grid(row=0, column=1, sticky="nsew")

#         canvas = tk.Canvas(self.param_frame, highlightthickness=0)
#         scbar_param = ttk.Scrollbar(self.param_frame, orient="vertical", command=canvas.yview)

#         self.param_container = ttk.Frame(canvas)
#         self.param_container.bind(
#             "<Configure>",
#             lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
#         )

#         canvas.create_window((0,0), window=self.param_container, anchor="nw")
#         canvas.configure(yscrollcommand=scbar_param.set)
#         canvas.pack(side="left", fill="both", expand=True)
#         scbar_param.pack(side="right", fill="y")

#         send_row = ttk.Frame(self.param_frame)
#         send_row.pack(fill="x", pady=(12,0), side="bottom")

#         self.copy_btn = ttk.Button(send_row, text="Copy Command", command=self._copy_command)
#         self.copy_btn.pack(side="left")

#         self.send_button = ttk.Button(
#             send_row,
#             text=" Send Command ",
#             style="Accent.TButton",
#             command=self._on_send_command
#         )
#         self.send_button.pack(side="right")

#     def _populate_commands(self, parent, selected_node):

#         COMMAND_MAP = {
#             "NSDCU": COMMANDS_NSDCU,
#             "NSRT": COMMANDS_NSRT,
#             "NSGW": COMMANDS_NSGW,
#         }

#         commands = COMMAND_MAP.get(selected_node, [])

#         for widget in parent.winfo_children():
#             widget.destroy()

#         cols = 2
#         for i in range(cols):
#             parent.columnconfigure(i, weight=1)

#         r = 0
#         c = 0

#         for cmd in commands:
#             btn = ttk.Button(
#                 parent,
#                 text=f"{cmd.number:2d} {cmd.name}",
#                 style="Command.TButton",
#                 command=lambda x=cmd: self._select_command(x)
#             )
#             btn.grid(row=r, column=c, padx=4, pady=3, sticky="ew")
#             ToolTip(btn, cmd.tooltip or cmd.name)

#             c += 1
#             if c >= cols:
#                 c = 0
#                 r += 1

#     def _build_log_area(self):
#         logf = ttk.Frame(self.root, padding="10 4 10 10")
#         logf.grid(row=2, column=0, sticky="nsew")
#         self.root.grid_rowconfigure(2, weight=1)

#         top = ttk.Frame(logf)
#         top.pack(fill="x")
#         ttk.Label(top, text="Command Log", font=("Segoe UI", 11, "bold")).pack(side="left")
#         ttk.Button(top, text="Clear", command=self._clear_log).pack(side="right")

#         self.log = scrolledtext.ScrolledText(
#             logf,
#             bg="#0d1117",
#             fg="#d4d4d4",
#             font=("Consolas", 10),
#             insertbackground="white"
#         )
#         self.log.pack(fill="both", expand=True, pady=(6,0))

#     def _select_first_command(self):
#         COMMAND_MAP = {
#             "NSDCU": COMMANDS_NSDCU,
#             "NSRT": COMMANDS_NSRT,
#             "NSGW": COMMANDS_NSGW,
#         }

#         node = self.current_node.get()
#         cmds = COMMAND_MAP.get(node, [])

#         if cmds:
#             self._select_command(cmds[0])

#     def _select_command(self, cmd: CommandInfo):
#         self.selected_cmd = cmd
#         self.param_frame.configure(text=f" {cmd.name} (Cmd {cmd.number}) ")

#         for w in self.param_container.winfo_children():
#             w.destroy()
#         self.widgets.clear()
#         self.added_blocks.clear()

#         if cmd.requires == "none":
#             ttk.Label(self.param_container, text="No parameters needed", foreground="#666").pack(pady=50)
#         elif cmd.requires == "date":
#             self._build_date_picker("Reference Date")
#         elif cmd.requires == "daily_date":
#             self._build_date_picker("Select Date")
#         elif cmd.requires == "add_block":
#             self._build_block_input_ui()
#         elif cmd.requires == "range":
#             self._build_range_input_ui()
#         elif cmd.requires == "option" and cmd.option_values:
#             self._build_option_selector(cmd.option_values)
#         elif cmd.requires == "relay":
#             self._build_relay_selector(cmd.option_values)
#         elif cmd.requires == "text":
#             self._build_text_input(cmd.tooltip or "Value:")
#         elif cmd.requires == "confirm":
#             self._build_confirm_ui(cmd.name)

#     def _build_date_picker(self, label_text="Date", key="date"):
#         f = ttk.Frame(self.param_container)
#         f.pack(fill="x", pady=6)
#         ttk.Label(f, text=label_text).pack(anchor="w")
#         de = DateEntry(
#             f,
#             date_pattern=DATE_FORMAT_API,
#             width=14,
#             year=2026,
#             month=1,
#             day=1
#         )
#         de.pack(anchor="w", pady=(3,0))
#         self.widgets[key] = de

#     def _build_time_picker(self, label_text="Time", key="time"):
#         f = ttk.Frame(self.param_container)
#         f.pack(fill="x", pady=6)
#         ttk.Label(f, text=label_text).pack(anchor="w")
#         time_frame = ttk.Frame(f)
#         time_frame.pack(anchor="w", pady=(3,0))

#         hour = ttk.Combobox(time_frame, values=[f"{i:02d}" for i in range(24)], width=5, state="readonly")
#         hour.current(0)
#         hour.pack(side="left")
#         ttk.Label(time_frame, text=":").pack(side="left", padx=2)
#         minute = ttk.Combobox(time_frame, values=[f"{i:02d}" for i in range(0,60,1)], width=5, state="readonly")
#         minute.current(0)
#         minute.pack(side="left")

#         self.widgets[key] = (hour, minute)

#     def _build_range_input_ui(self):
#         ttk.Label(self.param_container, text="Load Profile Range", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(8,12))
#         self._build_date_picker("Start Date", "start_date")
#         self._build_time_picker("Start Time", "start_time")
#         ttk.Separator(self.param_container, orient="horizontal").pack(fill="x", pady=12)
#         self._build_date_picker("End Date", "end_date")
#         self._build_time_picker("End Time", "end_time")
#         ttk.Label(self.param_container,
#                   text="→ Format example: N|65|15|000010022026_235911022026",
#                   foreground="#666").pack(anchor="w", pady=(12,0))

#     def _build_block_input_ui(self):
#         self._build_date_picker("Reference Date")
#         f = ttk.Frame(self.param_container)
#         f.pack(fill="x", pady=12)
#         ttk.Label(f, text="Enter block/suffix (e.g. _00_14_00_12)").pack(anchor="w")
#         self.block_entry = ttk.Entry(f, width=25)
#         self.block_entry.pack(side="left", padx=(0,8), pady=(4,0))
#         self.block_entry.focus_set()
#         ttk.Button(f, text="Add block", command=self._add_custom_block).pack(side="left", pady=(4,0))

#         self.block_listbox = tk.Listbox(self.param_container, height=2, width=40)
#         self.block_listbox.pack(fill="x", pady=(12,4))

#         ttk.Button(self.param_container, text="Clear All", command=self._clear_blocks)\
#            .pack(anchor="w", pady=(0,8))

#         ttk.Label(self.param_container,
#                   text="One separate command will be sent for each added block",
#                   foreground="#666").pack(anchor="w", pady=(4,0))

#     def _build_text_input(self, label_text: str):
#         f = ttk.Frame(self.param_container)
#         f.pack(fill="x", pady=20)
#         ttk.Label(f, text=label_text).pack(anchor="w")
#         entry = ttk.Entry(f, width=32)
#         entry.pack(anchor="w", pady=(6,0))
#         self.widgets["text"] = entry

#     def _build_confirm_ui(self, cmd_name: str):
#         ttk.Label(self.param_container,
#                   text=f"Execute {cmd_name}?\nThis action may be irreversible.",
#                   foreground="#c62828", justify="left").pack(pady=30, anchor="w")
#         f = ttk.Frame(self.param_container)
#         f.pack(fill="x", pady=10)
#         ttk.Label(f, text="Optional reason/note:").pack(anchor="w")
#         note = tk.Text(f, height=3, width=40, wrap="word")
#         note.pack(anchor="w", pady=(4,0))
#         self.widgets["note"] = note

#     def _add_custom_block(self):
#         block = self.block_entry.get().strip()
#         if not block:
#             messagebox.showwarning("Empty", "Please type something in the block field")
#             return
#         if block in self.added_blocks:
#             messagebox.showinfo("Duplicate", f"Block '{block}' already added")
#             return
#         self.added_blocks.append(block)
#         self.block_listbox.insert(tk.END, f"→ {block}")
#         self.block_entry.delete(0, tk.END)
#         self.block_entry.focus_set()

#     def _clear_blocks(self):
#         self.added_blocks.clear()
#         self.block_listbox.delete(0, tk.END)

#     def _build_option_selector(self, values: List[str]):
#         f = ttk.Frame(self.param_container)
#         f.pack(fill="x", pady=20)
#         ttk.Label(f, text="Select option:").pack(anchor="w")
#         cb = ttk.Combobox(f, values=values, state="readonly", width=20)
#         cb.current(0)
#         cb.pack(anchor="w", pady=(4,0))
#         self.widgets["option"] = cb

#     def _build_relay_selector(self, values: List[str]):
#         f = ttk.Frame(self.param_container)
#         f.pack(fill="x", pady=20)
#         ttk.Label(f, text="Relay Control:").pack(anchor="w")
#         cb = ttk.Combobox(f, values=["ON (1)", "OFF (0)"], state="readonly", width=20)
#         cb.current(1)  # default OFF
#         cb.pack(anchor="w", pady=(4, 0))
#         self.widgets["relay"] = cb

#     # ─── Core Logic ─────────────────────────────────────────────────
#     def _get_gwid(self) -> str:
#         raw = self.gwid_entry.get().strip()
#         if not raw:
#             raise ValueError("Gateway ID is required")
#         return f"{self.node_type.get()}{raw}"

#     def _get_meter_number(self) -> str:
#         val = self.meter_entry.get().strip()
#         if not val:
#             raise ValueError("Meter number / Slave ID is required")
#         return val

#     def _format_datetime_range(self) -> str:
#         def get_dt(key_date: str, key_time: str) -> str:
#             date_obj = self.widgets[key_date].get_date()
#             hour_combo, min_combo = self.widgets[key_time]
#             hh = int(hour_combo.get())
#             mm = int(min_combo.get())
#             return (
#                 f"{hh:02d}"
#                 f"{mm:02d}"
#                 f"{date_obj.day:02d}"
#                 f"{date_obj.month:02d}"
#                 f"{date_obj.year:04d}"
#             )

#         start_str = get_dt("start_date", "start_time")
#         end_str = get_dt("end_date", "end_time")
#         return f"{start_str}_{end_str}"

#     def _format_daily_date(self) -> str:
#         if "date" not in self.widgets:
#             raise ValueError("Date not selected")
#         date_obj = self.widgets["date"].get_date()
#         return (
#             f"{date_obj.day:02d}"
#             f"{date_obj.month:02d}"
#             f"{date_obj.year:04d}"
#         )

#     def _build_command_strings(self) -> List[str]:
#         if not self.selected_cmd:
#             raise ValueError("No command selected")

#         meter = self._get_meter_number()
#         cmd = self.selected_cmd
#         base = f"N|{meter}|{cmd.number}"
#         commands = []

#         r = cmd.requires
#         if r == "none":
#             commands.append(base + "|1")
#         elif r == "date":
#             d = self.widgets["date"].get()
#             if not d:
#                 raise ValueError("Date is required")
#             commands.append(base + f"|{d}")
#         elif r == "daily_date":
#             formatted_date = self._format_daily_date()
#             commands.append(base + f"|{formatted_date}")
#         elif r == "add_block":
#             d = self.widgets["date"].get()
#             if not d: raise ValueError("Date is required")
#             if not self.added_blocks: raise ValueError("Add at least one block")
#             for block in self.added_blocks:
#                 commands.append(f"{base}|{d}{block}")
#         elif r == "option":
#             val = self.widgets["option"].get().strip()
#             if not val: raise ValueError("Select an option")
#             commands.append(base + f"|{val}")
#         elif r == "range":
#             range_str = self._format_datetime_range()
#             commands.append(base + f"|{range_str}")
#         elif r == "text":
#             val = self.widgets["text"].get().strip()
#             if not val: raise ValueError("Value is required")
#             commands.append(base + f"|{val}")
#         elif r == "relay":
#             val = self.widgets["relay"].get().strip()
#             if not val:
#                 raise ValueError("Select relay option")

#             # Extract numeric value from "ON (1)" or "OFF (0)"
#             relay_value = val.split("(")[-1].replace(")", "")
#             commands.append(base + f"|{relay_value}")
#         elif r == "confirm":
#             note_widget = self.widgets.get("note")
#             note = note_widget.get("1.0", tk.END).strip() if note_widget else ""
#             suffix = f"|{note}" if note else "|1"
#             commands.append(base + suffix)

#         return commands

#     def _on_send_command(self):
#         if self.sending:
#             return

#         now = time.time()
#         if now - self.last_send_time < 0.8:
#             return
#         self.last_send_time = now

#         try:
#             gwid = self._get_gwid()
#             commands = self._build_command_strings()
#         except ValueError as e:
#             messagebox.showwarning("Input Error", str(e))
#             return

#         if not commands:
#             messagebox.showwarning("Nothing to send", "Missing required parameters")
#             return

#         text = "\n".join(commands)
#         n = len(commands)
#         if not messagebox.askyesno("Confirm Send", f"Send {n} command{'s' if n>1 else ''}?\n\n{text}"):
#             return

#         self.sending = True
#         self.send_button.configure(text=" Sending... ", state="disabled")

#         threading.Thread(target=self._send_multiple, args=(gwid, commands), daemon=True).start()

#     def _on_enter_key(self, event):
#         if not self.sending:
#             self._on_send_command()
#         return "break"

#     def _send_multiple(self, gwid: str, commands: List[str]):

#         selected_node = self.node_type.get()
#         base_url = API_MAP.get(selected_node)

#         if not base_url:
#             self.root.after(0, self._log_send_result, gwid, "-", "Invalid Node Selected")
#             self.root.after(0, self._finish_sending)
#             return

#         for cmd_str in commands:
#             try:
#                 resp = requests.get(
#                     f"{base_url}?gwid={gwid}&command_info={cmd_str}",
#                     timeout=15
#                 )
#                 resp.raise_for_status()
#                 result = resp.text.strip() or "(empty)"
#             except Exception as e:
#                 result = f"ERROR: {str(e)}"

#             self.root.after(0, self._log_send_result, gwid, cmd_str, result)

#         self.root.after(0, self._finish_sending)

#     def _log_send_result(self, gwid, cmd, response):
#         self._log(f"→ {gwid} | {cmd}")
#         self._log(f" ← {response}")
#         self._log("─" * 60)

#     def _finish_sending(self):
#         self.sending = False
#         self.send_button.configure(text=" Send Command(s) ", state="normal")

#     def _copy_command(self):
#         try:
#             cmds = self._build_command_strings()
#             self.root.clipboard_clear()
#             self.root.clipboard_append("\n".join(cmds))
#             messagebox.showinfo("Copied", f"{len(cmds)} command{'s' if len(cmds)>1 else ''} copied")
#         except ValueError as e:
#             messagebox.showwarning("Cannot copy", str(e))

#     def _log(self, msg: str):
#         ts = datetime.now().strftime("%H:%M:%S")
#         self.log.insert(tk.END, f"[{ts}] {msg}\n")
#         self.log.see(tk.END)

#     def _clear_log(self):
#         self.log.delete("1.0", tk.END)


# if __name__ == "__main__":
#     root = tk.Tk()
#     app = GatewayCommandApp(root)
#     root.mainloop()


# python -m pip install tkcalendar requests
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
BASE_API_URL_NSDCU = "https://api.ms-tech.in/v17/setcommandtogateway"
BASE_API_URL_NSRT  = "https://api.ms-tech.in/v14/setcommandtogateway"
BASE_API_URL_NSGW  = "https://api.ms-tech.in/v2/setcommandtogateway"

API_MAP = {
    "NSDCU": BASE_API_URL_NSDCU,
    "NSRT":  BASE_API_URL_NSRT,
    "NSGW":  BASE_API_URL_NSGW,
}

LOG_VIEWER_MAP = {
    "NSDCU": "http://172.104.244.42/kptclcommandlogs",
    "NSRT":  "http://172.104.244.42/rdprcommandlogs",
    "NSGW":  "http://172.104.244.42/commandlogs",
}

APP_TITLE    = "KPTCL / RDPR  ·  On-Demand Command Console"
DATE_FORMAT  = "dd-mm-yyyy"
DEFAULT_METER_MAP = {
    "NSDCU": "65",
    "NSRT":  "NSRT",
    "NSGW":  "NSTG",
}

# ── Palette ────────────────────────────────────────
BG_DARK     = "#0e1117"
BG_PANEL    = "#151b27"
BG_CARD     = "#1c2336"
BG_INPUT    = "#232d42"
ACCENT      = "#3b82f6"
ACCENT_DARK = "#1d4ed8"
ACCENT_DIM  = "#1e3a5f"
SUCCESS     = "#22c55e"
WARNING     = "#f59e0b"
DANGER      = "#ef4444"
FG_PRIMARY  = "#e8eaf0"
FG_MUTED    = "#6b7280"
FG_DIM      = "#374151"
BORDER      = "#2a3448"
SEL_BG      = "#1e3a5f"
SEL_FG      = "#93c5fd"
FONT_MONO   = ("Consolas", 10)
FONT_UI     = ("Segoe UI", 10)
FONT_BOLD   = ("Segoe UI", 10, "bold")
FONT_SMALL  = ("Segoe UI", 9)
FONT_LARGE  = ("Segoe UI", 12, "bold")
FONT_TITLE  = ("Segoe UI", 11, "bold")

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
    category: str = "general"

COMMANDS_NSDCU = [
    CommandInfo( 1,  "Full Load",           "date",      category="data"),
    CommandInfo( 2,  "Block Wise",          "add_block", tooltip="Date + custom blocks", category="data"),
    CommandInfo( 3,  "Config Profile",      "option",    option_values=["IP","L","B","DL","E"], tooltip="IP,L,B,DL,E", category="config"),
    CommandInfo( 4,  "Billing",             "none",      category="data"),
    CommandInfo( 5,  "Read Scalar",         "none",      category="data"),
    CommandInfo( 6,  "Read Events",         "none",      category="data"),
    CommandInfo( 7,  "Read OBIS",           "none",      category="data"),
    CommandInfo( 8,  "Format Node",         "none",      category="system"),
    CommandInfo( 9,  "Instant Profile",     "none",      category="data"),
    CommandInfo(10,  "Select Billing",      "text",      tooltip="Enter Pakets e.g. 1_3 2_5 3_4", category="config"),
    CommandInfo(11,  "Date Load Packet",    "daily_date",category="data"),
    CommandInfo(12,  "Clear All",           "none",      category="system"),
    CommandInfo(13,  "Read Daily Load",     "daily_date",category="data"),
    CommandInfo(14,  "EC",                  "none",      category="data"),
    CommandInfo(15,  "Customized Load",     "range",     category="data"),
    CommandInfo(17,  "ESP Restart",         "none",      category="system"),
    CommandInfo(18,  "Ethernet Format",     "none",      category="config"),
    CommandInfo(19,  "Delete On Demand",    "none",      category="system"),
    CommandInfo(20,  "Set Ethernet ID",     "text",      tooltip="Enter new Ethernet ID", category="config"),
    CommandInfo(21,  "Select IP Ethernet",  "text",      tooltip="Enter IP address", category="config"),
    CommandInfo(22,  "DL Range",            "range",     category="data"),
    CommandInfo(23,  "Read All Data",       "none",      category="data"),
]

COMMANDS_NSRT = [
    CommandInfo( 0,  "Relay ON/OFF",        "relay",     option_values=["0","1"], tooltip="0=OFF | 1=ON", category="control"),
    CommandInfo( 1,  "Full Load",           "date",      category="data"),
    CommandInfo( 2,  "Block Wise",          "add_block", tooltip="Date + custom blocks", category="data"),
    CommandInfo( 4,  "Billing",             "none",      category="data"),
    CommandInfo( 5,  "Read Scalar",         "none",      category="data"),
    CommandInfo( 6,  "Read Events",         "none",      category="data"),
    CommandInfo( 7,  "Read OBIS",           "none",      category="data"),
    CommandInfo( 8,  "Format Node",         "none",      category="system"),
    CommandInfo( 9,  "Instant Profile",     "none",      category="data"),
    CommandInfo(10,  "Select Billing",      "text",      tooltip="Enter Pakets e.g. 1_3 2_5 3_4", category="config"),
    CommandInfo(11,  "Date Load Packet",    "daily_date",category="data"),
    CommandInfo(12,  "Clear All",           "none",      category="system"),
    CommandInfo(13,  "Read Daily Load",     "daily_date",category="data"),
    CommandInfo(14,  "EC",                  "none",      category="data"),
    CommandInfo(15,  "Customized Load",     "range",     category="data"),
    CommandInfo(16,  "Read Water Meter",    "none",      category="data"),
    CommandInfo(17,  "ESP Restart",         "none",      category="system"),
    CommandInfo(18,  "Delete On Demand",    "none",      category="system"),
]

COMMANDS_NSGW = [
    CommandInfo( 1,  "Full Load",           "date",      category="data"),
    CommandInfo( 2,  "Block Wise",          "add_block", tooltip="Date + custom blocks", category="data"),
    CommandInfo( 4,  "Billing",             "none",      category="data"),
    CommandInfo( 5,  "Read Scalar",         "none",      category="data"),
    CommandInfo( 6,  "Read Events",         "none",      category="data"),
    CommandInfo( 7,  "Read OBIS",           "none",      category="data"),
    CommandInfo( 8,  "Format Node",         "none",      category="system"),
    CommandInfo( 9,  "Instant Profile",     "none",      category="data"),
    CommandInfo(10,  "Select Billing",      "text",      tooltip="Enter Pakets e.g. 1_3 2_5 3_4", category="config"),
    CommandInfo(11,  "Date Load Packet",    "daily_date",category="data"),
    CommandInfo(12,  "Clear All",           "none",      category="system"),
    CommandInfo(13,  "Read Daily Load",     "daily_date",category="data"),
    CommandInfo(14,  "EC",                  "none",      category="data"),
    CommandInfo(15,  "Customized Load",     "range",     category="data"),
]

COMMAND_MAP = {
    "NSDCU": COMMANDS_NSDCU,
    "NSRT":  COMMANDS_NSRT,
    "NSGW":  COMMANDS_NSGW,
}

# ────────────────────────────────────────────────
# ToolTip
# ────────────────────────────────────────────────
class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text   = text
        self.tip    = None
        widget.bind("<Enter>", self.show)
        widget.bind("<Leave>", self.hide)

    def show(self, event=None):
        if not self.text or self.tip:
            return
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 6
        self.tip = tk.Toplevel(self.widget)
        self.tip.wm_overrideredirect(True)
        self.tip.wm_geometry(f"+{x}+{y}")
        tk.Label(
            self.tip, text=self.text,
            bg="#1e293b", fg="#93c5fd",
            font=("Segoe UI", 9),
            relief="flat", padx=8, pady=4,
            bd=1, highlightbackground=BORDER, highlightthickness=1
        ).pack()

    def hide(self, event=None):
        if self.tip:
            self.tip.destroy()
            self.tip = None

# ────────────────────────────────────────────────
# Styled Widgets
# ────────────────────────────────────────────────
def dark_entry(parent, width=22, **kwargs):
    e = tk.Entry(
        parent, width=width,
        bg=BG_INPUT, fg=FG_PRIMARY,
        insertbackground=ACCENT,
        relief="flat",
        font=FONT_UI,
        bd=0,
        highlightthickness=1,
        highlightbackground=BORDER,
        highlightcolor=ACCENT,
        **kwargs
    )
    return e

def dark_label(parent, text, font=None, fg=None, **kwargs):
    return tk.Label(
        parent, text=text,
        bg=BG_PANEL, fg=fg or FG_MUTED,
        font=font or FONT_SMALL,
        **kwargs
    )

def section_label(parent, text):
    return tk.Label(
        parent, text=text.upper(),
        bg=BG_PANEL, fg=FG_MUTED,
        font=("Segoe UI", 8, "bold"),
        letterSpacing=2 if hasattr(tk.Label, "letterSpacing") else 0
    )

def card_frame(parent, **kwargs):
    return tk.Frame(parent, bg=BG_CARD, **kwargs)

def separator(parent, horizontal=True):
    return tk.Frame(
        parent,
        bg=BORDER,
        height=1 if horizontal else None,
        width=None if horizontal else 1
    )

# ────────────────────────────────────────────────
# Main Application
# ────────────────────────────────────────────────
class GatewayCommandApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("1280x760")
        self.root.minsize(900, 600)
        self.root.configure(bg=BG_DARK)

        self.current_node   = tk.StringVar(value="NSDCU")
        self.selected_cmd: Optional[CommandInfo] = None
        self.widgets        = {}
        self.sending        = False
        self.added_blocks:  List[str] = []
        self.last_send_time = 0
        self._selected_btn  = None
        self.status_var     = tk.StringVar(value="Ready")

        self._setup_ttk_styles()
        self._build_ui()
        self._select_first_command()
        self.root.bind("<Return>", self._on_enter_key)

    # ── ttk overrides (minimal – mostly using tk widgets) ───────────
    def _setup_ttk_styles(self):
        s = ttk.Style()
        s.theme_use("clam")

        # Combobox
        s.configure("Dark.TCombobox",
            fieldbackground=BG_INPUT,
            background=BG_INPUT,
            foreground=FG_PRIMARY,
            selectbackground=SEL_BG,
            selectforeground=SEL_FG,
            bordercolor=BORDER,
            arrowcolor=FG_MUTED,
            relief="flat"
        )
        s.map("Dark.TCombobox",
            fieldbackground=[("readonly", BG_INPUT)],
            foreground=[("readonly", FG_PRIMARY)],
            selectbackground=[("readonly", SEL_BG)]
        )
        # Scrollbar
        s.configure("Dark.Vertical.TScrollbar",
            background=BG_CARD,
            troughcolor=BG_PANEL,
            bordercolor=BG_PANEL,
            arrowcolor=FG_DIM,
            relief="flat"
        )

    # ── UI Layout ────────────────────────────────────────────────────
    def _build_ui(self):
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        self._build_header()
        self._build_body()
        self._build_statusbar()

    # ── Header ───────────────────────────────────────────────────────
    def _build_header(self):
        hdr = tk.Frame(self.root, bg=BG_PANEL, height=64)
        hdr.grid(row=0, column=0, sticky="ew")
        hdr.grid_propagate(False)

        # Left – Logo / Title
        left = tk.Frame(hdr, bg=BG_PANEL)
        left.pack(side="left", padx=20, pady=12)

        # Accent bar
        tk.Frame(left, bg=ACCENT, width=4, height=36).pack(side="left", padx=(0,12))

        title_group = tk.Frame(left, bg=BG_PANEL)
        title_group.pack(side="left")
        tk.Label(title_group, text="KPTCL / RDPR",
                 bg=BG_PANEL, fg=FG_PRIMARY, font=("Segoe UI", 13, "bold")).pack(anchor="w")
        tk.Label(title_group, text="On-Demand Command Console",
                 bg=BG_PANEL, fg=FG_MUTED, font=("Segoe UI", 9)).pack(anchor="w")

        # Right – controls
        right = tk.Frame(hdr, bg=BG_PANEL)
        right.pack(side="right", padx=20, pady=10)

        # Log Viewer button
        self._make_btn(right, "📋  Log Viewer", self._open_log_viewer,
                       bg="#1e3a5f", fg=SEL_FG, hover="#2563eb").pack(side="right", padx=(8,0))

        separator(right, horizontal=False).pack(side="right", fill="y", padx=12, pady=8)

        # Meter entry
        m_frame = self._input_group(right, "")
        self.meter_label_var = tk.StringVar(value="Meter / Slave ID")
        tk.Label(m_frame, textvariable=self.meter_label_var,
                 bg=BG_PANEL, fg=FG_MUTED, font=("Segoe UI", 8)).pack(anchor="w")
        self.meter_entry = dark_entry(m_frame, width=16)
        self.meter_entry.pack(anchor="w", pady=(2,0), ipady=4, padx=(0,2))
        m_frame.pack(side="right", padx=4)

        # GW entry
        gw_frame = self._input_group(right, "")
        tk.Label(gw_frame, text="Gateway ID",
                 bg=BG_PANEL, fg=FG_MUTED, font=("Segoe UI", 8)).pack(anchor="w")
        self.gwid_entry = dark_entry(gw_frame, width=18)
        self.gwid_entry.pack(anchor="w", pady=(2,0), ipady=4)
        gw_frame.pack(side="right", padx=4)

        # Node selector
        node_frame = self._input_group(right, "")
        tk.Label(node_frame, text="Node Type",
                 bg=BG_PANEL, fg=FG_MUTED, font=("Segoe UI", 8)).pack(anchor="w")
        self.node_cb = ttk.Combobox(
            node_frame, values=["NSDCU", "NSGW", "NSRT"],
            state="readonly", width=10,
            textvariable=self.current_node,
            style="Dark.TCombobox"
        )
        self.node_cb.pack(anchor="w", pady=(2,0), ipady=3)
        self.node_cb.bind("<<ComboboxSelected>>", self._on_node_change)
        node_frame.pack(side="right", padx=4)

        self._update_meter_default()

    def _input_group(self, parent, label_text):
        f = tk.Frame(parent, bg=BG_PANEL)
        if label_text:
            tk.Label(f, text=label_text, bg=BG_PANEL, fg=FG_MUTED, font=("Segoe UI",8)).pack(anchor="w")
        return f

    def _make_btn(self, parent, text, cmd, bg=ACCENT, fg="white", hover=ACCENT_DARK, font=None):
        b = tk.Label(
            parent, text=text,
            bg=bg, fg=fg,
            font=font or ("Segoe UI", 9, "bold"),
            cursor="hand2",
            padx=12, pady=6,
            relief="flat"
        )
        b.bind("<Button-1>", lambda e: cmd())
        b.bind("<Enter>",    lambda e: b.configure(bg=hover))
        b.bind("<Leave>",    lambda e: b.configure(bg=bg))
        return b

    # ── Body ─────────────────────────────────────────────────────────
    def _build_body(self):
        body = tk.Frame(self.root, bg=BG_DARK)
        body.grid(row=1, column=0, sticky="nsew", padx=12, pady=(8,0))
        body.grid_rowconfigure(0, weight=1)
        body.grid_columnconfigure(0, weight=5)
        body.grid_columnconfigure(1, weight=3)
        body.grid_columnconfigure(2, weight=4)

        self._build_command_panel(body)
        self._build_param_panel(body)
        self._build_log_panel(body)

    # ── Command Panel ────────────────────────────────────────────────
    def _build_command_panel(self, parent):
        frame = tk.Frame(parent, bg=BG_PANEL, bd=0)
        frame.grid(row=0, column=0, sticky="nsew", padx=(0,6), pady=0)
        frame.grid_rowconfigure(1, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        # Panel header
        ph = tk.Frame(frame, bg=BG_PANEL)
        ph.grid(row=0, column=0, sticky="ew", padx=12, pady=(12,8))
        tk.Label(ph, text="COMMANDS", bg=BG_PANEL, fg=FG_MUTED,
                 font=("Segoe UI", 8, "bold")).pack(side="left")

        # Scrollable canvas
        canvas = tk.Canvas(frame, bg=BG_PANEL, highlightthickness=0, bd=0)
        sb = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview,
                           style="Dark.Vertical.TScrollbar")
        self.cmd_inner = tk.Frame(canvas, bg=BG_PANEL)
        self.cmd_inner.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0,0), window=self.cmd_inner, anchor="nw")
        canvas.configure(yscrollcommand=sb.set)
        canvas.grid(row=1, column=0, sticky="nsew", padx=(6,0), pady=(0,6))
        sb.grid(row=1, column=1, sticky="ns", pady=(0,6))
        frame.grid_columnconfigure(0, weight=1)

        canvas.bind("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
        self.cmd_inner.bind("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

        self._populate_commands(self.cmd_inner, self.current_node.get())

    def _populate_commands(self, parent, node):
        for w in parent.winfo_children():
            w.destroy()
        self._selected_btn = None

        commands = COMMAND_MAP.get(node, [])
        cols = 2
        for i in range(cols):
            parent.columnconfigure(i, weight=1)

        # Category color mapping
        cat_colors = {
            "data":    (BG_CARD, ACCENT),
            "system":  ("#2d1b1b", DANGER),
            "config":  ("#1e2a1e", SUCCESS),
            "control": ("#2a1e10", WARNING),
            "general": (BG_CARD, FG_MUTED),
        }

        r, c = 0, 0
        for cmd in commands:
            bg_norm, accent_color = cat_colors.get(cmd.category, (BG_CARD, FG_MUTED))

            btn_frame = tk.Frame(parent, bg=BG_PANEL, padx=3, pady=2)
            btn_frame.grid(row=r, column=c, sticky="ew", padx=4, pady=2)

            btn = tk.Frame(btn_frame, bg=bg_norm, cursor="hand2",
                           highlightthickness=1, highlightbackground=BORDER)
            btn.pack(fill="both", expand=True)

            # Accent left bar
            accent_bar = tk.Frame(btn, bg=accent_color, width=3)
            accent_bar.pack(side="left", fill="y")

            inner = tk.Frame(btn, bg=bg_norm, padx=8, pady=7)
            inner.pack(side="left", fill="both", expand=True)

            num_lbl = tk.Label(inner, text=f"#{cmd.number:02d}",
                               bg=bg_norm, fg=accent_color, font=("Consolas", 8))
            num_lbl.pack(anchor="w")
            name_lbl = tk.Label(inner, text=cmd.name,
                                bg=bg_norm, fg=FG_PRIMARY, font=("Segoe UI", 9, "bold"),
                                wraplength=140, justify="left")
            name_lbl.pack(anchor="w")

            # Bind click
            def make_handler(c=cmd, b=btn, bg=bg_norm):
                def on_click(e=None):
                    self._select_command(c)
                    self._highlight_btn(b, bg)
                return on_click

            handler = make_handler()
            for widget in [btn, inner, num_lbl, name_lbl, accent_bar]:
                widget.bind("<Button-1>", handler)
                widget.bind("<Enter>",
                    lambda e, b=btn, bg_n=bg_norm: b.configure(highlightbackground=ACCENT))
                widget.bind("<Leave>",
                    lambda e, b=btn, bg_n=bg_norm: self._restore_border(b))

            if cmd.tooltip:
                ToolTip(btn, cmd.tooltip)

            c += 1
            if c >= cols:
                c = 0; r += 1

    def _highlight_btn(self, btn, orig_bg):
        if self._selected_btn and self._selected_btn[0] != btn:
            old_btn, old_bg = self._selected_btn
            old_btn.configure(highlightbackground=BORDER, highlightthickness=1)
        btn.configure(highlightbackground=ACCENT, highlightthickness=2)
        self._selected_btn = (btn, orig_bg)

    def _restore_border(self, btn):
        if self._selected_btn and self._selected_btn[0] == btn:
            btn.configure(highlightbackground=ACCENT, highlightthickness=2)
        else:
            btn.configure(highlightbackground=BORDER, highlightthickness=1)

    # ── Parameter Panel ──────────────────────────────────────────────
    def _build_param_panel(self, parent):
        outer = tk.Frame(parent, bg=BG_PANEL)
        outer.grid(row=0, column=1, sticky="nsew", padx=3, pady=0)
        outer.grid_rowconfigure(1, weight=1)
        outer.grid_columnconfigure(0, weight=1)

        # Header
        ph = tk.Frame(outer, bg=BG_PANEL)
        ph.grid(row=0, column=0, sticky="ew", padx=12, pady=(12,8))
        self.param_title = tk.Label(ph, text="PARAMETERS",
                                     bg=BG_PANEL, fg=FG_MUTED, font=("Segoe UI", 8, "bold"))
        self.param_title.pack(side="left")

        # Scrollable inner
        canvas = tk.Canvas(outer, bg=BG_PANEL, highlightthickness=0, bd=0)
        sb = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview,
                           style="Dark.Vertical.TScrollbar")
        self.param_container = tk.Frame(canvas, bg=BG_PANEL, padx=12)
        self.param_container.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0,0), window=self.param_container, anchor="nw")
        canvas.configure(yscrollcommand=sb.set)
        canvas.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        sb.grid(row=1, column=1, sticky="ns")
        outer.grid_columnconfigure(0, weight=1)

        # Action buttons
        action_row = tk.Frame(outer, bg=BG_PANEL)
        action_row.grid(row=2, column=0, columnspan=2, sticky="ew", padx=12, pady=(8,12))

        self._make_btn(
            action_row, "Copy", self._copy_command,
            bg=BG_CARD, fg=FG_MUTED, hover=BG_INPUT,
            font=("Segoe UI", 9)
        ).pack(side="left")

        self.send_btn_label = tk.StringVar(value="  ▶  Send Command")
        self.send_btn = tk.Label(
            action_row,
            textvariable=self.send_btn_label,
            bg=ACCENT, fg="white",
            font=("Segoe UI", 10, "bold"),
            cursor="hand2",
            padx=16, pady=8,
            relief="flat"
        )
        self.send_btn.pack(side="right")
        self.send_btn.bind("<Button-1>", lambda e: self._on_send_command())
        self.send_btn.bind("<Enter>", lambda e: self.send_btn.configure(bg=ACCENT_DARK))
        self.send_btn.bind("<Leave>", lambda e: self.send_btn.configure(
            bg=ACCENT if not self.sending else "#475569"))

    def _param_label(self, text):
        tk.Label(
            self.param_container, text=text.upper(),
            bg=BG_PANEL, fg=FG_MUTED,
            font=("Segoe UI", 8, "bold")
        ).pack(anchor="w", pady=(14,4))

    def _param_entry(self, key, placeholder=""):
        e = dark_entry(self.param_container, width=28)
        e.pack(anchor="w", ipady=5)
        self.widgets[key] = e
        return e

    def _build_date_picker(self, label_text="Date", key="date"):
        self._param_label(label_text)
        de = DateEntry(
            self.param_container,
            date_pattern=DATE_FORMAT,
            width=14,
            year=2026, month=1, day=1,
            background=BG_INPUT,
            foreground=FG_PRIMARY,
            bordercolor=BORDER,
            headersbackground=ACCENT_DARK,
            headersforeground="white",
            selectbackground=ACCENT,
            normalbackground=BG_CARD,
            normalforeground=FG_PRIMARY,
            othermonthforeground=FG_DIM,
            othermonthbackground=BG_PANEL,
            weekendforeground=SEL_FG,
            weekendbackground=BG_CARD,
        )
        de.pack(anchor="w", ipady=4)
        self.widgets[key] = de

    def _build_time_picker(self, label_text="Time", key="time"):
        self._param_label(label_text)
        f = tk.Frame(self.param_container, bg=BG_PANEL)
        f.pack(anchor="w")
        h = ttk.Combobox(f, values=[f"{i:02d}" for i in range(24)],
                         width=5, state="readonly", style="Dark.TCombobox")
        h.current(0); h.pack(side="left")
        tk.Label(f, text=" : ", bg=BG_PANEL, fg=FG_MUTED, font=FONT_UI).pack(side="left")
        m = ttk.Combobox(f, values=[f"{i:02d}" for i in range(60)],
                         width=5, state="readonly", style="Dark.TCombobox")
        m.current(0); m.pack(side="left")
        self.widgets[key] = (h, m)

    def _build_range_input_ui(self):
        tk.Label(self.param_container, text="Load Profile Range",
                 bg=BG_PANEL, fg=FG_PRIMARY, font=FONT_BOLD).pack(anchor="w", pady=(8,2))
        tk.Frame(self.param_container, bg=ACCENT, height=2).pack(fill="x", pady=(0,10))
        self._build_date_picker("Start Date", "start_date")
        self._build_time_picker("Start Time", "start_time")
        tk.Frame(self.param_container, bg=BORDER, height=1).pack(fill="x", pady=14)
        self._build_date_picker("End Date", "end_date")
        self._build_time_picker("End Time", "end_time")
        tk.Label(self.param_container,
                 text="Format:  HHMM DDMMYYYY _ HHMM DDMMYYYY",
                 bg=BG_PANEL, fg=FG_DIM, font=("Consolas", 8)
                 ).pack(anchor="w", pady=(12,0))

    def _build_block_input_ui(self):
        self._build_date_picker("Reference Date")
        self._param_label("Block Suffix")
        f = tk.Frame(self.param_container, bg=BG_PANEL)
        f.pack(anchor="w", fill="x")
        self.block_entry = dark_entry(f, width=20)
        self.block_entry.pack(side="left", ipady=4, padx=(0,6))
        self.block_entry.focus_set()
        self._make_btn(f, "+ Add", self._add_custom_block,
                       bg=ACCENT_DIM, fg=SEL_FG, hover=ACCENT).pack(side="left")

        # Block list
        list_frame = tk.Frame(self.param_container, bg=BORDER, padx=1, pady=1)
        list_frame.pack(fill="x", pady=(10,4))
        self.block_listbox = tk.Listbox(
            list_frame, height=4,
            bg=BG_INPUT, fg=FG_PRIMARY,
            font=FONT_MONO,
            selectbackground=ACCENT_DARK,
            selectforeground="white",
            bd=0, relief="flat",
            activestyle="none"
        )
        self.block_listbox.pack(fill="x")

        self._make_btn(self.param_container, "Clear All", self._clear_blocks,
                       bg="#2d1b1b", fg="#ef4444", hover="#3d2020",
                       font=("Segoe UI", 8)).pack(anchor="w", pady=(4,0))

        tk.Label(self.param_container,
                 text="ℹ  One command sent per block",
                 bg=BG_PANEL, fg=FG_MUTED, font=("Segoe UI", 8)).pack(anchor="w", pady=(10,0))

    def _build_text_input(self, label_text):
        self._param_label(label_text)
        e = dark_entry(self.param_container, width=28)
        e.pack(anchor="w", ipady=5)
        self.widgets["text"] = e

    def _build_option_selector(self, values):
        self._param_label("Select Option")
        cb = ttk.Combobox(
            self.param_container, values=values,
            state="readonly", width=22,
            style="Dark.TCombobox"
        )
        cb.current(0); cb.pack(anchor="w", ipady=3)
        self.widgets["option"] = cb

    def _build_relay_selector(self, values):
        self._param_label("Relay Control")
        cb = ttk.Combobox(
            self.param_container, values=["ON  (1)", "OFF (0)"],
            state="readonly", width=18,
            style="Dark.TCombobox"
        )
        cb.current(1); cb.pack(anchor="w", ipady=3)
        self.widgets["relay"] = cb

        tk.Label(self.param_container,
                 text="⚠  Verify relay state before sending",
                 bg=BG_PANEL, fg=WARNING, font=("Segoe UI", 8)).pack(anchor="w", pady=(10,0))

    # ── Log Panel ─────────────────────────────────────────────────────
    def _build_log_panel(self, parent):
        frame = tk.Frame(parent, bg=BG_PANEL)
        frame.grid(row=0, column=2, sticky="nsew", padx=(6,0), pady=0)
        frame.grid_rowconfigure(1, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        # Header
        ph = tk.Frame(frame, bg=BG_PANEL)
        ph.grid(row=0, column=0, sticky="ew", padx=12, pady=(12,8))
        tk.Label(ph, text="ACTIVITY LOG", bg=BG_PANEL, fg=FG_MUTED,
                 font=("Segoe UI", 8, "bold")).pack(side="left")
        self._make_btn(ph, "Clear", self._clear_log,
                       bg=BG_CARD, fg=FG_MUTED, hover=BG_INPUT,
                       font=("Segoe UI", 8)).pack(side="right")

        # Log text area
        log_outer = tk.Frame(frame, bg=BORDER, padx=1, pady=1)
        log_outer.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0,12))
        log_outer.grid_rowconfigure(0, weight=1)
        log_outer.grid_columnconfigure(0, weight=1)

        self.log = scrolledtext.ScrolledText(
            log_outer,
            bg="#080c14", fg="#94a3b8",
            font=("Consolas", 9),
            insertbackground=ACCENT,
            relief="flat", bd=0,
            selectbackground=ACCENT_DARK,
            wrap="word"
        )
        self.log.grid(row=0, column=0, sticky="nsew")

        # Tag colours
        self.log.tag_configure("ts",       foreground="#334155")
        self.log.tag_configure("outgoing", foreground="#60a5fa")
        self.log.tag_configure("response", foreground="#34d399")
        self.log.tag_configure("error",    foreground="#f87171")
        self.log.tag_configure("divider",  foreground="#1e293b")

        self._log("Console ready. Select a node, enter Gateway/Meter IDs, choose a command.", tag="response")

    # ── Status Bar ───────────────────────────────────────────────────
    def _build_statusbar(self):
        bar = tk.Frame(self.root, bg=BG_DARK, height=28)
        bar.grid(row=2, column=0, sticky="ew")

        self.status_indicator = tk.Frame(bar, bg=SUCCESS, width=8, height=8)
        self.status_indicator.pack(side="left", padx=(16,6), pady=10)

        tk.Label(bar, textvariable=self.status_var,
                 bg=BG_DARK, fg=FG_MUTED, font=("Segoe UI", 8)).pack(side="left")

        tk.Label(bar, text=f"  Node:  ",
                 bg=BG_DARK, fg=FG_DIM, font=("Segoe UI", 8)).pack(side="right", padx=(0,4))
        self.node_status_lbl = tk.Label(bar, textvariable=self.current_node,
                 bg=BG_DARK, fg=SEL_FG, font=("Segoe UI", 8, "bold"))
        self.node_status_lbl.pack(side="right")

        now = datetime.now().strftime("%d %b %Y  %H:%M")
        tk.Label(bar, text=now,
                 bg=BG_DARK, fg=FG_DIM, font=("Segoe UI", 8)).pack(side="right", padx=16)

    # ── Event Handlers ────────────────────────────────────────────────
    def _on_node_change(self, event=None):
        self._update_meter_default()
        self._populate_commands(self.cmd_inner, self.current_node.get())
        self._select_first_command()
        self._set_status(f"Switched to {self.current_node.get()}")

    def _update_meter_default(self, event=None):
        node = self.current_node.get()
        self.meter_label_var.set("Meter / Slave ID" if node == "NSDCU" else "Node ID")
        if node in DEFAULT_METER_MAP:
            self.meter_entry.delete(0, tk.END)
            self.meter_entry.insert(0, DEFAULT_METER_MAP[node])

    def _select_first_command(self):
        cmds = COMMAND_MAP.get(self.current_node.get(), [])
        if cmds:
            self._select_command(cmds[0])

    def _select_command(self, cmd: CommandInfo):
        self.selected_cmd = cmd
        self.param_title.configure(text=f"PARAMETERS  ·  {cmd.name.upper()}  [CMD {cmd.number:02d}]")

        for w in self.param_container.winfo_children():
            w.destroy()
        self.widgets.clear()
        self.added_blocks.clear()

        # Command info card
        cat_cols = {
            "data":    (ACCENT,   "#1e3a5f"),
            "system":  (DANGER,   "#2d1b1b"),
            "config":  (SUCCESS,  "#1b2d1e"),
            "control": (WARNING,  "#2d2010"),
            "general": (FG_MUTED, BG_CARD),
        }
        fg_c, bg_c = cat_cols.get(cmd.category, (FG_MUTED, BG_CARD))
        info = tk.Frame(self.param_container, bg=bg_c,
                        highlightthickness=1, highlightbackground=fg_c)
        info.pack(fill="x", pady=(8,4))
        tk.Frame(info, bg=fg_c, width=4).pack(side="left", fill="y")
        ic = tk.Frame(info, bg=bg_c, padx=10, pady=8)
        ic.pack(side="left", fill="both")
        tk.Label(ic, text=f"#{cmd.number:02d}  {cmd.name}", bg=bg_c, fg=fg_c,
                 font=("Segoe UI", 11, "bold")).pack(anchor="w")
        if cmd.tooltip:
            tk.Label(ic, text=cmd.tooltip, bg=bg_c, fg=FG_MUTED,
                     font=("Segoe UI", 8)).pack(anchor="w")
        tk.Label(ic, text=f"Category: {cmd.category.upper()}", bg=bg_c, fg=FG_DIM,
                 font=("Segoe UI", 8)).pack(anchor="w")

        # Build parameter widgets
        r = cmd.requires
        if r == "none":
            tk.Label(self.param_container, text="No parameters required",
                     bg=BG_PANEL, fg=FG_MUTED, font=("Segoe UI", 9)).pack(pady=20)
            tk.Label(self.param_container,
                     text="Click  ▶ Send Command  to execute.",
                     bg=BG_PANEL, fg=FG_DIM, font=("Segoe UI", 8)).pack()
        elif r == "date":
            self._build_date_picker("Reference Date")
        elif r == "daily_date":
            self._build_date_picker("Select Date")
        elif r == "add_block":
            self._build_block_input_ui()
        elif r == "range":
            self._build_range_input_ui()
        elif r == "option" and cmd.option_values:
            self._build_option_selector(cmd.option_values)
        elif r == "relay":
            self._build_relay_selector(cmd.option_values)
        elif r == "text":
            self._build_text_input(cmd.tooltip or "Value")

    # ── Command Building ─────────────────────────────────────────────
    def _get_gwid(self) -> str:
        raw = self.gwid_entry.get().strip()
        if not raw:
            raise ValueError("Gateway ID is required.")
        return f"{self.current_node.get()}{raw}"

    def _get_meter_number(self) -> str:
        val = self.meter_entry.get().strip()
        if not val:
            raise ValueError("Meter number / Node ID is required.")
        return val

    def _format_datetime_range(self) -> str:
        def get_dt(kd, kt):
            d = self.widgets[kd].get_date()
            h, m = self.widgets[kt]
            return f"{int(h.get()):02d}{int(m.get()):02d}{d.day:02d}{d.month:02d}{d.year:04d}"
        return f"{get_dt('start_date','start_time')}_{get_dt('end_date','end_time')}"

    def _format_daily_date(self) -> str:
        d = self.widgets["date"].get_date()
        return f"{d.day:02d}{d.month:02d}{d.year:04d}"

    def _build_command_strings(self) -> List[str]:
        if not self.selected_cmd:
            raise ValueError("No command selected.")
        meter   = self._get_meter_number()
        cmd     = self.selected_cmd
        base    = f"N|{meter}|{cmd.number}"
        commands = []
        r = cmd.requires

        if r == "none":
            commands.append(base + "|1")
        elif r == "date":
            d = self.widgets["date"].get()
            if not d: raise ValueError("Date is required.")
            commands.append(f"{base}|{d}")
        elif r == "daily_date":
            commands.append(f"{base}|{self._format_daily_date()}")
        elif r == "add_block":
            d = self.widgets["date"].get()
            if not d: raise ValueError("Date is required.")
            if not self.added_blocks: raise ValueError("Add at least one block.")
            for blk in self.added_blocks:
                commands.append(f"{base}|{d}{blk}")
        elif r == "option":
            val = self.widgets["option"].get().strip()
            if not val: raise ValueError("Select an option.")
            commands.append(f"{base}|{val}")
        elif r == "range":
            commands.append(f"{base}|{self._format_datetime_range()}")
        elif r == "text":
            val = self.widgets["text"].get().strip()
            if not val: raise ValueError("Value is required.")
            commands.append(f"{base}|{val}")
        elif r == "relay":
            val = self.widgets["relay"].get()
            if not val: raise ValueError("Select relay state.")
            relay_val = val.split("(")[-1].replace(")", "").strip()
            commands.append(f"{base}|{relay_val}")

        return commands

    # ── Send ─────────────────────────────────────────────────────────
    def _on_send_command(self):
        if self.sending:
            return
        if time.time() - self.last_send_time < 0.8:
            return
        self.last_send_time = time.time()

        try:
            gwid     = self._get_gwid()
            commands = self._build_command_strings()
        except ValueError as e:
            self._show_error("Input Error", str(e))
            return

        n    = len(commands)
        text = "\n".join(commands)
        if not messagebox.askyesno(
            "Confirm Send",
            f"Send {n} command{'s' if n>1 else ''} to {gwid}?\n\n{text}",
            parent=self.root
        ):
            return

        self.sending = True
        self.send_btn.configure(bg="#475569", cursor="")
        self.send_btn_label.set("  ⏳  Sending…")
        self._set_status(f"Sending {n} command(s) to {gwid}…", "warning")
        threading.Thread(target=self._send_multiple, args=(gwid, commands), daemon=True).start()

    def _on_enter_key(self, event):
        if not self.sending:
            self._on_send_command()
        return "break"

    def _send_multiple(self, gwid, commands):
        node     = self.current_node.get()
        base_url = API_MAP.get(node)
        if not base_url:
            self.root.after(0, self._log, "ERROR: Invalid node selected.", "error")
            self.root.after(0, self._finish_sending)
            return

        for cmd_str in commands:
            self.root.after(0, self._log, f"→  {gwid}  ·  {cmd_str}", "outgoing")
            try:
                resp = requests.get(
                    f"{base_url}?gwid={gwid}&command_info={cmd_str}",
                    timeout=15
                )
                resp.raise_for_status()
                result = resp.text.strip() or "(empty response)"
                self.root.after(0, self._log, f"←  {result}", "response")
            except Exception as e:
                self.root.after(0, self._log, f"✗  ERROR: {e}", "error")
            self.root.after(0, self._log, "─" * 52, "divider")

        self.root.after(0, self._finish_sending)

    def _finish_sending(self):
        self.sending = False
        self.send_btn.configure(bg=ACCENT, cursor="hand2")
        self.send_btn_label.set("  ▶  Send Command")
        self._set_status("Ready")

    def _copy_command(self):
        try:
            cmds = self._build_command_strings()
            self.root.clipboard_clear()
            self.root.clipboard_append("\n".join(cmds))
            self._set_status(f"Copied {len(cmds)} command(s) to clipboard.")
        except ValueError as e:
            self._show_error("Cannot Copy", str(e))

    def _add_custom_block(self):
        blk = self.block_entry.get().strip()
        if not blk:
            self._show_error("Empty Block", "Enter a block value first.")
            return
        if blk in self.added_blocks:
            self._show_error("Duplicate", f"Block '{blk}' already added.")
            return
        self.added_blocks.append(blk)
        self.block_listbox.insert(tk.END, f"  →  {blk}")
        self.block_entry.delete(0, tk.END)
        self.block_entry.focus_set()

    def _clear_blocks(self):
        self.added_blocks.clear()
        self.block_listbox.delete(0, tk.END)

    def _open_log_viewer(self):
        url = LOG_VIEWER_MAP.get(self.current_node.get())
        if url:
            webbrowser.open(url)

    # ── Logging / Status ─────────────────────────────────────────────
    def _log(self, msg: str, tag: str = ""):
        ts = datetime.now().strftime("%H:%M:%S")
        self.log.insert(tk.END, f"[{ts}] ", "ts")
        self.log.insert(tk.END, f"{msg}\n", tag or "")
        self.log.see(tk.END)

    def _clear_log(self):
        self.log.delete("1.0", tk.END)
        self._log("Log cleared.", "response")

    def _set_status(self, msg, level="normal"):
        self.status_var.set(msg)
        colors = {"normal": SUCCESS, "warning": WARNING, "error": DANGER}
        self.status_indicator.configure(bg=colors.get(level, SUCCESS))

    def _show_error(self, title, msg):
        messagebox.showwarning(title, msg, parent=self.root)


# ────────────────────────────────────────────────
if __name__ == "__main__":
    root = tk.Tk()
    app  = GatewayCommandApp(root)
    root.mainloop()
