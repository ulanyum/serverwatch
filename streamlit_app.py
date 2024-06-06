import asyncio
import aiohttp
import streamlit as st
import pandas as pd
from datetime import datetime
import time

def humanize_time_difference(update_time):
    # ... (değişiklik yok)

async def get_server_data(session, server):
    # ... (değişiklik yok)

async def get_all_server_data(servers):
    # ... (değişiklik yok)

def update_data(servers):
    # ... (değişiklik yok)

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

    # Otomatik güncelleme
    if "last_update" not in st.session_state:
        st.session_state.last_update = datetime.now()

    if (datetime.now() - st.session_state.last_update).total_seconds() >= 10:
        st.session_state.last_update = datetime.now()
        st.experimental_rerun()

    # Sonraki güncellemeye kalan süreyi göster
    next_update = st.session_state.last_update + pd.Timedelta(seconds=10)
    time_left = next_update - datetime.now()
    st.write(f"Next update in {time_left.seconds} seconds")

    # Sayfa yenilenmesini engelle
    time.sleep(1)

if __name__ == "__main__":
    main()
