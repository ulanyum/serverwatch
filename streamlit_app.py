import asyncio
import aiohttp
import streamlit as st
import pandas as pd
from datetime import datetime

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
        async with session.get(f"http://{server}/system_stats", ssl=False) as resp:
            if resp.status != 200:
                return None
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
            python_version = stats_data["system"]["python_version"].split(" ")[0]

        async with session.get(f"http://{server}/queue", ssl=False) as resp:
            if resp.status != 200:
                return None
            queue_data = await resp.json()
            queue_running = len(queue_data["queue_running"])
            queue_pending = len(queue_data["queue_pending"])
            current_task = ""
            if queue_running > 0 and "extra_pnginfo" in queue_data["queue_running"][0][2]:
                current_task = queue_data["queue_running"][0][2]["extra_pnginfo"]["workflow"]["nodes"][-1]["widgets_values"][0]

        status = "🟢 Online" if resp.status == 200 else "🔴 Offline"
        last_update = datetime.now()

        return {
            "server": server,
            "vram_total": vram_total,
            "vram_free": vram_free,
            "queue_running": queue_running,
            "queue_pending": queue_pending,
            "current_task": current_task,
            "status": status,
            "last_update": last_update,
            "device_name": f"RTX {device_name}",
            "python_version": python_version
        }
    except Exception as e:
        print(f"Error connecting to server {server}: {str(e)}")
        return None

async def get_all_server_data(servers):
    async with aiohttp.ClientSession() as session:
        tasks = [get_server_data(session, server) for server in servers]
        server_data = await asyncio.gather(*tasks)
        return [data for data in server_data if data is not None]

def update_data(servers):
    server_data = asyncio.run(get_all_server_data(servers))

    if server_data:
        table_data = []
        for data in server_data:
            table_data.append([
                data["server"],
                f"{data['vram_total']} GB",
                f"{data['vram_free']} GB",
                data["queue_running"],
                data["queue_pending"],
                data["current_task"],
                data["device_name"],
                data["python_version"],
                humanize_time_difference(data["last_update"]),
                data["status"]
            ])

        headers = ["Server", "Total VRAM", "Free VRAM", "Running", "Pending", "Task", "Device", "Python", "Update", "Status"]
        st.table(pd.DataFrame(table_data, columns=headers))
    else:
        st.warning("No server data available.")

def main():
    st.title("ComfyUI Server Monitor")

    server_input = st.text_area("Enter server addresses (one per line)")
    servers = [server.strip() for server in server_input.split("\n") if server.strip()]

    if st.button('Güncelle'):
        update_data(servers)

if __name__ == "__main__":
    main()
