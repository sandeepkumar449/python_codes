import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import serial
import serial.tools.list_ports
import threading
import queue
import csv
from datetime import datetime
import re
import json
import os

class SerialMonitor(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Advanced Serial Monitor")
        self.geometry("1000x750")
        self.minsize(800, 600)
        
        # Theme + styling
        self.style = ttk.Style()
        try:
            self.style.theme_use("clam")
        except Exception:
            pass  # fall back to default theme

        # Light palette (best-effort across platforms/themes)
        self.colors = {
            "bg": "#f4f5f7",
            "panel": "#ffffff",
            "fg": "#1f2328",
            "muted": "#6a737d",
            "accent": "#4a7abc",
            "accent2": "#4a9cf9",
            "danger": "#ff5555",
            "border": "#d0d7de",
        }
        self.configure(bg=self.colors["bg"])
        
        # Variables
        self.ser = None
        self.stop_thread = False
        self.connected = False
        self.received_bytes = 0
        self.sent_bytes = 0
        self.line_endings = {"None": "", "LF (\\n)": "\n", "CR (\\r)": "\r", "CR+LF (\\r\\n)": "\r\n"}
        self.current_line_ending = "\n"

        # Thread-safe RX path (Tkinter must be updated on main thread)
        self.rx_queue = queue.Queue()
        self.paused = False
        self.dropped_while_paused = 0
        self.max_pause_buffer = 1024 * 1024  # 1MB
        self.hex_offset = 0
        self.ascii_at_line_start = True
        self.hex_at_line_start = True
        self.dec_at_line_start = True
        self.bin_at_line_start = True

        # Logging
        self.log_file_path = None
        self.log_fp = None
        self.history_file_path = None
        self.state_file_path = os.path.join(os.path.dirname(__file__), ".serial_monitor_state.json")
        self.auto_send_running = False
        self.auto_send_after_id = None
        self.auto_send_index = 0
        
        # Setup the UI
        self.apply_styles()
        self.create_menu()
        self.setup_ui()
        self.load_app_state()
        self.auto_load_last_history()

        # Auto-refresh ports on startup (same as clicking Refresh)
        self.after(0, self.refresh_ports)
        
        # Start periodic port check
        self.after(1000, self.check_ports)

        # Start periodic RX processing (main-thread safe)
        self.after(50, self.process_rx_queue)

        # Helpful shortcuts
        self.bind_all("<Control-l>", lambda e: self.clear_output())
        self.bind_all("<Control-L>", lambda e: self.clear_output())
        self.bind_all("<Escape>", lambda e: self.entry_box.focus_set())
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def apply_styles(self):
        c = self.colors
        s = self.style



        

        


        s.configure(".", background=c["bg"], foreground=c["fg"])
        s.configure("TFrame", background=c["bg"])
        s.configure("TLabel", background=c["bg"], foreground=c["fg"])
        s.configure("TCheckbutton", background=c["bg"], foreground=c["fg"])

        # s.configure("TLabelframe", background=c["bg"], foreground=c["fg"], bordercolor=c["border"])
        # s.configure("TLabelframe.Label", background=c["bg"], foreground=c["fg"])

        s.configure("TLabelframe", background=c["panel"], foreground=c["fg"], bordercolor=c["border"])
        s.configure("TLabelframe.Label", background=c["panel"], foreground=c["accent2"])

        # s.configure("TButton", padding=(10, 6))
        # s.map("TButton",
        #       foreground=[("disabled", c["muted"])],
        #       background=[("active", c["panel"])])

        s.configure("TButton", padding=(10, 6), borderwidth=0)
        s.map("TButton", foreground=[("disabled", "#a0a7b4")])

        # Command area button styles
        s.configure(
            "CmdPrimary.TButton",
            background="#1f6feb",
            foreground="white",
            padding=(14, 8),
            font=("Calibri", 10, "bold"),
        )
        s.map(
            "CmdPrimary.TButton",
            background=[("active", "#388bfd"), ("pressed", "#1158c7"), ("disabled", "#9db9f2")],
            foreground=[("disabled", "#e9eef8"), ("!disabled", "white")],
        )

        s.configure(
            "CmdPause.TButton",
            background="#6f42c1",
            foreground="white",
            padding=(12, 8),
            font=("Calibri", 10, "bold"),
        )
        s.map(
            "CmdPause.TButton",
            background=[("active", "#8258d1"), ("pressed", "#5a32a3"), ("disabled", "#c6b5e8")],
            foreground=[("disabled", "#f0ebfa"), ("!disabled", "white")],
        )

        s.configure(
            "CmdLog.TButton",
            background="#0a7d57",
            foreground="white",
            padding=(12, 8),
            font=("Calibri", 10, "bold"),
        )
        s.map(
            "CmdLog.TButton",
            background=[("active", "#109468"), ("pressed", "#086746"), ("disabled", "#a9d8c7")],
            foreground=[("disabled", "#ebf7f2"), ("!disabled", "white")],
        )

        s.configure(
            "CmdAutoStart.TButton",
            background="#2563eb",
            foreground="white",
            padding=(10, 8),
            font=("Calibri", 10, "bold"),
        )
        s.map(
            "CmdAutoStart.TButton",
            background=[("active", "#3b82f6"), ("pressed", "#1d4ed8"), ("disabled", "#b3cbf8")],
            foreground=[("disabled", "#eff6ff"), ("!disabled", "white")],
        )

        s.configure(
            "CmdAutoStop.TButton",
            background="#dc2626",
            foreground="white",
            padding=(10, 8),
            font=("Calibri", 10, "bold"),
        )
        s.map(
            "CmdAutoStop.TButton",
            background=[("active", "#ef4444"), ("pressed", "#b91c1c"), ("disabled", "#f3b4b4")],
            foreground=[("disabled", "#fef2f2"), ("!disabled", "white")],
        )

        # Top communication bar button styles
        s.configure("TopRefresh.TButton", background="#b7791f", foreground="white", padding=(10, 6), font=("Calibri", 10, "bold"))
        s.map(
            "TopRefresh.TButton",
            background=[("active", "#c98a2c"), ("pressed", "#9a6417"), ("disabled", "#e2c79a")],
            foreground=[("disabled", "#fffaf0"), ("!disabled", "white")],
        )

        s.configure("TopConnect.TButton", background="#1f9d55", foreground="white", padding=(10, 6), font=("Calibri", 10, "bold"))
        s.map(
            "TopConnect.TButton",
            background=[("active", "#24b963"), ("pressed", "#177a41"), ("disabled", "#9fd9b9")],
            foreground=[("disabled", "#f0fff4"), ("!disabled", "white")],
        )

        s.configure("TopDisconnect.TButton", background="#c53030", foreground="white", padding=(10, 6), font=("Calibri", 10, "bold"))
        s.map(
            "TopDisconnect.TButton",
            background=[("active", "#dd4040"), ("pressed", "#9f2525"), ("disabled", "#e7a3a3")],
            foreground=[("disabled", "#fff5f5"), ("!disabled", "white")],
        )

        # History action button styles
        s.configure("HistLoad.TButton", background="#2563eb", foreground="white", padding=(9, 5), font=("Calibri", 10, "bold"))
        s.map(
            "HistLoad.TButton",
            background=[("active", "#3b7bf0"), ("pressed", "#1e4fb8"), ("disabled", "#a9c3f5")],
            foreground=[("disabled", "#eff6ff"), ("!disabled", "white")],
        )

        s.configure("HistSave.TButton", background="#0f9d58", foreground="white", padding=(9, 5), font=("Calibri", 10, "bold"))
        s.map(
            "HistSave.TButton",
            background=[("active", "#18b767"), ("pressed", "#0c7b45"), ("disabled", "#9fd8b9")],
            foreground=[("disabled", "#f0fff4"), ("!disabled", "white")],
        )

        s.configure("HistSaveAs.TButton", background="#0284c7", foreground="white", padding=(9, 5), font=("Calibri", 10, "bold"))
        s.map(
            "HistSaveAs.TButton",
            background=[("active", "#0ea5e9"), ("pressed", "#0369a1"), ("disabled", "#9fd7ef")],
            foreground=[("disabled", "#f0f9ff"), ("!disabled", "white")],
        )

        s.configure("HistClear.TButton", background="#d97706", foreground="white", padding=(9, 5), font=("Calibri", 10, "bold"))
        s.map(
            "HistClear.TButton",
            background=[("active", "#e68a12"), ("pressed", "#b76305"), ("disabled", "#ebc998")],
            foreground=[("disabled", "#fffaf0"), ("!disabled", "white")],
        )

        s.configure("HistEdit.TButton", background="#7c3aed", foreground="white", padding=(9, 5), font=("Calibri", 10, "bold"))
        s.map(
            "HistEdit.TButton",
            background=[("active", "#8b5cf6"), ("pressed", "#6526c7"), ("disabled", "#d2bef8")],
            foreground=[("disabled", "#f5f3ff"), ("!disabled", "white")],
        )

        s.configure("HistMove.TButton", background="#374151", foreground="white", padding=(9, 5), font=("Calibri", 10, "bold"))
        s.map(
            "HistMove.TButton",
            background=[("active", "#4b5563"), ("pressed", "#1f2937"), ("disabled", "#c7ccd4")],
            foreground=[("disabled", "#f3f4f6"), ("!disabled", "white")],
        )

        s.configure("ClearOutput.TButton", background="#c53030", foreground="white", padding=(10, 6), font=("Calibri", 10, "bold"))
        s.map(
            "ClearOutput.TButton",
            background=[("active", "#dd4040"), ("pressed", "#9f2525"), ("disabled", "#e7a3a3")],
            foreground=[("disabled", "#fff5f5"), ("!disabled", "white")],
        )

        s.configure("TCombobox", padding=(6, 4))
        s.configure("TEntry", padding=(6, 4))

    def create_menu(self):
        menubar = tk.Menu(self)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Start/Stop Log...", command=self.toggle_logging, accelerator="Ctrl+Shift+L")
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.destroy, accelerator="Alt+F4")
        menubar.add_cascade(label="File", menu=file_menu)

        edit_menu = tk.Menu(menubar, tearoff=0)
        edit_menu.add_command(label="Clear Output", command=self.clear_output, accelerator="Ctrl+L")
        edit_menu.add_command(label="Clear History", command=self.clear_history)
        menubar.add_cascade(label="Edit", menu=edit_menu)

        view_menu = tk.Menu(menubar, tearoff=0)
        view_menu.add_command(label="Pause/Resume", command=self.toggle_pause, accelerator="Ctrl+P")
        menubar.add_cascade(label="View", menu=view_menu)

        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="About", command=self.show_about)
        menubar.add_cascade(label="Help", menu=help_menu)

        self.config(menu=menubar)
        self.bind_all("<Control-P>", lambda e: self.toggle_pause())
        self.bind_all("<Control-p>", lambda e: self.toggle_pause())
        self.bind_all("<Control-Shift-L>", lambda e: self.toggle_logging())
        self.bind_all("<Control-Shift-l>", lambda e: self.toggle_logging())

    def show_about(self):
        messagebox.showinfo(
            "About",
            "Advanced Serial Monitor\n\n"
            "Features: port scan, send history, timestamps, pause, and logging.\n"
            "Built with Tkinter + pySerial."
        )
        
    def setup_ui(self):
        # Top communication/settings strip (Docklight-like)
        top_strip = ttk.Frame(self)
        top_strip.pack(fill=tk.X, padx=5, pady=(5, 2))

        top_strip.columnconfigure(0, weight=1)

        self.info_label = ttk.Label(top_strip, text="Ready", foreground="#6a737d")
        self.info_label.grid(row=0, column=0, sticky="w")

        comm_frame = ttk.Frame(top_strip)
        comm_frame.grid(row=0, column=1, sticky="e")

        ttk.Label(comm_frame, text="COM:").pack(side=tk.LEFT, padx=(0, 4))
        self.port_combo = ttk.Combobox(comm_frame, values=self.get_ports(), width=10, state="readonly")
        self.port_combo.pack(side=tk.LEFT, padx=(0, 6))

        ttk.Label(comm_frame, text="Baud:").pack(side=tk.LEFT, padx=(0, 4))
        self.baud_combo = ttk.Combobox(
            comm_frame,
            values=["9600", "19200", "38400", "57600", "115200", "230400", "460800", "921600"],
            width=8,
            state="readonly",
        )
        self.baud_combo.set("115200")
        self.baud_combo.pack(side=tk.LEFT, padx=(0, 6))
        self.baud_combo.bind("<<ComboboxSelected>>", self.on_baud_change)

        ttk.Label(comm_frame, text="Data:").pack(side=tk.LEFT, padx=(0, 4))
        self.databits_combo = ttk.Combobox(comm_frame, values=["5", "6", "7", "8"], width=4, state="readonly")
        self.databits_combo.set("8")
        self.databits_combo.pack(side=tk.LEFT, padx=(0, 6))

        ttk.Label(comm_frame, text="Parity:").pack(side=tk.LEFT, padx=(0, 4))
        self.parity_combo = ttk.Combobox(comm_frame, values=["None", "Even", "Odd", "Mark", "Space"], width=6, state="readonly")
        self.parity_combo.set("None")
        self.parity_combo.pack(side=tk.LEFT, padx=(0, 6))

        ttk.Label(comm_frame, text="Stop:").pack(side=tk.LEFT, padx=(0, 4))
        self.stopbits_combo = ttk.Combobox(comm_frame, values=["1", "1.5", "2"], width=4, state="readonly")
        self.stopbits_combo.set("1")
        self.stopbits_combo.pack(side=tk.LEFT, padx=(0, 6))

        ttk.Label(comm_frame, text="End:").pack(side=tk.LEFT, padx=(0, 4))
        self.line_ending_combo = ttk.Combobox(comm_frame, values=list(self.line_endings.keys()), width=8, state="readonly")
        self.line_ending_combo.set("LF (\\n)")
        self.line_ending_combo.pack(side=tk.LEFT, padx=(0, 6))
        self.line_ending_combo.bind("<<ComboboxSelected>>", self.on_line_ending_change)

        self.refresh_btn = ttk.Button(comm_frame, text="Refresh", command=self.refresh_ports, width=8, style="TopRefresh.TButton")
        self.refresh_btn.pack(side=tk.LEFT, padx=(0, 6))
        self.connect_btn = ttk.Button(comm_frame, text="Connect", command=self.connect_serial, width=9, style="TopConnect.TButton")
        self.connect_btn.pack(side=tk.LEFT, padx=(0, 6))
        self.disconnect_btn = ttk.Button(
            comm_frame, text="Disconnect", command=self.disconnect_serial, state="disabled", width=10, style="TopDisconnect.TButton"
        )
        self.disconnect_btn.pack(side=tk.LEFT)

        # Create main paned window for resizable panels
        main_pane = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True, padx=5, pady=(2, 5))
        
        # Left panel for controls and history
        left_frame = ttk.Frame(main_pane)
        main_pane.add(left_frame, weight=1)
        
        # Right panel for terminal
        right_frame = ttk.Frame(main_pane)
        main_pane.add(right_frame, weight=3)
        
        # Setup left panel content
        self.setup_left_panel(left_frame)
        
        # Setup right panel content
        self.setup_right_panel(right_frame)
        
        # Setup status bar
        self.setup_status_bar()

        # Initialize bottom bar fields from current UI selections
        self.update_baud_status()
        
    def setup_left_panel(self, parent):
        # Command/Send area (left panel, full height)
        send_seq_frame = ttk.LabelFrame(parent, text="Send Sequences", padding=8)
        send_seq_frame.pack(fill=tk.BOTH, expand=True)
        
        self.timestamp_var = tk.BooleanVar()
        options_frame = ttk.Frame(send_seq_frame)
        options_frame.pack(fill=tk.X, pady=(0, 6))

        self.timestamp_chk = ttk.Checkbutton(options_frame, text="Timestamps", variable=self.timestamp_var)
        self.timestamp_chk.pack(side=tk.LEFT, padx=(0, 10))
        
        self.autoscroll_var = tk.BooleanVar(value=True)
        self.autoscroll_chk = ttk.Checkbutton(options_frame, text="Auto-scroll", variable=self.autoscroll_var)
        self.autoscroll_chk.pack(side=tk.LEFT)

        self.echo_sent_var = tk.BooleanVar(value=True)
        self.echo_sent_chk = ttk.Checkbutton(options_frame, text="Show Sent", variable=self.echo_sent_var)
        self.echo_sent_chk.pack(side=tk.LEFT, padx=(10, 0))
        
        # Command area
        cmd_frame = ttk.Frame(send_seq_frame)
        cmd_frame.pack(fill=tk.X, pady=(0, 8))

        # Professional layout: one input row + one button row
        cmd_frame.columnconfigure(1, weight=1)

        ttk.Label(cmd_frame, text="Mode:").grid(row=0, column=0, sticky=tk.W, padx=(0, 8), pady=(0, 6))
        mode_inner = ttk.Frame(cmd_frame)
        mode_inner.grid(row=0, column=1, sticky="w", pady=(0, 6))

        self.send_mode = tk.StringVar(value="ascii")
        ttk.Radiobutton(mode_inner, text="ASCII", value="ascii", variable=self.send_mode).pack(side=tk.LEFT)
        ttk.Radiobutton(mode_inner, text="HEX", value="hex", variable=self.send_mode).pack(side=tk.LEFT, padx=(12, 0))
        self._last_send_mode = self.send_mode.get()
        self.send_mode.trace_add("write", self.on_send_mode_change)

        ttk.Label(cmd_frame, text="Input:").grid(row=1, column=0, sticky=tk.W, padx=(0, 8), pady=(0, 6))
        self.entry_box = ttk.Entry(cmd_frame, font=("Calibri", 11))
        self.entry_box.grid(row=1, column=1, sticky="ew", pady=(0, 6))
        self.entry_box.bind("<Return>", self.send_command)

        btn_row = ttk.Frame(cmd_frame)
        btn_row.grid(row=2, column=0, columnspan=2, sticky="ew")
        btn_row.columnconfigure(0, weight=1)

        left_btns = ttk.Frame(btn_row)
        left_btns.grid(row=0, column=0, sticky="w")

        self.pause_btn = ttk.Button(left_btns, text="Pause", command=self.toggle_pause, width=10, style="CmdPause.TButton")
        self.pause_btn.pack(side=tk.LEFT)

        self.log_btn = ttk.Button(left_btns, text="Start Log...", command=self.toggle_logging, width=12, style="CmdLog.TButton")
        self.log_btn.pack(side=tk.LEFT, padx=(6, 0))

        ttk.Label(left_btns, text="Auto Delay:").pack(side=tk.LEFT, padx=(12, 4))
        self.auto_delay_combo = ttk.Combobox(
            left_btns,
            values=["0.5", "1", "2", "5", "10"],
            width=5,
            state="readonly",
        )
        self.auto_delay_combo.set("1")
        self.auto_delay_combo.pack(side=tk.LEFT)

        self.auto_start_btn = ttk.Button(
            left_btns, text="Auto Start", command=self.start_auto_send, width=11, style="CmdAutoStart.TButton"
        )
        self.auto_start_btn.pack(side=tk.LEFT, padx=(6, 0))

        self.auto_stop_btn = ttk.Button(
            left_btns, text="Auto Stop", command=self.stop_auto_send, width=10, style="CmdAutoStop.TButton", state="disabled"
        )
        self.auto_stop_btn.pack(side=tk.LEFT, padx=(6, 0))

        self.send_btn = ttk.Button(btn_row, text="Send", command=self.send_command, width=10, style="CmdPrimary.TButton")
        self.send_btn.grid(row=0, column=1, sticky="e")
        
        # Sequence list (history)
        list_frame = ttk.Frame(send_seq_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        self.cmd_list = tk.Listbox(
            list_frame,
            bg="#ffffff",
            fg="#111111",
            font=("Calibri", 10),
            selectbackground=self.colors["accent"],
            selectforeground="white",
            highlightthickness=0,
            relief=tk.SOLID,
            borderwidth=1,
            activestyle="none",
        )
        self.cmd_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        list_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.cmd_list.yview)
        list_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.cmd_list.configure(yscrollcommand=list_scrollbar.set)
        
        self.cmd_list.bind("<Double-1>", self.send_from_history)
        self.cmd_list.bind("<Delete>", self.delete_history_item)
        self.cmd_list.bind("<F2>", self.edit_history_item)

        # History controls (moved below list)
        history_btn_frame = ttk.Frame(send_seq_frame)
        history_btn_frame.pack(fill=tk.X, pady=(6, 0))
        history_btn_frame.columnconfigure(0, weight=1)

        btn_group = ttk.Frame(history_btn_frame)
        btn_group.grid(row=0, column=1, sticky="e")

        self.load_btn = ttk.Button(btn_group, text="Load", command=self.load_commands, width=9, style="HistLoad.TButton")
        self.load_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.save_btn = ttk.Button(btn_group, text="Save", command=self.save_history, width=9, style="HistSave.TButton")
        self.save_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.save_as_btn = ttk.Button(btn_group, text="Save As", command=self.save_history_as, width=9, style="HistSaveAs.TButton")
        self.save_as_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.edit_btn = ttk.Button(btn_group, text="Edit", command=self.edit_history_item, width=9, style="HistEdit.TButton")
        self.edit_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.move_up_btn = ttk.Button(btn_group, text="Up", command=self.move_history_up, width=7, style="HistMove.TButton")
        self.move_up_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.move_down_btn = ttk.Button(btn_group, text="Down", command=self.move_history_down, width=7, style="HistMove.TButton")
        self.move_down_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.history_clear_btn = ttk.Button(btn_group, text="Clear", command=self.clear_history, width=9, style="HistClear.TButton")
        self.history_clear_btn.pack(side=tk.LEFT)
        
    def setup_right_panel(self, parent):
        # Terminal frame
        terminal_frame = ttk.LabelFrame(parent, text="Serial Monitor", padding=10)
        terminal_frame.pack(fill=tk.BOTH, expand=True)
        
        # Terminal controls
        term_ctrl_frame = ttk.Frame(terminal_frame)
        term_ctrl_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(term_ctrl_frame, text="Font Size:").pack(side=tk.LEFT, padx=(0, 5))
        self.font_size = tk.IntVar(value=10)
        
        # Use tk.Spinbox instead of ttk.Spinbox
        font_spinbox = tk.Spinbox(term_ctrl_frame, from_=8, to=24, width=5, textvariable=self.font_size,
                                 command=self.change_font_size)
        font_spinbox.pack(side=tk.LEFT, padx=(0, 10))
        
        self.output_clear_btn = ttk.Button(term_ctrl_frame, text="Clear Output", command=self.clear_output, style="ClearOutput.TButton")
        self.output_clear_btn.pack(side=tk.RIGHT)

        # Tabs: ASCII/HEX/Decimal/Binary
        self.monitor_tabs = ttk.Notebook(terminal_frame)
        self.monitor_tabs.pack(fill=tk.BOTH, expand=True)

        ascii_tab = ttk.Frame(self.monitor_tabs)
        hex_tab = ttk.Frame(self.monitor_tabs)
        decimal_tab = ttk.Frame(self.monitor_tabs)
        binary_tab = ttk.Frame(self.monitor_tabs)
        self.monitor_tabs.add(ascii_tab, text="ASCII")
        self.monitor_tabs.add(hex_tab, text="HEX")
        self.monitor_tabs.add(decimal_tab, text="Decimal")
        self.monitor_tabs.add(binary_tab, text="Binary")

        # ASCII output
        self.output_box = scrolledtext.ScrolledText(
            ascii_tab,
            wrap=tk.WORD,
            state="disabled",
            bg="#ffffff",
            fg="#111111",
            font=("Calibri", 11),
            insertbackground="#111111",
            padx=10,
            pady=10,
        )
        self.output_box.pack(fill=tk.BOTH, expand=True)

        # Configure tags for colored text (ASCII tab)
        self.output_box.tag_config("timestamp", foreground="#6a737d")
        self.output_box.tag_config("send", foreground="#0969da")
        self.output_box.tag_config("receive", foreground="#111111")
        self.output_box.tag_config("error", foreground="#d1242f")
        self.output_box.tag_config("info", foreground="#1a7f37")

        # HEX output
        self.hex_output_box = scrolledtext.ScrolledText(
            hex_tab,
            wrap=tk.NONE,
            state="disabled",
            bg="#ffffff",
            fg="#111111",
            font=("Calibri", 11),
            insertbackground="#111111",
            padx=10,
            pady=10,
        )
        self.hex_output_box.pack(fill=tk.BOTH, expand=True)

        self.hex_output_box.tag_config("timestamp", foreground="#6a737d")
        self.hex_output_box.tag_config("send", foreground="#0969da")
        self.hex_output_box.tag_config("error", foreground="#d1242f")
        self.hex_output_box.tag_config("info", foreground="#1a7f37")

        # Decimal output
        self.dec_output_box = scrolledtext.ScrolledText(
            decimal_tab,
            wrap=tk.NONE,
            state="disabled",
            bg="#ffffff",
            fg="#111111",
            font=("Calibri", 11),
            insertbackground="#111111",
            padx=10,
            pady=10,
        )
        self.dec_output_box.pack(fill=tk.BOTH, expand=True)
        self.dec_output_box.tag_config("timestamp", foreground="#6a737d")
        self.dec_output_box.tag_config("error", foreground="#d1242f")
        self.dec_output_box.tag_config("info", foreground="#1a7f37")

        # Binary output
        self.bin_output_box = scrolledtext.ScrolledText(
            binary_tab,
            wrap=tk.NONE,
            state="disabled",
            bg="#ffffff",
            fg="#111111",
            font=("Calibri", 11),
            insertbackground="#111111",
            padx=10,
            pady=10,
        )
        self.bin_output_box.pack(fill=tk.BOTH, expand=True)
        self.bin_output_box.tag_config("timestamp", foreground="#6a737d")
        self.bin_output_box.tag_config("error", foreground="#d1242f")
        self.bin_output_box.tag_config("info", foreground="#1a7f37")
        
    def setup_status_bar(self):
        status_frame = ttk.Frame(self, relief=tk.SUNKEN)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.status_connection = ttk.Label(status_frame, text="Disconnected", anchor=tk.W)
        self.status_connection.pack(side=tk.LEFT, padx=5, pady=2)
        
        self.status_stats = ttk.Label(status_frame, text="Received: 0 bytes | Sent: 0 bytes", anchor=tk.W)
        self.status_stats.pack(side=tk.LEFT, padx=5, pady=2)
        
        self.status_port = ttk.Label(status_frame, text="Port: None", anchor=tk.W)
        self.status_port.pack(side=tk.LEFT, padx=5, pady=2)
        
        self.status_baud = ttk.Label(status_frame, text="Baud: None", anchor=tk.W)
        self.status_baud.pack(side=tk.LEFT, padx=5, pady=2)

    def on_baud_change(self, event=None):
        self.update_baud_status()

    def update_baud_status(self):
        try:
            baud = self.baud_combo.get().strip()
        except Exception:
            baud = ""
        self.status_baud.config(text=f"Baud: {baud}" if baud else "Baud: None")
        
    def change_font_size(self):
        new_size = self.font_size.get()
        self.output_box.config(font=("Calibri", new_size))
        if hasattr(self, "hex_output_box"):
            self.hex_output_box.config(font=("Calibri", new_size))
        if hasattr(self, "dec_output_box"):
            self.dec_output_box.config(font=("Calibri", new_size))
        if hasattr(self, "bin_output_box"):
            self.bin_output_box.config(font=("Calibri", new_size))
        
    def on_line_ending_change(self, event):
        selected = self.line_ending_combo.get()
        self.current_line_ending = self.line_endings[selected]
        
    def check_ports(self):
        if not self.connected:
            current_port = self.port_combo.get()
            available_ports = self.get_ports()
            self.port_combo['values'] = available_ports
            
            # If the current port is no longer available, clear the selection
            if current_port and current_port not in available_ports:
                self.port_combo.set('')
                
        self.after(1000, self.check_ports)
        
    def get_ports(self):
        return [p.device for p in serial.tools.list_ports.comports()]

    def refresh_ports(self):
        ports = self.get_ports()
        self.port_combo['values'] = ports
        if ports and not self.port_combo.get():
            self.port_combo.set(ports[0])
        self.update_status("Ports refreshed")

    def update_status(self, message):
        self.status_connection.config(text=message)
        if hasattr(self, "info_label"):
            self.info_label.config(text=message)
        
    def update_stats(self):
        self.status_stats.config(text=f"Received: {self.received_bytes} bytes | Sent: {self.sent_bytes} bytes")

    def clear_output(self):
        self.output_box.config(state="normal")
        self.output_box.delete(1.0, tk.END)
        self.output_box.config(state="disabled")

        if hasattr(self, "hex_output_box"):
            self.hex_output_box.config(state="normal")
            self.hex_output_box.delete(1.0, tk.END)
            self.hex_output_box.config(state="disabled")
        if hasattr(self, "dec_output_box"):
            self.dec_output_box.config(state="normal")
            self.dec_output_box.delete(1.0, tk.END)
            self.dec_output_box.config(state="disabled")
        if hasattr(self, "bin_output_box"):
            self.bin_output_box.config(state="normal")
            self.bin_output_box.delete(1.0, tk.END)
            self.bin_output_box.config(state="disabled")

        self.hex_offset = 0
        self.ascii_at_line_start = True
        self.hex_at_line_start = True
        self.dec_at_line_start = True
        self.bin_at_line_start = True
        self.update_status("Output cleared")
        # Keep focus on typing after clearing
        try:
            self.entry_box.focus_set()
        except Exception:
            pass

    def toggle_pause(self):
        self.paused = not self.paused
        self.pause_btn.config(text="Resume" if self.paused else "Pause")
        if self.paused:
            self.update_status("Paused (RX buffered)")
        else:
            if self.dropped_while_paused:
                self.log_output(f"\n[Paused] Dropped {self.dropped_while_paused} bytes while paused (buffer limit)\n", "error")
                self.dropped_while_paused = 0
            self.update_status("Resumed")

    def toggle_logging(self):
        if self.log_fp:
            try:
                self.log_fp.flush()
                self.log_fp.close()
            except Exception:
                pass
            self.log_fp = None
            self.update_status("Logging stopped")
            self.log_btn.config(text="Start Log...")
            self.log_output("Logging stopped\n", "info")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".log",
            filetypes=[("Log Files", "*.log"), ("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        if not file_path:
            return

        try:
            self.log_file_path = file_path
            self.log_fp = open(file_path, "a", encoding="utf-8", newline="")
            self.log_btn.config(text="Stop Log")
            self.update_status(f"Logging to {file_path}")
            self.log_output(f"Logging started: {file_path}\n", "info")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start log: {e}")
            self.update_status(f"Log start failed: {e}")

    def connect_serial(self):
        port = self.port_combo.get()
        baud = self.baud_combo.get()
        databits = self.databits_combo.get()
        parity_ui = self.parity_combo.get()
        stopbits_ui = self.stopbits_combo.get()
        
        if not port:
            messagebox.showerror("Error", "Please select a serial port")
            return
            
        try:
            bytesize_map = {
                "5": serial.FIVEBITS,
                "6": serial.SIXBITS,
                "7": serial.SEVENBITS,
                "8": serial.EIGHTBITS,
            }
            parity_map = {
                "None": serial.PARITY_NONE,
                "Even": serial.PARITY_EVEN,
                "Odd": serial.PARITY_ODD,
                "Mark": serial.PARITY_MARK,
                "Space": serial.PARITY_SPACE,
            }
            stopbits_map = {
                "1": serial.STOPBITS_ONE,
                "1.5": serial.STOPBITS_ONE_POINT_FIVE,
                "2": serial.STOPBITS_TWO,
            }

            self.ser = serial.Serial(
                port=port,
                baudrate=int(baud),
                bytesize=bytesize_map.get(databits, serial.EIGHTBITS),
                parity=parity_map.get(parity_ui, serial.PARITY_NONE),
                stopbits=stopbits_map.get(stopbits_ui, serial.STOPBITS_ONE),
                timeout=1
            )
            self.stop_thread = False
            self.connected = True
            self.paused = False
            self.pause_btn.config(text="Pause")
            self.hex_offset = 0
            self.ascii_at_line_start = True
            self.hex_at_line_start = True
            self.dec_at_line_start = True
            self.bin_at_line_start = True
            threading.Thread(target=self.read_serial, daemon=True).start()
            
            # Update UI states
            self.connect_btn.config(state="disabled")
            self.disconnect_btn.config(state="normal")
            self.port_combo.config(state="disabled")
            self.baud_combo.config(state="disabled")
            self.databits_combo.config(state="disabled")
            self.parity_combo.config(state="disabled")
            self.stopbits_combo.config(state="disabled")
            self.refresh_btn.config(state="disabled")
            
            # Set focus to command entry
            self.entry_box.focus()
            
            # Update status
            self.update_status(f"Connected to {port}")
            self.status_port.config(text=f"Port: {port}")
            self.status_baud.config(text=f"Baud: {baud}")
            
            # Log connection
            self.log_output(
                f"Connected to {port} at {baud} baud (Data {databits}, Parity {parity_ui}, Stop {stopbits_ui})\n",
                "info",
            )
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open port: {e}")
            self.update_status(f"Connection failed: {e}")

    def disconnect_serial(self):
        if self.ser and self.ser.is_open:
            self.stop_auto_send()
            self.stop_thread = True
            self.connected = False
            self.ser.close()
            
            # Update UI states
            self.connect_btn.config(state="normal")
            self.disconnect_btn.config(state="disabled")
            self.port_combo.config(state="readonly")
            self.baud_combo.config(state="readonly")
            self.databits_combo.config(state="readonly")
            self.parity_combo.config(state="readonly")
            self.stopbits_combo.config(state="readonly")
            self.refresh_btn.config(state="normal")
            
            # Update status
            self.update_status("Disconnected")
            self.status_port.config(text="Port: None")
            self.status_baud.config(text="Baud: None")
            
            # Log disconnection
            self.log_output("Disconnected\n", "info")
            self.log_hex_output("Disconnected\n", "info")
            self.log_dec_output("Disconnected\n", "info")
            self.log_bin_output("Disconnected\n", "info")

            # Stop logging cleanly if active
            if self.log_fp:
                try:
                    self.log_fp.flush()
                    self.log_fp.close()
                except Exception:
                    pass
                self.log_fp = None
                self.log_btn.config(text="Start Log...")

    def read_serial(self):
        while not self.stop_thread and self.ser and self.ser.is_open:
            try:
                # Read all available data
                if self.ser.in_waiting > 0:
                    data = self.ser.read(self.ser.in_waiting)
                    if data:
                        # queue raw bytes; decode happens in main thread
                        self.rx_queue.put(data)
            except Exception as e:
                if not self.stop_thread:
                    self.rx_queue.put(("__error__", str(e)))
                break

    def process_rx_queue(self):
        try:
            # Drain queue quickly each tick to keep UI responsive
            while True:
                item = self.rx_queue.get_nowait()
                if isinstance(item, tuple) and len(item) == 2 and item[0] == "__error__":
                    self.log_output(f"Read error: {item[1]}\n", "error")
                    self.log_hex_output(f"Read error: {item[1]}\n", "error")
                    self.log_dec_output(f"Read error: {item[1]}\n", "error")
                    self.log_bin_output(f"Read error: {item[1]}\n", "error")
                    continue

                if not isinstance(item, (bytes, bytearray)):
                    continue

                if self.paused:
                    # Prevent unbounded growth while paused
                    pending_bytes = sum(len(x) for x in list(self.rx_queue.queue) if isinstance(x, (bytes, bytearray)))
                    if pending_bytes > self.max_pause_buffer:
                        self.dropped_while_paused += len(item)
                    continue

                raw = bytes(item)
                if not raw:
                    continue

                self.received_bytes += len(raw)
                self.update_stats()

                # ASCII tab (best-effort decode)
                text = raw.decode(errors="ignore")
                if text:
                    self.log_output(text, "receive")
                    if self.log_fp:
                        self._write_log("RX", text)

                # HEX tab (always show raw bytes)
                dump = self.format_hex_ascii(raw, base_offset=self.hex_offset)
                self.hex_offset += len(raw)
                self.log_hex_output(dump, "receive")
                self.log_dec_output(self.format_decimal(raw), "receive")
                self.log_bin_output(self.format_binary(raw), "receive")
                if self.log_fp:
                    self._write_log("RX_HEX", dump.rstrip("\n"))
        except queue.Empty:
            pass
        finally:
            self.after(50, self.process_rx_queue)

    # def format_hex_ascii(self, data: bytes, width: int = 16, base_offset: int = 0) -> str:
    #     # Simple hexdump: "00000000  41 54 0D 0A ...  |AT..|"
    #     lines = []
    #     for offset in range(0, len(data), width):
    #         chunk = data[offset:offset + width]
    #         hex_part = " ".join(f"{b:02X}" for b in chunk)
    #         # pad to fixed width for alignment
    #         hex_part = hex_part.ljust(width * 3 - 1)
    #         ascii_part = "".join(chr(b) if 32 <= b <= 126 else "." for b in chunk)
    #         lines.append(f"{(base_offset + offset):08X}  {hex_part}  |{ascii_part}|\n")
    #     return "".join(lines)

    def format_hex_ascii(self, data: bytes, width: int = 16, base_offset: int = 0) -> str:
        lines = []
        for offset in range(0, len(data), width):
            chunk = data[offset:offset + width]

            hex_part = " ".join(f"{b:02X}" for b in chunk)
            hex_part = hex_part.ljust(width * 3)

            ascii_part = "".join(chr(b) if 32 <= b <= 126 else "." for b in chunk)

            lines.append(f"{(base_offset + offset):08X} │ {hex_part} │ {ascii_part}\n")

        return "".join(lines)

    def format_decimal(self, data: bytes, width: int = 16) -> str:
        lines = []
        for offset in range(0, len(data), width):
            chunk = data[offset:offset + width]
            dec_part = " ".join(f"{b:03d}" for b in chunk)
            lines.append(f"{offset:08X} │ {dec_part}\n")
        return "".join(lines)

    def format_binary(self, data: bytes, width: int = 8) -> str:
        lines = []
        for offset in range(0, len(data), width):
            chunk = data[offset:offset + width]
            bin_part = " ".join(f"{b:08b}" for b in chunk)
            lines.append(f"{offset:08X} │ {bin_part}\n")
        return "".join(lines)

    def parse_hex_input(self, s: str) -> bytes:
        """
        Accepts inputs like:
          "41 54 0D 0A"
          "0x41,0x54,0x0D,0x0A"
          "41540D0A"
        """
        s = (s or "").strip()
        if not s:
            return b""

        # keep only hex digits (drop 0x, commas, spaces, etc.)
        hex_only = re.sub(r"[^0-9a-fA-F]", "", s)
        if len(hex_only) % 2 != 0:
            raise ValueError("HEX input must contain an even number of hex digits")
        return bytes.fromhex(hex_only)

    def on_send_mode_change(self, *args):
        try:
            new_mode = self.send_mode.get()
        except Exception:
            return

        if not hasattr(self, "entry_box"):
            self._last_send_mode = new_mode
            return

        current = self.entry_box.get()
        if not current:
            self._last_send_mode = new_mode
            return

        # Convert existing input when toggling modes
        try:
            if self._last_send_mode == new_mode:
                return

            if new_mode == "hex":
                raw = current.encode(errors="ignore")
                converted = raw.hex(" ").upper()
            else:
                raw = self.parse_hex_input(current)
                converted = raw.decode(errors="replace")

            self.entry_box.delete(0, tk.END)
            self.entry_box.insert(0, converted)
        except Exception as e:
            # Keep user text as-is; just inform
            messagebox.showerror("Send Mode", f"Cannot convert input for {new_mode.upper()} mode:\n{e}")
        finally:
            self._last_send_mode = new_mode

    def log_tx_bytes(self, data: bytes):
        if not data:
            return
        dump = self.format_hex_ascii(data, base_offset=0)
        # Prefix makes it easy to spot TX frames in HEX tab
        self.log_hex_output("TX\n", "send")
        self.log_hex_output(dump, "send")

    def _write_log(self, direction, text):
        if not self.log_fp:
            return
        try:
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            self.log_fp.write(f"{ts}\t{direction}\t{text}\n" if not text.endswith("\n") else f"{ts}\t{direction}\t{text}")
            self.log_fp.flush()
        except Exception as e:
            # If logging fails mid-session, stop it cleanly
            try:
                self.log_fp.close()
            except Exception:
                pass
            self.log_fp = None
            self.log_btn.config(text="Start Log...")
            self.log_output(f"Logging error: {e}\n", "error")

    def _normalize_newlines_for_display(self, text: str) -> str:
        # Treat CRLF and CR as a single line break so timestamps
        # are added once per logical line.
        s = str(text)
        s = s.replace("\r\n", "\n")
        s = s.replace("\r", "\n")
        return s

    def log_output(self, text, msg_type="receive"):
        self.output_box.config(state="normal")

        text = self._normalize_newlines_for_display(text)
        # Insert timestamps at the start of each line (not mid-line)
        parts = text.splitlines(keepends=True)
        for part in parts if parts else [text]:
            if self.timestamp_var.get() and self.ascii_at_line_start:
                timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                self.output_box.insert(tk.END, f"[{timestamp}] ", "timestamp")

            self.output_box.insert(tk.END, part, msg_type)

            # Update line-start tracker based on line ending
            if part.endswith("\n") or part.endswith("\r"):
                self.ascii_at_line_start = True
            else:
                self.ascii_at_line_start = False

        # Auto-scroll if enabled
        if self.autoscroll_var.get():
            self.output_box.see(tk.END)

        self.output_box.config(state="disabled")

    def log_hex_output(self, text, msg_type="receive"):
        if not hasattr(self, "hex_output_box"):
            return
        self.hex_output_box.config(state="normal")

        text = self._normalize_newlines_for_display(text)
        parts = text.splitlines(keepends=True)
        tag = msg_type if msg_type in ("error", "info", "send") else None
        for part in parts if parts else [text]:
            if self.timestamp_var.get() and self.hex_at_line_start:
                timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                self.hex_output_box.insert(tk.END, f"[{timestamp}] ", "timestamp")

            if tag:
                self.hex_output_box.insert(tk.END, part, tag)
            else:
                self.hex_output_box.insert(tk.END, part)

            if part.endswith("\n") or part.endswith("\r"):
                self.hex_at_line_start = True
            else:
                self.hex_at_line_start = False

        if self.autoscroll_var.get():
            self.hex_output_box.see(tk.END)

        self.hex_output_box.config(state="disabled")

    def log_dec_output(self, text, msg_type="receive"):
        self._log_extra_output(
            box_name="dec_output_box",
            text=text,
            msg_type=msg_type,
            tracker_attr="dec_at_line_start",
        )

    def log_bin_output(self, text, msg_type="receive"):
        self._log_extra_output(
            box_name="bin_output_box",
            text=text,
            msg_type=msg_type,
            tracker_attr="bin_at_line_start",
        )

    def _log_extra_output(self, box_name: str, text: str, msg_type: str, tracker_attr: str):
        box = getattr(self, box_name, None)
        if box is None:
            return
        box.config(state="normal")
        text = self._normalize_newlines_for_display(text)
        parts = text.splitlines(keepends=True)
        tag = msg_type if msg_type in ("error", "info", "send") else None
        at_line_start = getattr(self, tracker_attr, True)
        for part in parts if parts else [text]:
            if self.timestamp_var.get() and at_line_start:
                timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                box.insert(tk.END, f"[{timestamp}] ", "timestamp")
            if tag:
                box.insert(tk.END, part, tag)
            else:
                box.insert(tk.END, part)
            at_line_start = part.endswith("\n") or part.endswith("\r")
        setattr(self, tracker_attr, at_line_start)
        if self.autoscroll_var.get():
            box.see(tk.END)
        box.config(state="disabled")

    def send_command(self, event=None):
        cmd = self.entry_box.get().strip()
        if cmd and self.ser and self.ser.is_open:
            ok = self.send_single_command(cmd, status_prefix="Sent")
            if ok:
                # Add to history if not duplicate of last command
                if not self.cmd_list.size() or self.cmd_list.get(self.cmd_list.size() - 1) != cmd:
                    self.cmd_list.insert(tk.END, cmd)
        elif self.ser and self.ser.is_open:
            # Send just the line ending if input is empty
            try:
                payload = self.current_line_ending.encode()
                self.ser.write(payload)
                self.sent_bytes += len(payload)
                self.update_stats()
                if self.echo_sent_var.get():
                    self.log_output(self.current_line_ending, "send")
                    self.log_tx_bytes(payload)
                if self.log_fp:
                    self._write_log("TX", self.current_line_ending)
            except Exception as e:
                self.log_output(f"Send error: {e}\n", "error")
                self.log_hex_output(f"Send error: {e}\n", "error")
                
        self.entry_box.delete(0, tk.END)

    def send_from_history(self, event):
        selection = self.cmd_list.curselection()
        if selection:
            cmd = self.cmd_list.get(selection[0]).strip()
            if cmd and self.ser and self.ser.is_open:
                self.send_single_command(cmd, status_prefix="Sent from history")

    def send_single_command(self, cmd, status_prefix="Sent"):
        try:
            if self.send_mode.get() == "hex":
                payload = self.parse_hex_input(cmd)
                payload += self.current_line_ending.encode()
                self.ser.write(payload)
                self.sent_bytes += len(payload)
                if self.echo_sent_var.get():
                    self.log_output(f"[TX HEX] {cmd}\n", "send")
                    self.log_tx_bytes(payload)
                if self.log_fp:
                    self._write_log("TX_HEX", payload.hex(" ").upper())
            else:
                full_cmd = cmd + self.current_line_ending
                payload = full_cmd.encode()
                self.ser.write(payload)
                self.sent_bytes += len(payload)
                if self.echo_sent_var.get():
                    self.log_output(full_cmd, "send")
                    self.log_tx_bytes(payload)
                if self.log_fp:
                    self._write_log("TX", full_cmd)

            self.update_stats()
            self.update_status(f"{status_prefix}: {cmd}")
            return True
        except Exception as e:
            self.log_output(f"Send error: {e}\n", "error")
            self.log_hex_output(f"Send error: {e}\n", "error")
            self.update_status(f"Send failed: {e}")
            return False

    def start_auto_send(self):
        if self.auto_send_running:
            return
        if not (self.ser and self.ser.is_open):
            self.update_status("Connect serial before auto send")
            return
        if self.cmd_list.size() == 0:
            self.update_status("No commands available for auto send")
            return

        selection = self.cmd_list.curselection()
        self.auto_send_index = selection[0] if selection else 0
        self.auto_send_running = True
        self.auto_start_btn.config(state="disabled")
        self.auto_stop_btn.config(state="normal")
        self.update_status("Auto send started")
        self._run_auto_send_step()

    def _run_auto_send_step(self):
        if not self.auto_send_running:
            return
        if not (self.ser and self.ser.is_open):
            self.stop_auto_send()
            self.update_status("Auto send stopped: disconnected")
            return
        if self.auto_send_index >= self.cmd_list.size():
            self.stop_auto_send()
            self.update_status("Auto send completed")
            return

        cmd = self.cmd_list.get(self.auto_send_index).strip()
        self.cmd_list.selection_clear(0, tk.END)
        self.cmd_list.selection_set(self.auto_send_index)
        self.cmd_list.activate(self.auto_send_index)

        if cmd:
            ok = self.send_single_command(cmd, status_prefix="Auto sent")
            if not ok:
                self.stop_auto_send()
                return

        self.auto_send_index += 1
        delay_ms = int(float(self.auto_delay_combo.get()) * 1000)
        self.auto_send_after_id = self.after(delay_ms, self._run_auto_send_step)

    def stop_auto_send(self):
        if self.auto_send_after_id is not None:
            try:
                self.after_cancel(self.auto_send_after_id)
            except Exception:
                pass
            self.auto_send_after_id = None
        was_running = self.auto_send_running
        self.auto_send_running = False
        if hasattr(self, "auto_start_btn"):
            self.auto_start_btn.config(state="normal")
        if hasattr(self, "auto_stop_btn"):
            self.auto_stop_btn.config(state="disabled")
        if was_running:
            self.update_status("Auto send stopped")

    def delete_history_item(self, event):
        selection = self.cmd_list.curselection()
        if selection:
            self.cmd_list.delete(selection[0])

    def edit_history_item(self, event=None):
        selection = self.cmd_list.curselection()
        if not selection:
            self.update_status("Select a command to edit")
            return

        index = selection[0]
        current_cmd = self.cmd_list.get(index)
        updated_cmd = self.open_edit_command_dialog(current_cmd)
        if updated_cmd is None:
            return

        updated_cmd = updated_cmd.strip()
        if not updated_cmd:
            self.update_status("Edited command cannot be empty")
            return

        self.cmd_list.delete(index)
        self.cmd_list.insert(index, updated_cmd)
        self.cmd_list.selection_clear(0, tk.END)
        self.cmd_list.selection_set(index)
        self.cmd_list.activate(index)
        self.update_status("Command updated")

    def open_edit_command_dialog(self, initial_value):
        dialog = tk.Toplevel(self)
        dialog.title("Edit Command")
        dialog.transient(self)
        dialog.grab_set()
        dialog.geometry("760x220")
        dialog.minsize(640, 180)

        container = ttk.Frame(dialog, padding=12)
        container.pack(fill=tk.BOTH, expand=True)
        container.columnconfigure(0, weight=1)
        container.rowconfigure(1, weight=1)

        ttk.Label(container, text="Update command:").grid(row=0, column=0, sticky="w", pady=(0, 6))

        input_text = tk.Text(container, height=6, wrap=tk.NONE, font=("Calibri", 11))
        input_text.grid(row=1, column=0, sticky="nsew")
        input_text.insert("1.0", initial_value)
        input_text.focus_set()
        input_text.tag_add("sel", "1.0", "end-1c")

        x_scroll = ttk.Scrollbar(container, orient=tk.HORIZONTAL, command=input_text.xview)
        x_scroll.grid(row=2, column=0, sticky="ew")
        y_scroll = ttk.Scrollbar(container, orient=tk.VERTICAL, command=input_text.yview)
        y_scroll.grid(row=1, column=1, sticky="ns")
        input_text.configure(xscrollcommand=x_scroll.set, yscrollcommand=y_scroll.set)

        result = {"value": None}

        def on_ok():
            result["value"] = input_text.get("1.0", "end-1c")
            dialog.destroy()

        def on_cancel():
            dialog.destroy()

        btn_row = ttk.Frame(container)
        btn_row.grid(row=3, column=0, columnspan=2, sticky="e", pady=(10, 0))
        ttk.Button(btn_row, text="Cancel", command=on_cancel, width=10).pack(side=tk.RIGHT)
        ttk.Button(btn_row, text="OK", command=on_ok, width=10).pack(side=tk.RIGHT, padx=(0, 6))

        dialog.bind("<Escape>", lambda e: on_cancel())
        dialog.bind("<Control-Return>", lambda e: on_ok())
        self.wait_window(dialog)
        return result["value"]

    def move_history_up(self):
        selection = self.cmd_list.curselection()
        if not selection:
            self.update_status("Select a command to move")
            return
        index = selection[0]
        if index == 0:
            return
        value = self.cmd_list.get(index)
        self.cmd_list.delete(index)
        self.cmd_list.insert(index - 1, value)
        self.cmd_list.selection_clear(0, tk.END)
        self.cmd_list.selection_set(index - 1)
        self.cmd_list.activate(index - 1)
        self.update_status("Command moved up")

    def move_history_down(self):
        selection = self.cmd_list.curselection()
        if not selection:
            self.update_status("Select a command to move")
            return
        index = selection[0]
        last_index = self.cmd_list.size() - 1
        if index >= last_index:
            return
        value = self.cmd_list.get(index)
        self.cmd_list.delete(index)
        self.cmd_list.insert(index + 1, value)
        self.cmd_list.selection_clear(0, tk.END)
        self.cmd_list.selection_set(index + 1)
        self.cmd_list.activate(index + 1)
        self.update_status("Command moved down")

    def clear_history(self):
        self.cmd_list.delete(0, tk.END)
        self.update_status("History cleared")

    def load_commands(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Text Files", "*.txt"), ("CSV Files", "*.csv"), ("All Files", "*.*")]
        )
        if not file_path:
            return

        try:
            self.load_history_from_path(file_path)
            self.log_output(f"Loaded commands from {file_path}\n", "info")
            self.update_status(f"Commands loaded from {file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load file: {e}")
            self.update_status(f"Load error: {e}")

    def _write_history_to_path(self, file_path):
        with open(file_path, "w", encoding="utf-8") as f:
            if file_path.endswith(".csv"):
                writer = csv.writer(f)
                for i in range(self.cmd_list.size()):
                    writer.writerow([self.cmd_list.get(i)])
            else:
                for i in range(self.cmd_list.size()):
                    f.write(self.cmd_list.get(i) + "\n")

    def save_history(self):
        if not self.cmd_list.size():
            messagebox.showinfo("Info", "No commands in history to save")
            return

        # Quick save if path already known, otherwise behave like Save As
        if not self.history_file_path:
            self.save_history_as()
            return

        try:
            self._write_history_to_path(self.history_file_path)
            self.log_output(f"Saved command history to {self.history_file_path}\n", "info")
            self.update_status(f"History saved to {self.history_file_path}")
            self.save_app_state()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save file: {e}")
            self.update_status(f"Save error: {e}")

    def save_history_as(self):
        if not self.cmd_list.size():
            messagebox.showinfo("Info", "No commands in history to save")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("CSV Files", "*.csv"), ("All Files", "*.*")]
        )
        if not file_path:
            return

        try:
            self._write_history_to_path(file_path)
            self.history_file_path = file_path
            self.save_app_state()
            self.log_output(f"Saved command history to {file_path}\n", "info")
            self.update_status(f"History saved to {file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save file: {e}")
            self.update_status(f"Save error: {e}")

    def load_history_from_path(self, file_path):
        self.cmd_list.delete(0, tk.END)
        with open(file_path, "r", encoding="utf-8") as f:
            if file_path.endswith(".csv"):
                reader = csv.reader(f)
                for row in reader:
                    if row:
                        cmd = row[0].strip()
                        if cmd:
                            self.cmd_list.insert(tk.END, cmd)
            else:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        self.cmd_list.insert(tk.END, line)
        self.history_file_path = file_path
        self.save_app_state()

    def load_app_state(self):
        if not os.path.exists(self.state_file_path):
            return
        try:
            with open(self.state_file_path, "r", encoding="utf-8") as f:
                state = json.load(f)
            self.history_file_path = state.get("history_file_path") or None
        except Exception:
            # Ignore bad state file and continue with defaults
            self.history_file_path = None

    def save_app_state(self):
        state = {
            "history_file_path": self.history_file_path,
        }
        try:
            with open(self.state_file_path, "w", encoding="utf-8") as f:
                json.dump(state, f, indent=2)
        except Exception:
            pass

    def auto_load_last_history(self):
        if not self.history_file_path:
            return
        if not os.path.exists(self.history_file_path):
            return
        try:
            self.load_history_from_path(self.history_file_path)
            self.update_status(f"Auto-loaded: {self.history_file_path}")
            self.log_output(f"Auto-loaded commands from {self.history_file_path}\n", "info")
        except Exception as e:
            self.update_status(f"Auto-load failed: {e}")

    def on_close(self):
        self.stop_auto_send()
        self.save_app_state()
        self.destroy()


if __name__ == "__main__":
    app = SerialMonitor()
    app.mainloop()
