import base64
import contextlib
import json
from typing import Optional

from fastapi import HTTPException, Request
from fastapi.responses import Response

from deezer.core.config import *
from deezer.core.models import (
    InvalidAuthorizationHeaderError,
    NoAuthorizationHeaderError,
    ValidationError,
)
from deezer.core.redis import redis
from deezer.routers.v1 import router
from deezer.routers.v1.client import DeezerClient
from deezer.routers.v1.models import *
from deezer.routers.v1.utils import *


@router.get(
    "/search",
    summary="Search for a track, album, or playlist.",
    response_model=SearchResults,
    responses={
        401: {"model": NoAuthorizationHeaderError},
        403: {"model": InvalidAuthorizationHeaderError},
        422: {"model": ValidationError},
        500: {"model": DeezerError},
    },
)
async def search(query: str) -> Union[SearchResults, Response]:
    redis_result = await redis.get(
        json.dumps({"endpoint": "/v1/search", "query": query})
    )
    if redis_result:
        await redis.expire(
            json.dumps({"endpoint": "/v1/search", "query": query}), search_ttl
        )
        return Response(content=redis_result.decode("utf8"), status_code=200, media_type="application/json")

    client = DeezerClient()
    await client.setup_client()

    response = await client.search(query)
    await client.session.aclose()

    r = search_parser(response)
    await redis.set(
        json.dumps({"endpoint": "/v1/search", "query": query}), r.json(), ex=search_ttl
    )
    return r


@router.get(
    "/search/suggestions",
    summary="Get search suggestions for a query.",
    response_model=SearchSuggestionsResponse,
    responses={
        401: {"model": NoAuthorizationHeaderError},
        403: {"model": InvalidAuthorizationHeaderError},
        422: {"model": ValidationError},
        500: {"model": DeezerError},
    },
)
async def search_suggestions(
    query: str,
) -> Union[SearchSuggestionsResponse, Response]:
    redis_result = await redis.get(
        json.dumps({"endpoint": "/v1/search/suggestions", "query": query})
    )
    if redis_result:
        await redis.expire(
            json.dumps({"endpoint": "/v1/search/suggestions", "query": query}),
            search_suggestions_ttl,
        )
        return Response(content=redis_result.decode("utf8"), status_code=200, media_type="application/json")

    client = DeezerClient()
    await client.setup_client()

    response = await client.search_suggesions(query)
    await client.session.aclose()

    r = search_suggestion_parser(response)
    await redis.set(
        json.dumps({"endpoint": "/v1/search/suggestions", "query": query}),
        r.json(),
        ex=search_suggestions_ttl,
    )
    return r


@router.get(
    "/track/info/{id}",
    summary="Get track info.",
    response_model=TrackInfoResponse,
    responses={
        401: {"model": NoAuthorizationHeaderError},
        403: {"model": InvalidAuthorizationHeaderError},
        404: {"model": TrackNotFoundError},
        422: {"model": ValidationError},
        500: {"model": DeezerError},
    },
)
async def track_info(id: str) -> Union[SearchSuggestionsResponse, Response]:
    """
    The `id` path parameter is the track ID. Alternatively, you can prefix an isrc with `isrc:` to get the track info for that isrc.
    Example: `/v1/track/info/isrc:USUM71900001`
    """
    with contextlib.suppress(Exception):
        id = int(id)
        redis_result = await redis.get(
            json.dumps({"endpoint": "/v1/track/info", "id": id})
        )
        if redis_result:
            return Response(content=redis_result.decode("utf8"), status_code=200, media_type="application/json")

    client = DeezerClient()
    await client.setup_client()

    try:
        id = int(id)
    except:
        if id.startswith("isrc:"):
            redis_result = await redis.get(
                json.dumps({"endpoint": "/v1/isrc-id", "isrc": id[5:]})
            )
            if redis_result:
                id = json.loads(redis_result)["id"]
            else:
                id = await client.isrc_to_id(id[5:])
                if not id:
                    raise HTTPException(
                        status_code=404,
                        detail="The track you specified could not be found.",
                    )
        else:
            raise HTTPException(
                status_code=404, detail="The track you specified could not be found."
            )

    # Now we need to check redis again, because we have the the id
    redis_result = await redis.get(json.dumps({"endpoint": "/v1/track/info", "id": id}))
    if redis_result:
        return Response(content=redis_result.decode("utf8"), status_code=200, media_type="application/json")

    response = await client.get_track_info(id)
    await client.session.aclose()

    if not response:
        raise HTTPException(status_code=404, detail="Track not found.")

    r = track_info_mapper(response)
    await redis.set(json.dumps({"endpoint": "/v1/track/info", "id": id}), r.json())
    return r


