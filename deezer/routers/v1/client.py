from typing import Optional

import httpx
from fastapi import HTTPException

from deezer.routers.v1.blowfish import decrypt_chunk, generate_blowfish_key


class DeezerClient:
    def __init__(self) -> None:
        self.session = httpx.AsyncClient()
        self.session_id = ""
        self.user_token = ""
        self.user_license_token = ""
        self.api_token = ""

    async def api_request(self, method: str, data: Optional[dict] = {}) -> dict:
        if self.session_id:
            cookies = {"sid": self.session_id}
        else:
            cookies = {}

        params = {
            "method": method,
            "input": 3,
            "api_version": "1.0",
            "api_token": self.api_token,
        }
        r = await self.session.post(
            f"https://www.deezer.com/ajax/gw-light.php?",
            params=params,
            json=data,
            cookies=cookies,
        )
        if r.status_code != 200:
            raise HTTPException(
                status_code=500, detail="Had an error while making an API request."
            )
        return r.json()

    async def setup_client(self) -> None:
        ping_request = await self.api_request("deezer.ping")
        self.session_id = ping_request["results"]["SESSION"]

        user_data_request = await self.api_request("deezer.getUserData")
        self.user_token = user_data_request["results"]["USER_TOKEN"]
        self.user_license_token = user_data_request["results"]["USER"]["OPTIONS"][
            "license_token"
        ]
        self.api_token = user_data_request["results"]["checkForm"]

    async def search(self, query: str) -> dict:
        data = {"query": query, "start": 0, "nb": 10, "top_tracks": True}
        r = await self.api_request("deezer.pageSearch", data)
        return r["results"]

    async def search_suggesions(self, query: str) -> dict:
        data = {"QUERY": query}
        r = await self.api_request("search_getSuggestedQueries", data)
        return r["results"]

    async def get_track_info(self, track_id: str) -> dict:
        data = {"sng_id": track_id}
        r = await self.api_request("song.getData", data)

        if not r["results"]:
            return

        return r["results"]

    # Unused, for now
    async def get_lyrics(self, id: int) -> dict:
        data = {"sng_id": id}
        r = await self.api_request("song.getLyrics", data)

        return r["results"]

    async def isrc_to_id(self, isrc: str) -> int:
        url = f"https://api.deezer.com/2.0/track/isrc:{isrc}"
        r = await self.session.get(url)
        if r.status_code != 200:
            raise HTTPException(
                status_code=500, detail="Had an error while making an API request."
            )
        j = r.json()
        if "id" in j.keys():
            return j["id"]

    async def download_track(self, track_info: dict) -> bytes:
        data = {
            "license_token": self.user_license_token,
            "media": [
                {
                    "type": "FULL",
                    "formats": [{"cipher": "BF_CBC_STRIPE", "format": "MP3_128"}],
                }
            ],
            "track_tokens": [track_info["TRACK_TOKEN"]],
        }
        resp = await self.session.post("https://media.deezer.com/v1/get_url", json=data)
        if resp.status_code != 200:
            raise HTTPException(
                status_code=500, detail="Had an error while making an API request."
            )
        json = resp.json()

        url = json["data"][0]["media"][0]["sources"][0]["url"]

        blowfish_key = generate_blowfish_key(track_info["SNG_ID"])
        async with self.session.stream("GET", url) as r:
            iterations = 0
            async for data in r.aiter_bytes(chunk_size=2048):
                if iterations % 3 == 0 and len(data) == 2048:
                    data = decrypt_chunk(data, blowfish_key)
                yield data
                iterations += 1
                continue
