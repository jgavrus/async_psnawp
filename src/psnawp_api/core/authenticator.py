from __future__ import annotations

import asyncio
import time
from typing import Any
from urllib.parse import urlparse, parse_qs

from aiohttp import ClientSession

from psnawp_api.core import psnawp_exceptions
from psnawp_api.utils.endpoints import BASE_PATH, API_PATH
from psnawp_api.utils.misc import create_logger, create_session


class Authenticator:
    """Provides an interface for PSN Authentication."""

    __PARAMS = {
        "CLIENT_ID": "09515159-7237-4370-9b40-3806e67c0891",
        "SCOPE": "psn:mobile.v2.core psn:clientapp",
        "REDIRECT_URI": "com.scee.psxandroid.scecompcall://redirect",
    }
    __AUTH_HEADER = {"Authorization": "Basic MDk1MTUxNTktNzIzNy00MzcwLTliNDAtMzgwNmU2N2MwODkxOnVjUGprYTV0bnRCMktxc1A="}

    def __init__(self, npsso_cookie: str):
        """Represents a single authentication to PSN API.

        :param npsso_cookie: npsso cookie obtained from PSN website.

        :raises: ``PSNAWPAuthenticationError`` If npsso code is expired or is incorrect.

        """
        self._npsso_token = npsso_cookie
        self._auth_properties: dict[str, Any] = {}
        self._authenticator_logger = create_logger(__file__)

    async def async_request_token(self, data, session: ClientSession):
        response = await session.post(
            f"{BASE_PATH['base_uri']}{API_PATH['access_token']}",
            headers=Authenticator.__AUTH_HEADER,
            data=data,
        )
        self._auth_properties = await response.json()
        self._auth_properties["access_token_expires_at"] = self._auth_properties["expires_in"] + time.time()
        if self._auth_properties["refresh_token_expires_in"] <= 60 * 60 * 24 * 3:
            self._authenticator_logger.warning(
                "Warning: Your refresh token is going to expire in less than 3 days. Please renew you npsso token!")

    async def obtain_fresh_access_token(self, session: ClientSession) -> str:
        """Gets a new access token from refresh token.

        :returns: access token

        """
        if not self._auth_properties:
            await self._authenticate()
        if self._auth_properties.get("access_token_expires_at", 0) > time.time():
            return self._auth_properties["access_token"]

        data = {
            "refresh_token": self._auth_properties["refresh_token"],
            "grant_type": "refresh_token",
            "scope": Authenticator.__PARAMS["SCOPE"],
            "token_format": "jwt",
        }
        await self.async_request_token(data, session)
        return self._auth_properties["access_token"]

    async def oauth_token(self, code: str, session: ClientSession) -> None:
        """Obtain the access token using oauth code for the first time,
        after this the access token is obtained via refresh token.

        :param session: aiohttp  ClientSession.
        :param code: Code obtained using npsso code.

        """

        data = {
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": Authenticator.__PARAMS["REDIRECT_URI"],
            "scope": Authenticator.__PARAMS["SCOPE"],
            "token_format": "jwt",
        }

        await self.async_request_token(data, session)

    @create_session
    async def _authenticate(self, session: ClientSession = None) -> None:
        """Authenticate using the npsso code provided in the constructor.

        Obtains the access code and the refresh code. Access code lasts about 1 hour.
        While the refresh code lasts about 2 months. After 2 months a new npsso code is needed.

        :raises: ``PSNAWPAuthenticationError`` If authentication is not successful.

        """
        cookies = {"Cookie": f"npsso={self._npsso_token}"}
        params = {
            "access_type": "offline",
            "client_id": Authenticator.__PARAMS["CLIENT_ID"],
            "scope": Authenticator.__PARAMS["SCOPE"],
            "redirect_uri": Authenticator.__PARAMS["REDIRECT_URI"],
            "response_type": "code",
        }
        response = await session.get(
            f"{BASE_PATH['base_uri']}{API_PATH['oauth_code']}",
            headers=cookies,
            params=params,
            allow_redirects=False,
        )
        response.raise_for_status()
        location_url = response.headers["location"]
        parsed_url = urlparse(location_url)
        parsed_query = parse_qs(parsed_url.query)
        if "error" in parsed_query.keys():
            if "4165" in parsed_query["error_code"]:
                raise psnawp_exceptions.PSNAWPAuthenticationError(
                    "Your npsso code has expired or is incorrect. Please generate a new code!")
            else:
                raise psnawp_exceptions.PSNAWPAuthenticationError("Something went wrong while authenticating")
        await self.oauth_token(parsed_query["code"][0], session)