@router.get(
    "/track/lyrics/{id}",
    summary="Get track lyrics.",
    response_model=TrackLyricsResponse,
    responses={
        401: {"model": NoAuthorizationHeaderError},
        403: {"model": InvalidAuthorizationHeaderError},
        404: {"model": TrackNotFoundError},
        422: {"model": ValidationError},
        500: {"model": DeezerError},
    },
)
async def track_lyrics(id: str) -> TrackLyricsResponse:
    """
    The `id` path parameter is the track ID. Alternatively, you can prefix an isrc with `isrc:` to get the track info for that isrc.
    Example: `/v1/track/info/isrc:USUM71900001`
    """
    with contextlib.suppress(Exception):
        id = int(id)
        redis_result = await redis.get(
            json.dumps({"endpoint": "/v1/track/lyrics", "id": id})
        )
        if redis_result:
            await redis.expire(
                json.dumps({"endpoint": "/v1/track/lyrics", "id": id}), track_lyrics_ttl
            )
            return Response(content=redis_result.decode("utf8"), status_code=200, media_type="application/json")

    client = DeezerClient()
    await client.setup_client()

    try:
        id = int(id)
    except:
        if id.startswith("isrc:"):
            redis_result = await redis.get(
                json.dumps({"endpoint": "/v1/isrc-id", "isrc": id[5:]})
            )
            if redis_result:
                id = json.loads(redis_result)["id"]
            else:
                id = await client.isrc_to_id(id[5:])
                if not id:
                    raise HTTPException(
                        status_code=404,
                        detail="The track you specified could not be found.",
                    )
        else:
            raise HTTPException(
                status_code=404, detail="The track you specified could not be found."
            )

    redis_result = await redis.get(
        json.dumps({"endpoint": "/v1/track/lyrics", "id": id})
    )
    if redis_result:
        await redis.expire(
            json.dumps({"endpoint": "/v1/track/lyrics", "id": id}), track_lyrics_ttl
        )
        return Response(content=redis_result.decode("utf8"), status_code=200, media_type="application/json")

    response = await client.get_lyrics(id)
    await client.session.aclose()

    r = TrackLyricsResponse(
        text=response["LYRICS_TEXT"],
        lines=[
            LyricLine(
                text=line["line"], start=line["milliseconds"], duration=line["duration"]
            )
            for line in response["LYRICS_SYNC_JSON"]
            if "LYRICS_SYNC_JSON" in response.keys() and line["line"]
        ],
    )
    await redis.set(
        json.dumps({"endpoint": "/v1/track/lyrics", "id": id}),
        r.json(),
        ex=track_lyrics_ttl,
    )
    return r


