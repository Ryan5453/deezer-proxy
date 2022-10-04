<h1 align="center">
    deezer proxy
</p>

<p align="center">
    <a href="https://github.com/ryan5453/deezer-proxy/stargazers">
        <img src="https://img.shields.io/github/stars/ryan5453/deezer-proxy?style=social">
    </a>
    <a href="https://github.com/ryan5453/deezer-proxy/blob/main/LICENSE">
        <img src="https://img.shields.io/github/license/ryan5453/deezer-proxy">
    </a>
    <a href="https://python.org/">
        <img src="https://img.shields.io/badge/python-3.9-blue">
    </a>
    <a href="https://github.com/ambv/black">
        <img src="https://img.shields.io/badge/code%20style-black-black.svg">
    </a>
    <a href="https://github.com/PyCQA/isort">
        <img src="https://img.shields.io/badge/imports-isort-black.svg">
    </a>
</p>

## Setup
It's easiest to use this with docker. But, you can also run it without docker.

### Docker
- Git clone the repo
- CD into the repo
- Create an `.env` file with the following contents:
```env
DEEZER_MASTER_KEY=<KEY> # You'll need to find this by yourself, sorry.
DEEZER_REDIS_URL=redis://redis:6379/0
DEEZER_SEARCH_TTL=10800
DEEZER_SUGGESTIONS_TTL=86400
DEEZER_TRACK_LYRICS_TTL=43200
DEEZER_AUTH_KEY=<KEY> # If you don't include this line, authentication will be disabled
```
- Run `docker-compose up -d`

### Without Docker
- Git clone the repo
- (Optional) Create a virtual environment
- Install the requirements with `pip install -r requirements.txt`
- Install Redis
- Set the environment variables (see above)
- Run `uvicorn deezer:app`


## What is this?
This is a simple API written in Python using FastAPI that proxies requests to the internal Deezer API. It does not contain the Deezer blowfish key, so you will need obtain that on your own.