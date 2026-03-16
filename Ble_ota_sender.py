# #!/usr/bin/env python3
# """
# BLE OTA GUI tool
# - Pick a firmware .bin
# - Scan BLE devices
# - Start / Stop OTA
# - Tune chunk size and inter-chunk delay to change transfer speed
# """

# import asyncio
# import threading
# import time
# import os
# import traceback
# import PySimpleGUI as sg
# from bleak import BleakClient, BleakScanner
# from bleak.exc import BleakError, BleakCharacteristicNotFoundError

# # Default UUIDs
# OTA_SERVICE_UUID = "12345678-1234-1234-1234-1234567890ab"
# OTA_CHARACTERISTIC_UUID = "abcd1234-5678-90ab-cdef-1234567890ab"
# VERSION_CHARACTERISTIC_UUID = "00002a26-0000-1000-8000-00805f9b34fb"

# # ---------------------------
# # CUSTOM POPUP STYLE WINDOW
# # ---------------------------
# sg.theme("DarkBlue3")

# layout = [
#     [sg.Text("Firmware (.bin):", pad=(5,5)),
#      sg.Input(key="-FILE-", enable_events=True, readonly=True, expand_x=True),
#      sg.FileBrowse(file_types=(("BIN Files", "*.bin"),), key="-BROWSE-")],

#     [sg.Text("Device prefix:"),
#      sg.Input(default_text="OPTICAL_READER_004755", key="-PREFIX-", expand_x=True),
#      sg.Button("Scan", key="-SCAN-")],

#     [sg.Listbox(values=[], size=(60,6), key="-DEVICES-", enable_events=True, expand_x=True, expand_y=True)],

#     [sg.Text("Chunk size:"),
#      sg.Slider(range=(16,4096), default_value=512, orientation="h", key="-CHUNK-", expand_x=True),
#      sg.Text("Delay (ms):"),
#      sg.Slider(range=(0,200), default_value=0, orientation="h", key="-DELAY-", expand_x=True)],

#     [sg.Checkbox("Write with response (safer, slower)", default=False, key="-WITH_RESPONSE-"),
#      sg.Button("Start OTA", key="-START-"),
#      sg.Button("Stop OTA", key="-STOP-", disabled=True)],

#     [sg.ProgressBar(100, orientation="h", size=(60, 20), key="-PROG-", expand_x=True)],

#     [sg.Multiline(size=(90, 12), key="-LOG-", disabled=True, autoscroll=True,
#                   expand_x=True, expand_y=True, reroute_stdout=False)],

#     [sg.Text("Status:"), sg.Text("", key="-STATUS-", expand_x=True)]
# ]

# # Make window auto-resizable + popup style + movable
# window = sg.Window(
#     "BLE Firmware OTA Sender",
#     layout,
#     finalize=True,
#     resizable=True,
#     grab_anywhere=True,
#     enable_close_attempted_event=True,
#     right_click_menu=["", ["Clear Log", "Exit"]],
# )

# # State
# ota_thread = None
# ota_stop_event = threading.Event()
# scan_thread = None

# # ---------------------------
# # LOG FUNCTION
# # ---------------------------
# def log(msg):
#     now = time.strftime("%H:%M:%S")
#     window["-LOG-"].print(f"[{now}] {msg}")

# # ---------------------------
# # READ FIRMWARE VERSION
# # ---------------------------
# async def read_firmware_version(client):
#     try:
#         data = await client.read_gatt_char(VERSION_CHARACTERISTIC_UUID)
#         version_str = data.decode().strip()
#         log(f"Device firmware version read: {version_str}")
#         return float(version_str)
#     except:
#         return None

# # ---------------------------
# # SEND FIRMWARE
# # ---------------------------
# async def send_firmware_async(address, file_path, chunk_size, delay_ms, with_response):
#     total_sent = 0
#     file_size = os.path.getsize(file_path)

#     log(f"Connecting to {address} ...")

#     try:
#         async with BleakClient(address) as client:
#             log(f"Connected to {address}")