@router.get(
    "/track/download/{id}",
    summary="Download a track.",
    responses={
        200: {
            "content": {"audio/mpeg": {}, "application/json": None},
        },
        401: {"model": NoAuthorizationHeaderError},
        403: {"model": InvalidAuthorizationHeaderError},
        404: {"model": TrackNotFoundError},
        422: {"model": ValidationError},
        500: {"model": DeezerError},
    },
)
async def track_download(
    request: Request, id: str, image: Optional[bool] = True
) -> Response:
    """
    This endpoint is used to download a track. The audio codec is MP3, and the bitrate is 128kbps.

    The `id` path parameter is the ID of the track you want to download. You can get this ID by searching for a track using the `/search` endpoint. Alternatively, you can prefix an isrc with `isrc:` to get the track with that isrc.

    The `image` parameter is used to determine whether or not to inject image ID3 tag into the track. This makes the file size slightly larger and makes the request take longer to complete. It is enabled by default.
    """
    start, end = 0, None
    range_header = request.headers.get("Range")
    if range_header:
        try:
            range = range_header.split("bytes")[1].strip("=")

            start, end = range.split("-")
            if not end:
                end = None
            if not start:
                start = 0

            start = int(start)
            if end:
                end = int(end)
        except:
            pass  # We already set the range, so it'll fall back to the default range

    def process_range(data: bytes):
        if not end:
            return data[start:]
        else:
            return data[start:end]

    with contextlib.suppress(Exception):
        id = int(id)
        redis_result = await redis.get(
            json.dumps(
                {"endpoint": "/v1/track/download", "track_id": id, "image": image}
            )
        )
        if redis_result:
            redis_result = json.loads(redis_result)
            file_name = redis_result["file_name"]
            file = base64.b64decode(redis_result["file"])
            duration = redis_result["duration"]
            await redis.expire(
                json.dumps(
                    {"endpoint": "/v1/track/download", "track_id": id, "image": image}
                ),
                duration * 3,
            )
            return Response(
                content=process_range(file),
                media_type="audio/mpeg",
                headers={
                    "Content-Disposition": f"attachment; filename={file_name}".encode(
                        "utf8"
                    ).decode("latin1"),
                },
            )

    client = DeezerClient()
    await client.setup_client()

    try:
        id = int(id)
    except:
        if id.startswith("isrc:"):
            redis_result = await redis.get(
                json.dumps({"endpoint": "/v1/isrc-id", "isrc": id[5:]})
            )
            if redis_result:
                id = json.loads(redis_result)["id"]
            else:
                id = await client.isrc_to_id(id[5:])
                if not id:
                    raise HTTPException(
                        status_code=404,
                        detail="The track you specified could not be found.",
                    )
        else:
            raise HTTPException(
                status_code=404, detail="The track you specified could not be found."
            )

    redis_result = await redis.get(
        json.dumps({"endpoint": "/v1/track/download", "track_id": id, "image": image})
    )
    if redis_result:
        redis_result = json.loads(redis_result)
        file_name = redis_result["file_name"]
        file = base64.b64decode(redis_result["file"])
        duration = redis_result["duration"]
        await redis.expire(
            json.dumps(
                {"endpoint": "/v1/track/download", "track_id": id, "image": image}
            ),
            duration * 3,
        )

        return Response(
            content=process_range(file),
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": f"attachment; filename={file_name}".encode(
                    "utf8"
                ).decode("latin1"),
            },
        )

    track_info = await client.get_track_info(id)
    if not track_info:
        raise HTTPException(status_code=404, detail="Track not found.")

    audio_streamer = client.download_track(track_info)
    audio_data = b"".join([a async for a in audio_streamer])

    audio_data = await inject_id3(client, track_info, audio_data, image)

    await client.session.aclose()

    file_name = f"{track_info['SNG_TITLE']} - {track_info['ART_NAME']}.mp3"
    data = {
        "file_name": file_name,
        "duration": int(track_info["DURATION"]),
        "file": base64.b64encode(audio_data).decode("utf-8"),
    }
    await redis.set(
        json.dumps({"endpoint": "/v1/track/download", "track_id": id, "image": image}),
        json.dumps(data),
        ex=int(track_info["DURATION"]) * 3,
    )

    file_name = track_info["SNG_TITLE"] + " - " + track_info["ART_NAME"] + ".mp3"
    return Response(
        content=process_range(audio_data),
        media_type="audio/mpeg",
        headers={
            "Content-Disposition": f"attachment; filename={file_name}".encode(
                "utf8"
            ).decode("latin1"),
        },
    )
