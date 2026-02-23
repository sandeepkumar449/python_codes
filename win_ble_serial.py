# sudo apt install bluetooth libbluetooth-dev

import asyncio
import threading
import tkinter as tk
from tkinter import scrolledtext, messagebox
from datetime import datetime

# ─── Bleak (BLE) ────────────────────────────────────────────────────────────
try:
    from bleak import BleakScanner, BleakClient
    HAS_BLEAK = True
except ImportError:
    HAS_BLEAK = False
    print("WARNING: bleak not installed → BLE support disabled")

# ─── pybluez (Classic BT) ───────────────────────────────────────────────────
# try:
#     import bluetooth
#     HAS_PYBLUEZ = True
# except ImportError:
#     HAS_PYBLUEZ = False
#     print("WARNING: pybluez not installed → Classic BT support disabled")
HAS_PYBLUEZ = False

# Globals
notify_char_uuid = None
client = None
loop = None
current_font_size = 12

# ─── Button factory ─────────────────────────────────────────────────────────
def create_button(parent, text, command, bg="#3a3a4d", width=None):
    btn = tk.Button(
        parent,
        text=text,
        command=command,
        bg=bg,
        fg="white",
        disabledforeground="white",         # ← key line
        activebackground="#505070",
        activeforeground="white",
        padx=12 if width is None else 10,
        pady=6,
        bd=0,
        relief="flat",
        font=("Arial", 11, "bold"),
        cursor="hand2",
        width=width,
        highlightthickness=0,
    )
    btn.bind("<ButtonPress-1>", lambda e: btn.config(bg="#505070"))
    btn.bind("<ButtonRelease-1>", lambda e: btn.config(bg=bg))
    return btn

# ─── Log helper ─────────────────────────────────────────────────────────────
def add_log(message, tag="info"):
    log_box.config(state="normal")
    ts = datetime.now().strftime("[%H:%M:%S] ") if timestamp_enabled.get() else ""
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
    f = ("Courier", current_font_size)
    log_box.configure(font=f)
    for tag in ["rx", "tx", "info"]:
        log_box.tag_config(tag, font=f)

# ─── BLE functions (unchanged core logic) ───────────────────────────────────
async def scan_ble():
    if not HAS_BLEAK: return []
    try:
        return await BleakScanner.discover(timeout=5.0)
    except Exception as e:
        add_log(f"BLE scan error: {e}", "info")
        return []

async def find_characteristics(cl):
    global notify_char_uuid
 
    services = cl.services   # ✅ new API
 
    for s in services:
        for c in s.characteristics:
            props = c.properties
            if ("write" in props or "write-without-response" in props) and "notify" in props:
                notify_char_uuid = c.uuid
                return c.uuid
 
    return None

def notification_handler(sender, data):
    try:
        text = data.decode(errors="ignore").strip()
    except:
        text = data.hex()
    add_log(f"[RX] {text}", "rx")

async def connect_to_device(addr):
    global client
    if not HAS_BLEAK:
        return False, "bleak not available"
    client = BleakClient(addr)
    try:
        await client.connect()
        await asyncio.sleep(0.5)
        if not client.is_connected:
            return False, "Connection failed"
        char_uuid = await find_characteristics(client)
        if not char_uuid:
            return False, "No writable+notify characteristic found"
        await client.start_notify(char_uuid, notification_handler)
        return True, char_uuid
    except Exception as e:
        return False, str(e)

async def disconnect_device():
    global client, notify_char_uuid
    if client and client.is_connected:
        await client.disconnect()
    client = None
    notify_char_uuid = None

async def send_data(msg):
    if client and notify_char_uuid and client.is_connected:
        await client.write_gatt_char(notify_char_uuid, msg.encode())
        add_log(f"[TX] {msg}", "tx")

# ─── Classic scan ───────────────────────────────────────────────────────────
def scan_classic():
    if not HAS_PYBLUEZ: return []
    try:
        return bluetooth.discover_devices(duration=8, lookup_names=True, flush_cache=True, lookup_class=False)
    except Exception as e:
        add_log(f"Classic BT scan error: {e}", "info")
        return []

# ─── GUI actions ────────────────────────────────────────────────────────────
def on_scan():
    device_list.delete(0, tk.END)
    name_filter = search_entry.get().strip().lower()
    if HAS_PYBLUEZ:
        threading.Thread(target=do_classic_scan, args=(name_filter,), daemon=True).start()
    if HAS_BLEAK:
        run_async(scan_and_load_ble(name_filter))

def do_classic_scan(name_filter):
    for addr, name in scan_classic():
        name = name or "Unknown"
        if name_filter and name_filter not in name.lower():
            continue
        window.after(0, lambda t=f"{name} ({addr}) [Classic]": device_list.insert(tk.END, t))
    window.after(0, lambda: add_log("[Classic BT scan finished]", "info"))

async def scan_and_load_ble(name_filter):
    for d in await scan_ble():
        name = d.name or "Unknown"
        if name_filter and name_filter not in name.lower():
            continue
        window.after(0, lambda t=f"{name} ({d.address}) [BLE]": device_list.insert(tk.END, t))
    window.after(0, lambda: add_log("[BLE scan finished]", "info"))

def on_connect():
    sel = device_list.curselection()
    if not sel: return
    text = device_list.get(sel[0])
    if "[Classic]" in text:
        messagebox.showinfo("Not implemented", "Classic (RFCOMM) connection not yet supported.")
        return
    try:
        addr = text.rsplit("(", 1)[1].split(")")[0].strip()
        run_async(connect_and_enable(addr))
    except:
        messagebox.showerror("Error", "Cannot parse device address")

