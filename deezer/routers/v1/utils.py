from io import BytesIO
from typing import List

from mutagen.id3 import APIC, ID3, TALB, TDRC, TIT2, TPE1, TRCK

from deezer.routers.v1.client import DeezerClient
from deezer.routers.v1.models import *
from deezer.routers.v1.models import SearchResults


def track_info_artist_mapper(data: dict) -> ArtistTrackInfo:
    return ArtistTrackInfo(
        name=data["ART_NAME"],
        id=int(data["ART_ID"]),
        additional=[
            AdditionalArtistTrackInfo(
                name=artist["ART_NAME"],
                id=int(artist["ART_ID"]),
                artwork=generate_artwork("artist", artist["ART_PICTURE"]),
            )
            for artist in data["ARTISTS"]
        ],
    )


def track_info_mapper(data: dict) -> TrackInfoResponse:
    return TrackInfoResponse(
        name=data["SNG_TITLE"],
        id=data["SNG_ID"],
        isrc=data["ISRC"],
        track_number=data["TRACK_NUMBER"],
        explicit=data["EXPLICIT_LYRICS"] == "1",
        duration=data["DURATION"],
        artist=track_info_artist_mapper(data),
        album=AlbumTrackInfo(
            name=data["ALB_TITLE"],
            id=data["ALB_ID"],
            artwork=generate_artwork("album", data["ALB_PICTURE"]),
        ),
    )


async def inject_id3(
    client: DeezerClient, track_info: dict, audio_data: bytes, image: bool
) -> bytes:
    audio_data = BytesIO(audio_data)

    song_name = track_info["SNG_TITLE"]
    artist_name = track_info["ART_NAME"]
    album_name = track_info["ALB_TITLE"]
    track_number = track_info["TRACK_NUMBER"]  # It's a string
    release_date = track_info["PHYSICAL_RELEASE_DATE"]  # YYYY-MM-DD format

    album_art_url = (
        "https://cdns-images.dzcdn.net/images/cover/"
        + track_info["ALB_PICTURE"]
        + "/1000x1000-000000-80-0-0.jpg"
    )

    audio = ID3()
    audio.add(TIT2(encoding=3, text=song_name))
    audio.add(TPE1(encoding=3, text=artist_name))
    audio.add(TALB(encoding=3, text=album_name))
    audio.add(TRCK(encoding=3, text=track_number))
    audio.add(TDRC(encoding=3, text=release_date))
    
    if image:
        try:
            album_art = (await client.session.get(album_art_url)).read()
            audio.add(
                APIC(encoding=3, mime="image/jpeg", type=3, desc="Cover", data=album_art)
            )
        except Exception:
            pass  # In the case of an error, we don't want to fail the whole metadata injection because it's not that important

    audio.save(audio_data, v2_version=3)

    return audio_data.getvalue()


def search_suggestion_parser(response: dict) -> SearchSuggestionsResponse:
    return SearchSuggestionsResponse(
        results=[result["QUERY"] for result in response["SUGGESTION"]]
    )


def generate_artwork(type: str, hash: str) -> List[Artwork]:
    if not hash:
        return []
    return [
        Artwork(
            url=f"https://e-cdn-images.dzcdn.net/images/{type}/{hash}/500x500-000000-80-0-0.jpg",
            size="small",
            width=250,
            height=250,
        ),
        Artwork(
            url=f"https://e-cdn-images.dzcdn.net/images/{type}/{hash}/750x750-000000-80-0-0.jpg",
            size="medium",
            width=500,
            height=500,
        ),
        Artwork(
            url=f"https://e-cdn-images.dzcdn.net/images/{type}/{hash}/1000x1000-000000-80-0-0.jpg",
            size="large",
            width=1000,
            height=1000,
        ),
    ]


def artist_mapper(data: dict) -> ArtistSearchResult:
    return ArtistSearchResult(
        name=data["ART_NAME"],
        id=data["ART_ID"],
        artwork=generate_artwork("artist", data["ART_PICTURE"]),
    )


def album_mapper(data: dict) -> AlbumSearchResult:
    return AlbumSearchResult(
        name=data["ALB_TITLE"],
        id=data["ALB_ID"],
        artwork=generate_artwork("album", data["ALB_PICTURE"]),
        artist=AlbumArtistSearchResult(
            main=MainAlbumArtistSearchResult(
                name=data["ART_NAME"],
                id=data["ART_ID"],
            ),
            additional=[artist_mapper(artist) for artist in data["ARTISTS"]],
        ),
        release_date=data.get(
            "ORIGINAL_RELEASE_DATE", data.get("PHYSICAL_RELEASE_DATE")
        ),
    )


def track_mapper(data: dict) -> TrackSearchResult:
    return TrackSearchResult(
        name=data["SNG_TITLE"],
        id=data["SNG_ID"],
        artist=artist_mapper(data),
        album=album_mapper(data),
        duration=int(data["DURATION"]),
        isrc=data["ISRC"],
        has_lyrics=data["HAS_LYRICS"],
        explicit=data["EXPLICIT_LYRICS"] == "1",
    )


def playlist_mapper(data: dict) -> PlaylistSearchResult:
    return PlaylistSearchResult(
        name=data["TITLE"],
        id=data["PLAYLIST_ID"],
        artwork=generate_artwork("playlist", data["PLAYLIST_PICTURE"]),
        track_count=data["NB_SONG"],
    )


def search_parser(response: dict) -> SearchResults:
    top_result = None
    if response.get("TOP_RESULT"):
        top_result = response["TOP_RESULT"][0]
        if top_result["__TYPE__"] == "artist":
            top_result = TopResult(
                type="artist",
                data=artist_mapper(top_result),
            )
        elif top_result["__TYPE__"] == "album":
            top_result = TopResult(
                type="album",
                data=album_mapper(top_result),
            )
        elif top_result["__TYPE__"] == "track":
            top_result = TopResult(
                type="track",
                data=track_mapper(top_result),
            )
        elif top_result["__TYPE__"] == "playlist":
            top_result = TopResult(
                type="playlist",
                data=playlist_mapper(top_result),
            )

    artists = [artist_mapper(artist) for artist in response["ARTIST"]["data"]]
    albums = [album_mapper(album) for album in response["ALBUM"]["data"]]
    tracks = [track_mapper(track) for track in response["TRACK"]["data"]]
    playlists = [playlist_mapper(playlist) for playlist in response["PLAYLIST"]["data"]]
    lyrics = [track_mapper(track) for track in response["LYRICS"]["data"]]

    return SearchResults(
        top_result=top_result,
        artists=artists,
        albums=albums,
        tracks=tracks,
        playlists=playlists,
        lyrics=lyrics,
    )
