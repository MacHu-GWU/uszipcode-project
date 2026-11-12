# -*- coding: utf-8 -*-

"""
The API keys of the pipeline, each defined once. Both are free. A key is read from
its environment variable, else from its file in the home folder, only when a file
has to be downloaded; it is never written anywhere (see ``fetch.py``).
"""

from .core import Secret

#: for the Census Data API: sent as ``?key=...``
CENSUS_KEY = Secret(
    env="CENSUS_API_KEY",
    file="~/.census_key",
    signup_url="https://api.census.gov/data/key_signup.html",
    query_param="key",
)

#: for the HUD-USPS crosswalk: sent as ``Authorization: Bearer ...``
HUD_TOKEN = Secret(
    env="HUD_API_TOKEN",
    file="~/.hud_token",
    signup_url="https://www.huduser.gov/hudapi/public/register",
    bearer=True,
)
