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
            python_version = stats_data["system"]["python_version"].split(" ")[0]

        # /queue endpoint'inden veri al
        async with session.get(f"http://{server}/queue", ssl=False) as resp:
            queue_data = await resp.json()
            queue_running = len(queue_data["queue_running"])
            queue_pending = len(queue_data["queue_pending"])
            current_task = ""
            if queue_running > 0 and
