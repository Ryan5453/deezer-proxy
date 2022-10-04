from typing import List, Optional, Union

from pydantic import BaseModel, Field

# Shared models


class DeezerError(BaseModel):
    error: str = Field(
        ..., example="Something went wrong when contacting the Deezer API."
    )


class TrackNotFoundError(BaseModel):
    error: str = Field(..., example="The track you specified could not be found.")


class Artwork(BaseModel):
    url: str = Field(
        ...,
        example="https://e-cdn-images.dzcdn.net/images/album/290abe93bdda84bb8b170f30a4998c4c/1000x1000-000000-80-0-0.jpg",
    )
    size: str = Field(..., example="large")
    width: int = Field(..., example=1000)
    height: int = Field(..., example=1000)


# Models for the /v1/track/lyrics/:id endpoint


class LyricLine(BaseModel):
    text: str = Field(..., example="I'm not a human being")
    start: int = Field(..., example=0)
    duration: int = Field(..., example=0)


class TrackLyricsResponse(BaseModel):
    text: str = Field(..., example="I'm a little teapot, short and stout")
    lines: List[LyricLine]


# Models for the /v1/track/info/:id endpoint


class AlbumTrackInfo(BaseModel):
    name: str
    id: int
    artwork: List[Artwork]


class AdditionalArtistTrackInfo(BaseModel):
    name: str
    id: int
    artwork: List[Artwork]


class ArtistTrackInfo(BaseModel):
    name: str
    id: int
    additional: List[AdditionalArtistTrackInfo]


class TrackInfoResponse(BaseModel):
    name: str
    id: int
    isrc: str
    track_number: int
    explicit: bool
    duration: int
    album: AlbumTrackInfo
    artist: ArtistTrackInfo


# Models for the /v1/search/suggestions endpoint


class SearchSuggestionsResponse(BaseModel):
    results: List[str] = Field(
        ..., example=["taylor swift", "taylor swift - cardigan", "taylor swift - betty"]
    )


# Models for the /v1/search endpoint


class ArtistSearchResult(BaseModel):
    name: str = Field(..., example="Taylor Swift")
    id: int = Field(..., example=12246)
    artwork: List[Artwork]


class MainAlbumArtistSearchResult(BaseModel):
    name: str = Field(..., example="Taylor Swift")
    id: int = Field(..., example=12246)


class AlbumArtistSearchResult(BaseModel):
    main: MainAlbumArtistSearchResult
    additional: List[ArtistSearchResult]


class AlbumSearchResult(BaseModel):
    name: str = Field(..., example="folklore (deluxe version)")
    id: int = Field(..., example=167766152)
    artwork: List[Artwork]
    artist: AlbumArtistSearchResult
    release_date: Optional[str] = Field(None, example="2020-07-24")


class TrackSearchResult(BaseModel):
    name: str = Field(..., example="betty")
    id: int = Field(..., example=1053765342)
    artist: ArtistSearchResult
    album: AlbumSearchResult
    isrc: str = Field(..., example="USUG12002848")
    duration: int = Field(..., example=201)
    has_lyrics: bool = Field(..., example=True)
    explicit: bool = Field(..., example=True)


class PlaylistSearchResult(BaseModel):
    name: str = Field(..., example="betty james and augustine story")
    id: int = Field(..., example=10696288182)
    artwork: List[Artwork]
    track_count: int = Field(..., example=24)


class TopResult(BaseModel):
    type: str = Field(..., example="artist")
    data: Union[
        ArtistSearchResult,
        AlbumSearchResult,
        TrackSearchResult,
        PlaylistSearchResult,
    ]


class SearchResults(BaseModel):
    top_result: Optional[TopResult]
    artists: List[ArtistSearchResult]
    albums: List[AlbumSearchResult]
    tracks: List[TrackSearchResult]
    playlists: List[PlaylistSearchResult]
    lyrics: List[TrackSearchResult]
