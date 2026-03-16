import asyncio
import threading
import tkinter as tk
from tkinter import scrolledtext, messagebox
from bleak import BleakScanner, BleakClient
import requests
import json

notify_char_uuid = None
client = None
loop = None
rx_buffer = ""
rx_timer = None
RX_TIMEOUT = 0.5  # seconds
API_URL = "https://api.ms-tech.in/v26/meterdata"
dcuid = ""

# ---------------- Helper Button Function ----------------
def create_button(parent, text, command, bg="#3a3a4d"):
    return tk.Button(
        parent,
        text=text,
        command=command,
        bg=bg,
        fg="white",
        activebackground="#505065",
        activeforeground="white",
        padx=10,
        pady=5,
        bd=0,
        relief="flat",
        font=("Arial Black", 11, "bold"),
        cursor="hand2"
    )

# ---------------- FONT SIZE CONTROL ------------------
current_font_size = 12

def add_log(message, tag="info"):
    log_box.config(state="normal")
    if timestamp_enabled.get():
        from datetime import datetime
        ts = datetime.now().strftime("[%H:%M:%S] ")
    else:
        ts = ""
    log_box.insert("end", ts + message + "\n", tag)
    log_box.see("end")
    log_box.config(state="disabled")

def increase_font_size():
    global current_font_size
    current_font_size += 1
    apply_font_size()

def decrease_font_size():
    global current_font_size
    if current_font_size > 6:
        current_font_size -= 1
        apply_font_size()

def apply_font_size():
    log_box.configure(font=("Courier", current_font_size))
    log_box.tag_config("rx",   font=("Courier", current_font_size))
    log_box.tag_config("tx",   font=("Courier", current_font_size))
    log_box.tag_config("info", font=("Courier", current_font_size))

# ---------------- BLE FUNCTIONS ------------------
async def scan_ble():
    return await BleakScanner.discover(timeout=4)

async def find_characteristics(client):
    global notify_char_uuid
    services = await client.get_services()
    for s in services:
        for c in s.characteristics:
            if ("write" in c.properties or "write-without-response" in c.properties) and "notify" in c.properties:
                notify_char_uuid = c.uuid
                return c.uuid
    return None

def flush_rx_buffer():
    global rx_buffer
    if not rx_buffer:
        return
    
    if rx_buffer:
        add_log(f"[RX] {rx_buffer.strip()}", "rx")
        
    if "7e" in rx_buffer:
        full_data = rx_buffer.strip()
        rx_buffer = ""  # Clear immediately
        payload = {"data": dcuid + " " + full_data}
        headers = {"Content-Type": "application/json"}
        try:
            response = requests.post(API_URL, json=payload, headers=headers, timeout=15)
            add_log(f"Status Code: {response.status_code}")
            try:
                json_response = response.json()
                formatted = json.dumps(json_response, indent=4)
            except:
                formatted = response.text
            window.after(0, lambda: add_log(formatted, "info"))
        except Exception as e:
            add_log(f"API Error: {str(e)}")
    rx_buffer = ""

def notification_handler(sender, data):
    global rx_buffer, rx_timer
    try:
        chunk = data.decode(errors="ignore")
    except Exception:
        chunk = data.hex()
    rx_buffer += chunk
    
    if rx_timer is not None:
        rx_timer.cancel()
    rx_timer = threading.Timer(RX_TIMEOUT, flush_rx_buffer)
    rx_timer.start()

async def connect_to_device(addr):
    global client
    client = BleakClient(addr)
    await client.connect()
    if not client.is_connected:
        return False, "Connection failed"
    char_uuid = await find_characteristics(client)
    if not char_uuid:
        return False, "Writable characteristic missing"
    await client.start_notify(char_uuid, notification_handler)
    return True, char_uuid

async def disconnect_device():
    global client, notify_char_uuid
    if client and client.is_connected:
        await client.disconnect()
    client = None
    notify_char_uuid = None

async def send_data(msg):
    if client and notify_char_uuid:
        await client.write_gatt_char(notify_char_uuid, msg.encode())
        add_log(f"[TX] {msg}", "tx")

# ---------------- ASYNC BRIDGE ------------------
def run_async(coro):
    asyncio.run_coroutine_threadsafe(coro, loop)

def start_asyncio_loop():
    global loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_forever()

# ---------------- GUI FUNCTIONS ------------------
def on_scan():
    device_list.delete(0, tk.END)
    name_filter = search_entry.get().strip()
    run_async(scan_and_load(name_filter))

async def scan_and_load(name_filter):
    devices = await scan_ble()
    for d in devices:
        name = d.name or "Unknown"
        if name_filter and name_filter.lower() not in name.lower():
            continue
        device_list.insert(tk.END, f"{name} ({d.address})")