#             v = await read_firmware_version(client)
#             if v:
#                 log(f"Device version: {v}")

#             with open(file_path, "rb") as f:
#                 start = time.time()

#                 while True:
#                     if ota_stop_event.is_set():
#                         log("Stop requested. Aborting transfer.")
#                         return False

#                     chunk = f.read(chunk_size)
#                     if not chunk:
#                         break

#                     await client.write_gatt_char(
#                         OTA_CHARACTERISTIC_UUID,
#                         chunk,
#                         response=with_response
#                     )

#                     total_sent += len(chunk)
#                     percent = (total_sent / file_size) * 100

#                     # Update UI
#                     window["-PROG-"].update(percent)
#                     elapsed = time.time() - start
#                     speed = total_sent / elapsed

#                     window["-STATUS-"].update(
#                         f"{total_sent}/{file_size} bytes ({int(percent)}%) - {int(speed)} B/s"
#                     )

#                     if delay_ms:
#                         await asyncio.sleep(delay_ms / 1000)

#             # Send EOF
#             try:
#                 await client.write_gatt_char(OTA_CHARACTERISTIC_UUID, b"EOF", response=True)
#             except:
#                 pass

#             window["-PROG-"].update(100)
#             window["-STATUS-"].update("Completed")
#             log("OTA complete.")

#             return True

#     except Exception as e:
#         log(f"OTA failed: {e}")
#         window["-STATUS-"].update("Error")
#         return False

# # ---------------------------
# # BACKGROUND THREAD RUNNER
# # ---------------------------
# def ota_thread_func(address, file_path, chunk, delay, resp):
#     loop = asyncio.new_event_loop()
#     asyncio.set_event_loop(loop)
#     loop.run_until_complete(send_firmware_async(address, file_path, chunk, delay, resp))
#     window.write_event_value("-OTA_DONE-", None)

# # ---------------------------
# # START / STOP OTA
# # ---------------------------
# def start_ota(address, file_path, chunk, delay, resp):
#     ota_stop_event.clear()
#     window["-START-"].update(disabled=True)
#     window["-STOP-"].update(disabled=False)

#     th = threading.Thread(
#         target=ota_thread_func,
#         args=(address, file_path, chunk, delay, resp),
#         daemon=True
#     )
#     th.start()

# def stop_ota():
#     ota_stop_event.set()
#     log("Stopping...")

# # ---------------------------
# # SCAN THREAD
# # ---------------------------
# def scan_thread_func(prefix):
#     loop = asyncio.new_event_loop()
#     asyncio.set_event_loop(loop)

#     log(f"Scanning for BLE devices prefix='{prefix}'...")
#     devices = loop.run_until_complete(BleakScanner.discover(timeout=5.0))

#     found = []
#     for d in devices:
#         name = d.name or "<no-name>"
#         if prefix and name.startswith(prefix):
#             found.append(f"{name} | {d.address}")

#     window.write_event_value("-SCAN_DONE-", found)
#     loop.close()

# # ---------------------------
# # MAIN EVENT LOOP
# # ---------------------------
# while True:
#     event, values = window.read(timeout=100)

#     if event in (sg.WIN_CLOSED, sg.WIN_CLOSE_ATTEMPTED_EVENT):
#         try:
#             # Stop OTA
#             if ota_thread and ota_thread.is_alive():
#                 log("Stopping OTA before exit...")
#                 ota_stop_event.set()
#                 ota_thread.join(timeout=3)

#             # Stop Scan thread
#             if scan_thread and scan_thread.is_alive():
#                 log("Stopping scanner...")
#                 scan_thread.join(timeout=2)

#         except Exception as e:
#             print("Exit cleanup error:", e)

#         window.close()
#         break

#     if event == "Clear Log":
#         window["-LOG-"].update("")

#     if event == "-SCAN-":
#         prefix = values["-PREFIX-"]
#         threading.Thread(target=scan_thread_func, args=(prefix,), daemon=True).start()

