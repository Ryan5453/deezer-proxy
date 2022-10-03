import base64
import json
from typing import Optional

from fastapi import HTTPException, Request
from fastapi.responses import Response

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
        404: {"model": TrackNotFoundError},
        422: {"model": ValidationError},
        500: {"model": DeezerError},
    },
)
async def search(query: str) -> SearchResults:
    client = DeezerClient()
    await client.setup_client()

    response = await client.search(query)
    await client.session.aclose()

    return search_parser(response)


@router.get(
    "/search/suggestions",
    summary="Get search suggestions for a query.",
    response_model=SearchResults,
    responses={
        401: {"model": NoAuthorizationHeaderError},
        403: {"model": InvalidAuthorizationHeaderError},
        422: {"model": ValidationError},
        500: {"model": DeezerError},
    },
)
async def search_suggestions(query: str) -> SearchResults:
    client = DeezerClient()
    await client.setup_client()

    response = await client.search_suggesions(query)
    await client.session.aclose()

    return search_suggestion_parser(response)


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
async def track_info(id: str) -> TrackInfoResponse:
    """
    The `id` path parameter is the track ID. Alternatively, you can prefix an isrc with `isrc:` to get the track info for that isrc.
    Example: `/v1/track/info/isrc:USUM71900001`
    """
    client = DeezerClient()
    await client.setup_client()

    try:
        id = int(id)
    except:
        if id.startswith("isrc:"):
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

    response = await client.get_track_info(id)
    await client.session.aclose()

    if not response:
        raise HTTPException(status_code=404, detail="Track not found.")

    return track_info_mapper(response)


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
    client = DeezerClient()
    await client.setup_client()

    try:
        id = int(id)
    except:
        if id.startswith("isrc:"):
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

    response = await client.get_lyrics(id)
    await client.session.aclose()

    return TrackLyricsResponse(
        text=response["LYRICS_TEXT"],
        lines=[
            LyricLine(
                text=line["line"], start=line["milliseconds"], duration=line["duration"]
            )
            for line in response["LYRICS_SYNC_JSON"]
            if "LYRICS_SYNC_JSON" in response.keys() and line["line"]
        ],
    )


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
    request: Request, id: int, image: Optional[bool] = True
) -> Response:
    """
    This endpoint is used to download a track. The audio codec is MP3, and the bitrate is 128kbps.

    The `id` path parameter is the ID of the track you want to download. You can get this ID by searching for a track using the `/search` endpoint.

    The `image` parameter is used to determine whether or not to inject image ID3 tag into the track. This makes the file size slightly larger and makes the request take longer to complete. It is enabled by default.
    """
    redis_result = await redis.get(json.dumps({"track_id": id, "image": image}))
    if redis_result:
        redis_result = json.loads(redis_result)
        file_name = redis_result["file_name"]
        file = base64.b64decode(redis_result["file"])
        return Response(
            content=file,
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": f"attachment; filename={file_name}",
                "Content-Length": str(len(file)),
            },
        )

    client = DeezerClient()
    await client.setup_client()

    track_info = await client.get_track_info(id)
    if not track_info:
        raise HTTPException(status_code=404, detail="Track not found.")

    audio_streamer = client.download_track(track_info)
    audio_data = b"".join([a async for a in audio_streamer])

    if image:
        audio_data = await inject_id3(client, track_info, audio_data)

    await client.session.aclose()

    file_name = f"{track_info['SNG_TITLE']} - {track_info['ART_NAME']}.mp3"
    data = {
        "file_name": file_name,
        "file": base64.b64encode(audio_data).decode("utf-8"),
    }
    await redis.set(
        json.dumps({"track_id": id, "image": image}), json.dumps(data)
    )

    file_name = track_info["SNG_TITLE"] + " - " + track_info["ART_NAME"] + ".mp3"
    return Response(
        content=audio_data,
        media_type="audio/mpeg",
        headers={
            "Content-Disposition": f"attachment; filename={file_name}",
            "Content-Length": str(len(audio_data)),
        },
    )
