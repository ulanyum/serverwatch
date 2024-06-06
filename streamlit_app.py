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

def get_all_server_data(servers):
    async def get_all_server_data_async(servers):
        async with aiohttp.ClientSession() as session:
            tasks = [get_server_data(session, server) for server in servers]
            server_data = await asyncio.gather(*tasks)
            return [data for data in server_data if data is not None]

    return asyncio.run(get_all_server_data_async(servers))

def update_data(servers):
    # ... (değişiklik yok)

def main():
    # ... (değişiklik yok)

if __name__ == "__main__":
    main()
