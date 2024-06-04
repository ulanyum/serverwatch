import asyncio
import aiohttp
import json
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import time
import os

SERVERS_FILE = "servers.json"

def load_servers():
    if os.path.exists(SERVERS_FILE):
        with open(SERVERS_FILE, "r") as file:
            return json.load(file)
    else:
        return []

def save_servers(servers):
    with open(SERVERS_FILE, "w") as file:
        json.dump(servers, file)

def humanize_time_difference(update_time):
    now = datetime.now()
    diff = now - update_time

    seconds = diff.total_seconds()
    if seconds < 60:
        return f"{int(seconds)} sn önce"
    elif seconds < 3600:
        minutes = seconds // 60
        return f"{int(minutes)} dk önce"
    elif seconds < 86400:
        hours = seconds // 3600
        return f"{int(hours)} saat önce"
    else:
        days = seconds // 86400
        return f"{int(days)} gün önce"

async def get_server_data(session, server):
    try:
        # Port numarasını al
        port = server.split(":")[-1]

        # /system_stats endpoint'inden veri al
        async with session.get(f"http://{server}/system_stats", ssl=False) as resp:
            stats_data = await resp.json()
            vram_total = round(stats_data["devices"][0]["vram_total"] / (1024 ** 3), 2)
            vram_free = round(stats_data["devices"][0]["vram_free"] / (1024 ** 3), 2)
            device_name_full = stats_data["devices"][0]["name"]
            if "RTX" in device_name_full:
                device_name = device_name_full.split("RTX")[1][:6].strip()
            elif "RXT" in device_name_full:
                device_name = device_name_full.split("RXT")[1][:6].strip()
            else:
                device_name = device_name_full

        # /queue endpoint'inden veri al
        async with session.get(f"http://{server}/queue", ssl=False) as resp:
            queue_data = await resp.json()
            queue_running = len(queue_data["queue_running"])
            queue_pending = len(queue_data["queue_pending"])
            current_task = ""
            if queue_running > 0 and "extra_pnginfo" in queue_data["queue_running"][0][2]:
                current_task = queue_data["queue_running"][0][2]["extra_pnginfo"]["workflow"]["nodes"][-1]["widgets_values"][0]

        # Sunucunun durumunu kontrol et
        status = "🟢 Online" if resp.status == 200 else "🔴 Offline"

        # Son güncelleme zamanını al
        last_update = datetime.now()

        return {
            "port": port,
            "vram_total": vram_total,
            "vram_free": vram_free,
            "queue_running": queue_running,
            "queue_pending": queue_pending,
            "current_task": current_task,
            "status": status,
            "last_update": last_update,
            "device_name": f"RTX {device_name}"
        }
    except Exception as e:
        print(f"Error connecting to server {server}: {str(e)}")
        return None

async def get_all_server_data(servers):
    async with aiohttp.ClientSession() as session:
        tasks = []
        for server in servers:
            tasks.append(asyncio.ensure_future(get_server_data(session, server)))

        server_data = await asyncio.gather(*tasks)
        return [data for data in server_data if data is not None]

def update_data():
    # Sunucu listesini dosyadan yükle
    servers = load_servers()

    server_data = asyncio.run(get_all_server_data(servers))

    if len(server_data) > 0:
        # Streamlit tablosunu oluştur
        table_data = []
        for data in server_data:
            table_data.append([
                data["port"],
                f"{data['vram_total']} GB",
                f"{data['vram_free']} GB",
                data["queue_running"],
                data["queue_pending"],
                data["current_task"],
                data["device_name"],
                humanize_time_difference(data["last_update"]),
                data["status"]
            ])

        # Tablo başlıklarını belirle
        headers = ["Port", "Total VRAM", "Free VRAM", "Running", "Pending", "Task", "Device", "Update", "Status"]

        # Tabloyu görüntüle
        st.table(pd.DataFrame(table_data, columns=headers))
    else:
        st.warning("No server data available.")

def add_servers():
    if st.button("Add Server"):
        with st.form("add_server_form"):
            server_addresses = st.text_input("Enter server addresses (comma-separated)")
            submit_button = st.form_submit_button("Add Servers")
            if submit_button:
                if server_addresses.strip():
                    servers = load_servers()
                    new_servers = [server.strip() for server in server_addresses.split(",") if server.strip()]
                    servers.extend(server for server in new_servers if server not in servers)
                    save_servers(servers)
                st.experimental_rerun()

def main():
    st.title("ComfyUI Server Monitor")

    # Sunucu ekleme butonunu görüntüle
    add_servers()

    if st.button('Update'):
        update_data()

    # İlk yükleme sırasında verileri güncelle
    update_data()

if __name__ == "__main__":
    main()