#     if event == "-SCAN_DONE-":
#         window["-DEVICES-"].update(values["-SCAN_DONE-"])
#         log("Scan completed.")

#     if event == "-START-":
#         file = values["-FILE-"]
#         if not os.path.isfile(file):
#             sg.popup_error("Select firmware .bin file")
#             continue

#         sel = values["-DEVICES-"]
#         if not sel:
#             sg.popup_error("Select a device")
#             continue

#         address = sel[0].split("|")[-1].strip()
#         start_ota(address, file,
#                   int(values["-CHUNK-"]),
#                   int(values["-DELAY-"]),
#                   bool(values["-WITH_RESPONSE-"]))

#     if event == "-STOP-":
#         stop_ota()

#     if event == "-OTA_DONE-":
#         window["-START-"].update(disabled=False)
#         window["-STOP-"].update(disabled=True)
#         log("OTA Finished.")

# window.close()




# """
# UBUNTU 

# MUST install the **new PySimpleGUI** from their *private server*, and first remove the broken version.

# ---

# # ✅ Follow these exact steps (Linux)

# ### 1️⃣ **Uninstall the broken version**

# ```
# python3 -m pip uninstall PySimpleGUI
# python3 -m pip cache purge
# ```

# ### 2️⃣ **Install the new correct version (from private server)**

# ```
# python3 -m pip install --upgrade --extra-index-url https://PySimpleGUI.net/install PySimpleGUI
# ```

# If the above fails, force reinstall:

# ```
# python3 -m pip install --force-reinstall --extra-index-url https://PySimpleGUI.net/install PySimpleGUI
# ```

# ---

# # ✅ Verify installation

# Run:

# ```
# python3 - << 'EOF'
# import PySimpleGUI as sg
# print("VERSION:", sg.__version__)
# sg.theme("DarkBlue3")
# print("Theme OK")
# EOF
# ```

# If it prints **Theme OK**, then your OTA GUI will work.

# ---

# # ⚠️ If still failing, I can convert the whole GUI to **Tkinter**

# Tkinter comes preinstalled on Linux and **never requires pip install**.

# Just tell me:

# 👉 “Yes, convert to Tkinter UI”

# And I will give you a **fully working OTA GUI** with zero external dependencies.

# ---

# ### Want the Tkinter version now?

# WINDOWS 

# Nice — here are **5 clear, Windows-friendly steps** to install PySimpleGUI. I’ll include exact commands you can copy into **Command Prompt (cmd.exe)** or **PowerShell**.

# ---

# ### 1) Check Python & pip

# Open Command Prompt and run:

# ```
# python --version
# python -m pip --version
# ```

# You need **Python 3.7+** (recommended 3.8–3.12). If these fail, install Python from python.org and check “Add Python to PATH” during setup.

# ---

# ### 2) (Recommended) Create and activate a virtual environment

# This keeps packages isolated.

# In **Command Prompt**:

# ```
# python -m venv venv
# venv\Scripts\activate
# ```

# In **PowerShell**:

# ```
# python -m venv venv
# .\venv\Scripts\Activate.ps1
# ```

# (If PowerShell blocks activation, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` then activate.)

# You should now see `(venv)` at the start of your prompt.

# ---

# ### 3) Upgrade pip (inside the venv)

# ```
# python -m pip install --upgrade pip setuptools wheel
# ```

# ---

# ### 4) Install PySimpleGUI (use their private index)

# PySimpleGUI sometimes publishes to a private PyPI mirror. Use this command to install (or force-reinstall) from that index:

# ```
# python -m pip install PySimpleGUI --extra-index-url https://PySimpleGUI.net/install
# ```

# If you need to force a fresh install:

# ```
# python -m pip install --force-reinstall --extra-index-url https://PySimpleGUI.net/install PySimpleGUI
# ```

# If you ever need to completely remove and clear pip cache first:

# ```
# python -m pip uninstall PySimpleGUI
# python -m pip cache purge
# ```

