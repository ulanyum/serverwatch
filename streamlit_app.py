import asyncio
import aiohttp
import streamlit as st
import pandas as pd
from datetime import datetime
import time
import altair as alt

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

def get_all_server_data(servers):
    async def get_all_server_data_async(servers):
        async with aiohttp.ClientSession() as session:
            tasks = [get_server_data(session, server) for server in servers]
            server_data = await asyncio.gather(*tasks)
            return [data for data in server_data if data is not None]

    return asyncio.run(get_all_server_data_async(servers))

def display_server_details(server_data):
    st.header(f"Server Details - Port: {server_data['port']}")

    # Sunucu bilgilerini göster
    st.subheader("Server Information")
    st.write(f"- Device: {server_data['device_name']}")
    st.write(f"- Status: {server_data['status']}")
    st.write(f"- Last Update: {humanize_time_difference(server_data['last_update'])} ago")

    # VRAM kullanımını göster
    st.subheader("VRAM Usage")
    vram_data = pd.DataFrame({
        'VRAM (GB)': [server_data['vram_total'] - server_data['vram_free'], server_data['vram_free']],
        'Type': ['Used', 'Free']
    })
    vram_chart = alt.Chart(vram_data).mark_bar().encode(
        x=alt.X('VRAM (GB)'),
        y=alt.Y('Type', sort=alt.EncodingSortField(field='VRAM (GB)', order='descending')),
        color=alt.Color('Type', scale=alt.Scale(range=['#FF5733', '#36A2EB']))
    )
    st.altair_chart(vram_chart, use_container_width=True)

    # Kuyruk durumunu göster
    st.subheader("Queue Status")
    queue_data = pd.DataFrame({
        'Queue': ['Running', 'Pending'],
        'Count': [server_data['queue_running'], server_data['queue_pending']]
    })
    queue_chart = alt.Chart(queue_data).mark_bar().encode(
        x=alt.X('Count'),
        y=alt.Y('Queue'),
        color=alt.Color('Queue', scale=alt.Scale(range=['#36A2EB', '#FFCE56']))
    )
    st.altair_chart(queue_chart, use_container_width=True)

    # Geçerli görevi ve iş akışını göster
    st.subheader("Current Task")
    st.write(f"- Task: {server_data['current_task']}")
    st.write(f"- Workflow: {server_data['workflow']}")

def update_data(servers):
    server_data = get_all_server_data(servers)

    if server_data:
        table_data = []
        for data in server_data:
            table_data.append([
                f"<a href='?server={data['port']}'>{data['port']}</a>",
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
        st.markdown(pd.DataFrame(table_data, columns=headers).to_html(escape=False, index=False), unsafe_allow_html=True)
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

    update_data(st.session_state.servers)

    # Sunucu ayrıntı sayfasını göster
    query_params = st.experimental_get_query_params()
    if 'server' in query_params:
        server_port = query_params["server"][0]
        for data in server_data:
            if data['port'] == server_port:
                display_server_details(data)
                break

if __name__ == "__main__":
    main()