def on_connect():
    global dcuid
    sel = device_list.curselection()
    if not sel:
        return
    text = device_list.get(sel[0])
    _, addr = text.rsplit("(", 1)
    addr = addr.replace(")", "")
    dcuid = text.split(" ")[0]
    run_async(connect_and_enable(addr, dcuid))

async def connect_and_enable(addr, dcuid):
    ok, msg = await connect_to_device(addr)
    if not ok:
        window.after(0, lambda: messagebox.showerror("BLE", msg))
        return
    send_btn.config(state=tk.NORMAL)
    disconnect_btn.config(state=tk.NORMAL)
    connect_btn.config(state=tk.DISABLED)
    add_log(f"[Connected to {dcuid}]", "info")

def on_disconnect():
    run_async(disconnect_and_update())

async def disconnect_and_update():
    await disconnect_device()
    send_btn.config(state=tk.DISABLED)
    disconnect_btn.config(state=tk.DISABLED)
    connect_btn.config(state=tk.NORMAL)
    add_log("[Disconnected from device]", "info")

def on_send():
    msg = msg_entry.get()
    if msg.strip() == "":
        return
    run_async(send_data(msg))
    msg_entry.delete(0, tk.END)
    msg_entry.focus_set()

def clear_logs():
    log_box.configure(state="normal")
    log_box.delete("1.0", tk.END)
    log_box.configure(state="disabled")

def close_app():
    if loop:
        loop.call_soon_threadsafe(loop.stop)
    window.destroy()

def cmd_send(default_msg):
    run_async(send_data(default_msg))

# ────────────────────────────────────────────────
#                  BUILD GUI
# ────────────────────────────────────────────────

window = tk.Tk()
window.title("BLE SERIAL TERMINAL")
window.geometry("980x680")           # wider to accommodate side-by-side layout
window.configure(bg="#1f1f2e")
window.minsize(900, 600)

# ─── Main horizontal paned layout ───
main_container = tk.Frame(window, bg="#1f1f2e")
main_container.pack(fill="both", expand=True, padx=8, pady=8)

# LEFT SIDE – controls + devices + send + commands
left_frame = tk.Frame(main_container, bg="#1f1f2e", width=380)
left_frame.pack(side="left", fill="y", padx=(0, 8))

# TOP CONTROLS (search + buttons)
frame_btns = tk.Frame(left_frame, bg="#1f1f2e")
frame_btns.pack(fill="x", pady=(0, 8))

search_entry = tk.Entry(frame_btns, width=28, bg="#2b2b3c", fg="white",
                        insertbackground="white", font=("Arial", 11))
search_entry.pack(side="left", padx=(0, 6))

scan_btn = create_button(frame_btns, "Scan", on_scan, bg="#28a745")
scan_btn.pack(side="left", padx=4)

connect_btn = create_button(frame_btns, "Connect", on_connect, bg="#007bff")
connect_btn.pack(side="left", padx=4)

disconnect_btn = create_button(frame_btns, "Disconnect", on_disconnect, bg="#dc3545")
disconnect_btn.pack(side="left", padx=4)

clear_btn = create_button(frame_btns, "Clear", clear_logs, bg="#6c757d")
clear_btn.pack(side="left", padx=4)

# Device list
# device_frame = tk.LabelFrame(left_frame, text="Discovered Devices",
#                               bg="#1f1f2e", fg="white",
#                               font=("Arial", 11, "bold"))
# device_frame.pack(fill="both", expand=True, pady=(0, 10))

# # ── Medium-large size Listbox ────────────────────────────────
# device_list = tk.Listbox(
#     device_frame,
#     width=55,           # was 45 → increased to 55 (wider)
#     height=14,          # was 10 → increased to 14 (taller)
#     bg="#2b2b3c",
#     fg="white",
#     selectbackground="#007ACC",
#     selectforeground="white",
#     font=("Arial", 12),
#     activestyle="none",     # no dotted line around selected item
#     borderwidth=0,
#     highlightthickness=0
# )
# device_list.pack(padx=8, pady=8, fill="both", expand=True)
# ── Smaller Device Frame ────────────────────────────────
device_frame = tk.LabelFrame(
    left_frame,
    text="Discovered Devices",
    bg="#1f1f2e",
    fg="white",
    font=("Arial", 10, "bold")   # smaller title font
)

device_frame.pack(
    fill="none",        # prevent stretching
    expand=False,
    pady=(0, 8),
    padx=5
)

