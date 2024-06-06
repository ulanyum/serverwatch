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
                st.error(f"Failed to fetch system stats from {server}. Status code: {resp.status}")
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

        async with session.get(f"http://{server}/queue", ssl=False) as resp:
            if resp.status != 200:
                st.error(f"Failed to fetch queue data from {server}. Status code: {resp.status}")
                return None
            queue_data = await resp.json()
            queue_running = len(queue_data["queue_running"])
            queue_pending = len(queue_data["queue_pending"])
            current_task = ""
            workflow = ""
            if queue_running > 0 and "extra_pnginfo" in queue_data["queue_running"][0][2]:
                current_task = queue_data["queue_running"][0][2]["extra_pnginfo"]["workflow"]["nodes"][-1]["widgets_values"][0]
                workflow = queue_data["queue_running"][0][2]["extra_pnginfo"]["workflow"]

        status = "🟢 Online" if resp.status == 200 else "🔴 Offline"
        last_update = datetime.now()

        port = server.split(":")[-1]

        return {
            "port": port,
            "vram_total": vram_total,
            "vram_free": vram_free,
            "queue_running": queue_running,
            "queue_pending": queue_pending,
            "current_task": current_task,
            "workflow": workflow,
            "status": status,
            "last_update": last_update,
            "device_name": f"RTX {device_name}",
        }
    except Exception as e:
        st.error(f"Error connecting to server {server}: {str(e)}")
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
                data["port"],
                f"{data['vram_total']} GB",
                f"{data['vram_free']} GB",
                data["queue_running"],
                data["queue_pending"],
                data["current_task"],
                data["device_name"],
                humanize_time_difference(data["last_update"]),
                data["status"],
                data["workflow"]
            ])

        headers = ["Port", "Total VRAM", "Free VRAM", "Running", "Pending", "Task", "Device", "Update", "Status", "Workflow"]
        st.table(pd.DataFrame(table_data, columns=headers))
    else:
        st.warning("No server data available.")

def main():
    st.title("ComfyUI Server Monitor")

    if "servers" not in st.session_state:
        st.session_state.servers = []

    server_input = st.text_area("Enter server addresses (one per line)", value="\n".join(st.session_state.servers))
    servers = [server.strip() for server in server_input.split("\n") if server.strip()]

    if st.button("Add Servers"):
        st.session_state.servers = servers
        st.experimental_rerun()

    if st.button('Update'):
        update_data(st.session_state.servers)

if __name__ == "__main__":
    main()
