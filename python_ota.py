import asyncio
import os
from bleak import BleakClient, BleakScanner
from bleak.exc import BleakError, BleakCharacteristicNotFoundError

# UUIDs from ESP32
OTA_SERVICE_UUID = "12345678-1234-1234-1234-1234567890ab"
OTA_CHARACTERISTIC_UUID = "abcd1234-5678-90ab-cdef-1234567890ab"
VERSION_CHARACTERISTIC_UUID = "00002a26-0000-1000-8000-00805f9b34fb"  # Standard firmware version UUID

# Config
DEVICE_NAME_PREFIX = "NSGW719903"
FIRMWARE_PATH = "/home/mstuser4/Desktop/node_code_test9.0.ino.esp32.bin"
VERSION_THRESHOLD = 9.2
CHUNK_SIZE = 512
MAX_RETRIES = 5
RETRY_DELAY = 10


async def wait_for_device(name_prefix, timeout=30):
    print(f"Scanning for BLE devices starting with '{name_prefix}'...")
    for _ in range(timeout):
        devices = await BleakScanner.discover()
        for d in devices:
            if d.name and d.name.startswith(name_prefix):
                print(f"Found device: {d.name} - {d.address}")
                return d.address
        await asyncio.sleep(1)
    raise TimeoutError(f"BLE device with name starting '{name_prefix}' not found within {timeout} seconds.")


async def read_firmware_version(client):
    try:
        version_data = await client.read_gatt_char(VERSION_CHARACTERISTIC_UUID)
        version_str = version_data.decode().strip()
        print(f"Firmware version read from device: {version_str}")
        return float(version_str)
    except Exception as e:
        # Gracefully handle missing characteristic (or any read error)
        if "Characteristic" in str(e) and "not found" in str(e):
            print("Warning: Firmware version characteristic not found. Proceeding without it.")
            return None  # or use a default like 0.0 if needed
        else:
            raise RuntimeError(f"Failed to read firmware version: {e}")


async def send_firmware(client):
    total_bytes_sent = 0
    try:
        with open(FIRMWARE_PATH, "rb") as f:
            while True:
                chunk = f.read(CHUNK_SIZE)
                if not chunk:
                    break
                await client.write_gatt_char(OTA_CHARACTERISTIC_UUID, chunk)
                total_bytes_sent += len(chunk)

                print(f"Sent {len(chunk)} bytes (Total: {total_bytes_sent})")
                await asyncio.sleep(0.0001)

        print(f"\nFirmware sent successfully! Total bytes sent: {total_bytes_sent}")

        # Send EOF marker
        print("Sending EOF marker...")
        await client.write_gatt_char(OTA_CHARACTERISTIC_UUID, b"EOF")
        print("EOF sent. Waiting for ESP to restart...")
        await asyncio.sleep(RETRY_DELAY)
        
    except Exception as e:
        raise RuntimeError(f"Firmware transmission failed: {e}")


async def update_firmware(address):
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            async with BleakClient(address) as client:
                print(f"Connected to {address} (Attempt {attempt})")
                # Check version
                # current_version = await read_firmware_version(client)
                # if current_version >= VERSION_THRESHOLD:
                #     print(f"Version {current_version} >= {VERSION_THRESHOLD}. Skipping OTA.")
                #     return

                # print(f"Version {current_version} < {VERSION_THRESHOLD}. Starting OTA...")
                # await send_firmware(client)
                # return  # success

                # Check version
                current_version = await read_firmware_version(client)
                if current_version == VERSION_THRESHOLD:
                    print(f"Version {current_version} == {VERSION_THRESHOLD}. Skipping OTA.")
                    return
                else:
                    print(f"Version {current_version} != {VERSION_THRESHOLD}. Starting OTA...")
                    await send_firmware(client)
                    return  # success


        except (BleakCharacteristicNotFoundError, BleakError, Exception) as e:
            print(f"Attempt {attempt} failed: {e}")
            if attempt < MAX_RETRIES:
                print(f"Retrying in {RETRY_DELAY} seconds...\n")
                await asyncio.sleep(RETRY_DELAY)
            else:
                print("Maximum retry attempts reached. Firmware update failed.")
                raise


async def main():
    try:
        address = await wait_for_device(DEVICE_NAME_PREFIX)
        await update_firmware(address)
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