async def connect_and_enable(addr):
    ok, msg = await connect_to_device(addr)
    if not ok:
        window.after(0, lambda m=msg: messagebox.showerror("Connection failed", m))
        return
    send_btn.config(state=tk.NORMAL)
    disconnect_btn.config(state=tk.NORMAL)
    connect_btn.config(state=tk.DISABLED)
    add_log(f"[Connected to {addr}]", "info")

def on_disconnect():
    run_async(disconnect_and_update())

async def disconnect_and_update():
    await disconnect_device()
    send_btn.config(state=tk.DISABLED)
    disconnect_btn.config(state=tk.DISABLED)
    connect_btn.config(state=tk.NORMAL)
    add_log("[Disconnected]", "info")

def on_send():
    msg = msg_entry.get().strip()
    if msg:
        run_async(send_data(msg))
        msg_entry.delete(0, tk.END)

def cmd_send(msg):
    run_async(send_data(msg))

def clear_logs():
    log_box.config(state="normal")
    log_box.delete("1.0", tk.END)
    log_box.config(state="disabled")

def close_app():
    if loop and loop.is_running():
        loop.call_soon_threadsafe(loop.stop)
    window.destroy()

# ─── Async bridge ───────────────────────────────────────────────────────────
def run_async(coro):
    if loop and loop.is_running():
        asyncio.run_coroutine_threadsafe(coro, loop)

def start_asyncio_loop():
    global loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_forever()

# ─── GUI ────────────────────────────────────────────────────────────────────
window = tk.Tk()
window.title("WIN Clasic + Ble Serial Terminal")
window.geometry("820x720")
window.configure(bg="#1f1f2e")

timestamp_enabled = tk.BooleanVar(value=True)

# Top controls
frame_top = tk.Frame(window, bg="#1f1f2e")
frame_top.pack(pady=10, padx=10, fill="x")

search_entry = tk.Entry(frame_top, width=34, bg="#2b2b38", fg="white",
                        insertbackground="white", font=("Arial", 11),
                        relief="flat")
search_entry.pack(side="left", padx=(0,6))

create_button(frame_top, "Scan", on_scan, bg="#28a745").pack(side="left", padx=4)
connect_btn    = create_button(frame_top, "Connect",    on_connect,    bg="#007bff")
disconnect_btn = create_button(frame_top, "Disconnect", on_disconnect, bg="#dc3545")
clear_btn      = create_button(frame_top, "Clear",      clear_logs,    bg="#6c757d")

connect_btn.pack   (side="left", padx=4)
disconnect_btn.pack(side="left", padx=4)
clear_btn.pack     (side="left", padx=4)

# Device list
device_frame = tk.LabelFrame(window, text=" Devices ", bg="#1f1f2e", fg="#cccccc",
                             font=("Arial", 10, "bold"), padx=6, pady=6)
device_frame.pack(padx=10, pady=(0,8), fill="both", expand=False)

device_list = tk.Listbox(device_frame, bg="#252535", fg="white",
                         selectbackground="#0066cc", selectforeground="white",
                         font=("Arial", 11), height=8)
device_list.pack(fill="both", expand=True, padx=2, pady=2)

# Send area
frame_send = tk.Frame(window, bg="#1f1f2e")
frame_send.pack(pady=6, padx=10, fill="x")

msg_entry = tk.Entry(frame_send, bg="#252535", fg="#e0e0ff",
                     insertbackground="#bb86fc", font=("Arial", 12),
                     relief="flat")
msg_entry.pack(side="left", fill="x", expand=True, padx=(0,8), ipady=4)

send_btn = create_button(frame_send, "Send", on_send, bg="#17a2b8", width=10)
send_btn.pack(side="left")
send_btn.config(state=tk.DISABLED)

# Command buttons
cmd_frame = tk.Frame(window, bg="#1f1f2e")
cmd_frame.pack(pady=8, padx=10, fill="x")

for text in ["VERSION", "GETBATTERY", "1", "2", "3", "4"]:
    create_button(cmd_frame, text, lambda m=text: cmd_send(m), bg="#17a2b8").pack(side="left", padx=5)

# Log frame
log_frame = tk.LabelFrame(window, text=" Log ", bg="#1f1f2e", fg="#cccccc",
                          font=("Arial", 10, "bold"), padx=6, pady=6)
log_frame.pack(padx=10, pady=(0,10), fill="both", expand=True)

options = tk.Frame(log_frame, bg="#1f1f2e")
options.pack(fill="x", pady=(0,4))

font_frame = tk.Frame(options, bg="#1f1f2e")
font_frame.pack(side="left")

create_button(font_frame, "A+", increase_font_size, bg="#444444", width=4).pack(side="left", padx=3)
create_button(font_frame, "A−", decrease_font_size, bg="#444444", width=4).pack(side="left", padx=3)

tk.Checkbutton(options, text="Timestamps", variable=timestamp_enabled,
               bg="#1f1f2e", fg="white", selectcolor="#3a3a4d",
               activebackground="#1f1f2e", font=("Arial", 10)).pack(side="right")

log_box = scrolledtext.ScrolledText(log_frame, bg="#181822", fg="#e0e0ff",
                                    font=("Courier", current_font_size),
                                    state="disabled", wrap="word")
log_box.pack(fill="both", expand=True, padx=2, pady=2)

log_box.tag_config("rx",   foreground="#40c4ff")
log_box.tag_config("tx",   foreground="#ffd740")
log_box.tag_config("info", foreground="#ff6e40")

# Start asyncio
threading.Thread(target=start_asyncio_loop, daemon=True).start()

window.protocol("WM_DELETE_WINDOW", close_app)
msg_entry.focus_set()
window.mainloop()