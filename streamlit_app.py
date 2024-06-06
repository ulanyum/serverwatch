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
            if queue_running > 0:
                current_job = queue_data["queue_running"][0]
                if "extra_pnginfo" in current_job[2] and "workflow" in current_job[2]["extra_pnginfo"]:
                    workflow_data = current_job[2]["extra_pnginfo"]["workflow"]
                    if "nodes" in workflow_data:
                        current_task = workflow_data["nodes"][-1]["widgets_values"][0]
                    workflow = workflow_data.get("name", "")

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