# (If you prefer a system install instead of a venv, add `--user` or run the pip command from an elevated/admin prompt — but venv is recommended.)

# ---

# ### 5) Verify installation

# Option A — using pip:

# ```
# python -m pip show PySimpleGUI
# ```

# This prints package name and version.

# Option B — quick Python check:

# ```
# python -c "import PySimpleGUI as sg; print('PySimpleGUI installed, module:', sg)"
# ```

# ---

# If you see any errors, paste the exact error here and I’ll help fix it (for example: TLS/SSL errors, index URL blocked, or activation policy issues). Want a one-line command that does everything (create venv, activate, install)? I can provide that too.

# """

#!/usr/bin/env python3
#!/usr/bin/env python3
"""
BLE OTA Sender - Tkinter (ttk) UI
Added:
- Chunk size number label
- Delay (ms) number label
- OTA elapsed timer (start on OTA start, stop on OTA finish)
"""

import os
import time
import threading
import asyncio
import traceback
from functools import partial
from tkinter import Tk, StringVar, IntVar, BooleanVar, filedialog, messagebox
from tkinter import N, S, E, W, LEFT, RIGHT, BOTH, X, Y
from tkinter.scrolledtext import ScrolledText
from tkinter.ttk import Frame, Label, Entry, Button, Scale, Checkbutton, Progressbar, Treeview, Style
import tkinter as tk
from tkinter import ttk


from bleak import BleakScanner, BleakClient

# Default UUIDs
OTA_SERVICE_UUID = "12345678-1234-1234-1234-1234567890ab"
OTA_CHARACTERISTIC_UUID = "abcd1234-5678-90ab-cdef-1234567890ab"
VERSION_CHARACTERISTIC_UUID = "00002a26-0000-1000-8000-00805f9b34fb"


