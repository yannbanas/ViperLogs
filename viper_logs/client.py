"""Client for remote logging."""
import aiohttp
import json
from typing import Optional, Dict
from datetime import datetime

class LogClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        
    async def log(
        self, 
        level: str, 
        user_id: str, 
        action: str, 
        description: str, 
        component: str, 
        metadata: Optional[Dict] = None
    ):
        async with aiohttp.ClientSession() as session:
            try:
                payload = {
                    "level": level,
                    "user_id": user_id,
                    "action": action,
                    "description": description,
                    "component": component,
                    "metadata": metadata or {}
                }
                async with session.post(
                    f"{self.base_url}/log", 
                    json=payload,
                    raise_for_status=False
                ) as resp:
                    data = await resp.json()
                    if resp.status not in (200, 201):
                        print(f"Server error: {data.get('message', 'Unknown error')}")
                        return None
                    return data
            except aiohttp.ClientError as e:
                print(f"Client error: {str(e)}")
                return None

    async def get_metrics(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/metrics") as resp:
                return await resp.json()

    async def set_level(self, level: str):
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.base_url}/level/{level}") as resp:
                return await resp.json()