# ── Smaller Listbox ────────────────────────────────
device_list = tk.Listbox(
    device_frame,
    width=65,
    height=18,
    bg="#2b2b3c",
    fg="white",
    selectbackground="#007ACC",
    selectforeground="white",
    font=("Arial", 12),
    activestyle="none",
    borderwidth=0,
    highlightthickness=0
)
# device_list = tk.Listbox(
#     device_frame,
#     width=83,           # reduced from 55
#     height=24,           # reduced from 14
#     bg="#2b2b3c",
#     fg="white",
#     selectbackground="#007ACC",
#     selectforeground="white",
#     font=("Arial", 15),   # reduced font size
#     activestyle="none",
#     borderwidth=0,
#     highlightthickness=0
# )

device_list.pack(
    padx=5,
    pady=5,
    fill="none",
    expand=False
)
# device_frame = tk.LabelFrame(left_frame, text="Discovered Devices", bg="#1f1f2e", fg="white",
#                               font=("Arial", 11, "bold"))
# device_frame.pack(fill="both", expand=True, pady=(0, 10))

# device_list = tk.Listbox(device_frame, width=45, height=10, bg="#2b2b3c", fg="white",
#                          selectbackground="#007ACC", font=("Arial", 12), activestyle="none")
# device_list.pack(padx=6, pady=6, fill="both", expand=True)

# Message send area
frame_send = tk.Frame(left_frame, bg="#1f1f2e")
frame_send.pack(fill="x", pady=(0, 10))

msg_entry = tk.Entry(frame_send, width=45, bg="#2b2b3c", fg="white",
                     insertbackground="white", font=("Arial", 11))
msg_entry.pack(side="left", padx=(0, 6), fill="x", expand=True)

send_btn = create_button(frame_send, "Send", on_send, bg="#28a745")
send_btn.pack(side="left")

# Command buttons
cmd_frame = tk.Frame(left_frame, bg="#1f1f2e")
cmd_frame.pack(fill="x", pady=4)

CMD_BUTTONS = [
    ("READINST",  "#17a2b8"),
    ("GETFSLIST", "#17a2b8"),
    ("READBILL",  "#17a2b8"),
    ("VERSION",   "#17a2b8"),
    ("POST", "#17a2b8"),
]

for i, (text, color) in enumerate(CMD_BUTTONS):
    btn = create_button(cmd_frame, text, lambda m=text: cmd_send(m), bg=color)
    btn.grid(row=0, column=i, padx=4, pady=2, sticky="ew")
cmd_frame.columnconfigure(tuple(range(len(CMD_BUTTONS))), weight=1)

# ─── RIGHT SIDE – Logs ───
right_frame = tk.Frame(main_container, bg="#1f1f2e")
right_frame.pack(side="right", fill="both", expand=True)

log_frame = tk.LabelFrame(right_frame, text="BLE Logs", bg="#1f1f2e", fg="white",
                          font=("Arial", 11, "bold"))
log_frame.pack(fill="both", expand=True)

# Font size + Timestamp controls
options_frame = tk.Frame(log_frame, bg="#1f1f2e")
options_frame.pack(fill="x", padx=6, pady=(4, 2))

font_btn_frame = tk.Frame(options_frame, bg="#1f1f2e")
font_btn_frame.pack(side="left")

tk.Button(font_btn_frame, text="A+", command=increase_font_size,
          bg="#444", fg="white", bd=0, padx=10, pady=3).pack(side="left", padx=3)
tk.Button(font_btn_frame, text="A−", command=decrease_font_size,
          bg="#444", fg="white", bd=0, padx=10, pady=3).pack(side="left", padx=3)

timestamp_enabled = tk.BooleanVar(value=True)
timestamp_chk = tk.Checkbutton(
    options_frame,
    text="Show timestamps",
    variable=timestamp_enabled,
    bg="#1f1f2e", fg="white",
    selectcolor="#444",
    activebackground="#1f1f2e",
    activeforeground="white",
    font=("Arial", 10)
)
timestamp_chk.pack(side="right")

# Log box
log_box = scrolledtext.ScrolledText(
    log_frame,
    bg="#2b2b3c",
    fg="white",
    font=("Courier", current_font_size),
    state="disabled",
    wrap="word"
)
log_box.pack(padx=6, pady=(0, 6), fill="both", expand=True)

log_box.tag_config("rx",   foreground="#00cfff")
log_box.tag_config("tx",   foreground="#ffc107")
log_box.tag_config("info", foreground="#ff6f61")

# ─── Start asyncio thread ───
threading.Thread(target=start_asyncio_loop, daemon=True).start()

# ─── Window close handler ───
window.protocol("WM_DELETE_WINDOW", close_app)

msg_entry.focus_set()
window.mainloop()