class BLETkOTA:
    def __init__(self, root):
        self.root = root
        self.root.title("BLE Firmware OTA Sender (Tkinter)")
        self.root.geometry("900x640")
    

        # State variables
        self.file_path = StringVar()
        self.prefix = StringVar(value="OPTICAL_READER_004755")
        self.chunk_size = IntVar(value=512)
        self.delay_ms = IntVar(value=30)
        self.with_response = BooleanVar(value=False)
        self.status_text = StringVar(value="Idle")
        self.progress_val = IntVar(value=0)

        self.timer_running = False
        self.timer_start_time = 0
        self.timer_text = StringVar(value="Timer: 00:00:00")

        self.stop_event = threading.Event()
        self.ota_thread = None
        self.scan_thread = None

        self._build_ui()

    # ===================== FIXED BUTTON FUNCTIONS =====================

    def _adjust_chunk(self, delta):
        value = self.chunk_size.get() + delta
        if value < 16:
            value = 16
        if value > 4096:
            value = 4096

        self.chunk_size.set(value)       # updates scale + entry


    def _sync_chunk(self):
        """Called when user types manually in Entry and presses Enter."""
        try:
            value = int(self.chunk_entry.get())
        except:
            value = self.chunk_size.get()

        if value < 16:
            value = 16
        if value > 4096:
            value = 4096

        self.chunk_size.set(value)


    def _adjust_delay(self, delta):
        value = self.delay_ms.get() + delta
        if value < 0:
            value = 0
        if value > 200:
            value = 200

        self.delay_ms.set(value)


    def _sync_delay(self):
        """Called when user edits delay entry manually."""
        try:
            value = int(self.delay_entry.get())
        except:
            value = self.delay_ms.get()

        if value < 0:
            value = 0
        if value > 200:
            value = 200

        self.delay_ms.set(value)


    def _build_ui(self):
        style = Style(self.root)
        style.theme_use("clam")

        top = Frame(self.root, padding=(8,8))
        top.pack(fill=X, padx=6, pady=6)

        # File row
        Label(top, text="Firmware (.bin):").grid(row=0, column=0, sticky=W)
        self.file_entry = Entry(top, textvariable=self.file_path, width=70)
        self.file_entry.grid(row=0, column=1, sticky=W, padx=(6,6))
        Button(top, text="Browse...", command=self.browse_file).grid(row=0, column=2, sticky=W)

        # Prefix + Scan
        Label(top, text="Device prefix:").grid(row=1, column=0, sticky=W, pady=(8,0))
        self.prefix_entry = Entry(top, textvariable=self.prefix, width=40)
        self.prefix_entry.grid(row=1, column=1, sticky=W, pady=(8,0))
        Button(top, text="Scan", command=self.start_scan).grid(row=1, column=2, sticky=W, pady=(8,0))

        # Device list
        Label(self.root, text="Devices:").pack(anchor=W, padx=10)
        self.device_tree = Treeview(self.root, columns=("name","addr"), show="headings", height=8)
        self.device_tree.heading("name", text="Name")
        self.device_tree.heading("addr", text="Address")
        self.device_tree.column("name", width=420)
        self.device_tree.column("addr", width=200)
        self.device_tree.pack(fill=X, padx=10, pady=(4,8))

        # Controls frame
        ctrl = Frame(self.root, padding=(8,8))
        ctrl.pack(fill=X, padx=6)

        # --- CHUNK SIZE CONTROL (Slider + Entry + +/- buttons) ---
        Label(ctrl, text="Chunk size:").grid(row=0, column=0, sticky=W, pady=4)

        chunk_frame = Frame(ctrl)
        chunk_frame.grid(row=0, column=1, sticky=W)

        self.chunk_scale = Scale(chunk_frame, from_=16, to=4096, orient="horizontal",
                                variable=self.chunk_size, length=260)
        self.chunk_scale.pack(side=LEFT)

        # Minus button
        Button(chunk_frame, text="-", width=2,
            command=lambda: self._adjust_chunk(-16)).pack(side=LEFT, padx=2)

        # Plus button
        Button(chunk_frame, text="+", width=2,
            command=lambda: self._adjust_chunk(+16)).pack(side=LEFT)

        # Entry box
        self.chunk_entry = Entry(chunk_frame, width=6, textvariable=self.chunk_size)
        self.chunk_entry.pack(side=LEFT, padx=6)
        self.chunk_entry.bind("<Return>", lambda e: self._sync_chunk())

        # --- DELAY CONTROL (Slider + Entry + +/- buttons) ---
        Label(ctrl, text="Delay (ms):").grid(row=0, column=2, sticky=W, pady=4)

        delay_frame = Frame(ctrl)
        delay_frame.grid(row=0, column=3, sticky=W)

        self.delay_scale = Scale(delay_frame, from_=0, to=200, orient="horizontal",
                                variable=self.delay_ms, length=160)
        self.delay_scale.pack(side=LEFT)

        # Minus button
        Button(delay_frame, text="-", width=2,
            command=lambda: self._adjust_delay(-1)).pack(side=LEFT, padx=2)

        # Plus button
        Button(delay_frame, text="+", width=2,
            command=lambda: self._adjust_delay(+1)).pack(side=LEFT)

        # Entry box
        self.delay_entry = Entry(delay_frame, width=4, textvariable=self.delay_ms)
        self.delay_entry.pack(side=LEFT, padx=6)
        self.delay_entry.bind("<Return>", lambda e: self._sync_delay())


        # Checkbox + Buttons
        self.response_chk = Checkbutton(ctrl, text="Write with response (safer, slower)",
                                        variable=self.with_response)
        self.response_chk.grid(row=1, column=0, columnspan=2, sticky=W, pady=(8,0))

        self.start_btn = Button(ctrl, text="Start OTA", command=self.start_ota)
        self.start_btn.grid(row=1, column=2, sticky=W, padx=(6,6), pady=(8,0))

        self.stop_btn = Button(ctrl, text="Stop OTA", command=self.stop_ota, state="disabled")
        self.stop_btn.grid(row=1, column=3, sticky=W, pady=(8,0))

        # Progress + status + timer
        prog_frame = Frame(self.root, padding=(8,8))
        prog_frame.pack(fill=X, padx=10, pady=(6,0))
        self.progress = Progressbar(prog_frame, orient="horizontal", mode="determinate",
                                    maximum=100, variable=self.progress_val)
        self.progress.pack(fill=X, padx=2)

        Label(prog_frame, textvariable=self.status_text).pack(anchor=W, pady=(6,0))
        Label(prog_frame, textvariable=self.timer_text, foreground="blue").pack(anchor=W)

        # Log window
        Label(self.root, text="Log:").pack(anchor=W, padx=10, pady=(8,0))
        self.log_text = ScrolledText(self.root, height=14, state="disabled")
        self.log_text.pack(fill=BOTH, expand=True, padx=10, pady=(2,10))

    # Logging
    def log(self, msg):
        now = time.strftime("%H:%M:%S")
        self.log_text.configure(state="normal")
        self.log_text.insert("end", f"[{now}] {msg}\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    # Timer functions
    def start_timer(self):
        self.timer_start_time = time.time()
        self.timer_running = True
        self._update_timer()

    def stop_timer(self):
        self.timer_running = False

    def _update_timer(self):
        if not self.timer_running:
            return
        elapsed = int(time.time() - self.timer_start_time)
        h = elapsed // 3600
        m = (elapsed % 3600) // 60
        s = elapsed % 60
        self.timer_text.set(f"Timer: {h:02d}:{m:02d}:{s:02d}")
        self.root.after(1000, self._update_timer)

    # Status + progress
    def set_status(self, text):
        self.status_text.set(text)

    def set_progress(self, percent):
        self.progress_val.set(int(percent))

    # Browse file
    def browse_file(self):
        p = filedialog.askopenfilename(filetypes=[("BIN files", "*.bin"), ("All files", "*.*")])
        if p:
            self.file_path.set(p)

    # Scan devices
    def start_scan(self):
        if self.scan_thread and self.scan_thread.is_alive():
            messagebox.showinfo("Scan", "Scan already in progress")
            return
        self.device_tree.delete(*self.device_tree.get_children())
        self.log(f"Scanning for devices with prefix '{self.prefix.get()}' ...")
        self.scan_thread = threading.Thread(target=self._scan_thread_func, args=(self.prefix.get(),), daemon=True)
        self.scan_thread.start()

    def _scan_thread_func(self, prefix):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            devices = loop.run_until_complete(BleakScanner.discover(timeout=5.0))
            found = []
            for d in devices:
                name = d.name or "<no-name>"
                if prefix:
                    if name.startswith(prefix):
                        found.append((name, d.address))
                else:
                    found.append((name, d.address))
            self.root.after(0, partial(self._populate_devices, found))
            loop.close()
        except Exception as e:
            self.root.after(0, partial(self.log, f"Scan error: {e}"))
            traceback.print_exc()

    def _populate_devices(self, device_list):
        for name, addr in device_list:
            self.device_tree.insert("", "end", values=(name, addr))
        self.log("Scan completed. Found %d device(s)." % len(device_list))

    # Read firmware version
    async def _read_firmware_version(self, client):
        try:
            data = await client.read_gatt_char(VERSION_CHARACTERISTIC_UUID)
            version_str = data.decode(errors="ignore").strip()
            self.root.after(0, partial(self.log, f"Device firmware version read: {version_str}"))
            try:
                return float(version_str)
            except:
                return None
        except Exception:
            return None

    # OTA sending
    async def _send_firmware_async(self, address, file_path, chunk_size, delay_ms, with_response):
        total_sent = 0
        file_size = os.path.getsize(file_path)
        self.root.after(0, partial(self.log, f"Connecting to {address} ..."))

        try:
            async with BleakClient(address) as client:
                self.root.after(0, partial(self.log, f"Connected to {address}"))
                v = await self._read_firmware_version(client)
                if v:
                    self.root.after(0, partial(self.log, f"Device version: {v}"))

                with open(file_path, "rb") as f:
                    start = time.time()
                    while True:
                        if self.stop_event.is_set():
                            self.root.after(0, partial(self.log, "Stop requested. Aborting transfer."))
                            return False

                        chunk = f.read(chunk_size)
                        if not chunk:
                            break

                        await client.write_gatt_char(OTA_CHARACTERISTIC_UUID, chunk, response=with_response)

                        total_sent += len(chunk)
                        percent = (total_sent / file_size) * 100
                        elapsed = time.time() - start
                        speed = int(total_sent / elapsed) if elapsed > 0 else 0

                        self.root.after(0, partial(self.set_progress, percent))
                        status = f"{total_sent}/{file_size} bytes ({int(percent)}%) - {speed} B/s"
                        self.root.after(0, partial(self.set_status, status))

                        if delay_ms:
                            await asyncio.sleep(delay_ms / 1000)

                # EOF packet
                try:
                    await client.write_gatt_char(OTA_CHARACTERISTIC_UUID, b"EOF", response=True)
                except Exception:
                    pass

                self.root.after(0, partial(self.set_progress, 100))
                self.root.after(0, partial(self.set_status, "Completed"))
                self.root.after(0, partial(self.log, "OTA complete."))
                return True

        except Exception as e:
            self.root.after(0, partial(self.log, f"OTA failed: {e}"))
            self.root.after(0, partial(self.set_status, "Error"))
            traceback.print_exc()
            return False

    # Thread runner
    def _ota_thread_func(self, address, file_path, chunk, delay, resp):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self._send_firmware_async(address, file_path, chunk, delay, resp))
        except Exception as e:
            self.root.after(0, partial(self.log, f"OTA thread error: {e}"))
            traceback.print_exc()
        finally:
            self.root.after(0, self._ota_done_ui_update)

    def _ota_done_ui_update(self):
        self.start_btn.configure(state="enabled")
        self.stop_btn.configure(state="disabled")
        self.set_status("Idle")
        self.stop_timer()
        self.log("OTA Finished or stopped.")

    # Start / Stop OTA
    def start_ota(self):
        sel = self.device_tree.selection()
        if not sel:
            messagebox.showerror("Error", "Select a device from the list")
            return

        item = self.device_tree.item(sel[0])
        addr = item["values"][1]

        file_path = self.file_path.get()
        if not file_path or not os.path.isfile(file_path):
            messagebox.showerror("Error", "Select a firmware .bin file")
            return

        # Prepare
        self.stop_event.clear()
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="enabled")
        self.set_progress(0)
        self.set_status("Starting OTA...")
        self.log(
            f"Starting OTA to {addr} with chunk={self.chunk_size.get()} delay={self.delay_ms.get()}ms resp={self.with_response.get()}"
        )

        self.start_timer()

        # Start thread
        self.ota_thread = threading.Thread(
            target=self._ota_thread_func,
            args=(addr, file_path,
                  int(self.chunk_size.get()),
                  int(self.delay_ms.get()),
                  bool(self.with_response.get())),
            daemon=True
        )
        self.ota_thread.start()

    def stop_ota(self):
        if not self.ota_thread or not self.ota_thread.is_alive():
            self.log("No OTA in progress.")
            return
        self.stop_event.set()
        self.set_status("Stopping...")
        self.log("Stop requested; waiting for OTA thread to abort.")
        self.stop_timer()

def main():
    root = Tk()
    app = BLETkOTA(root)
    root.protocol("WM_DELETE_WINDOW", partial(on_close, app, root))
    root.mainloop()

def on_close(app, root):
    try:
        if app.ota_thread and app.ota_thread.is_alive():
            if messagebox.askyesno("Exit", "OTA is in progress. Stop and exit?"):
                app.stop_event.set()
                app.stop_timer()
                app.ota_thread.join(timeout=3)
            else:
                return
    except Exception as e:
        print("Error on close:", e)
    finally:
        root.destroy()

if __name__ == "__main__":
    main()




