import json
from typing import Any

from aiohttp import ClientSession, ClientResponse

from psnawp_api.core.authenticator import Authenticator
from psnawp_api.core.psnawp_exceptions import (
    PSNAWPNotFound,
    PSNAWPForbidden,
    PSNAWPBadRequest,
    PSNAWPNotAllowed,
    PSNAWPServerError,
    PSNAWPUnauthorized,
)


async def response_checker(response: ClientResponse) -> None:
    """Checks the HTTP(S) response and re-raises them as PSNAWP Exceptions
    :param response: :class:`ClientSession` object
    :type response: requests.Response

    :returns: None

    """
    if response.status == 400:
        raise PSNAWPBadRequest(await response.text())
    elif response.status == 401:
        raise PSNAWPUnauthorized(await response.text())
    elif response.status == 403:
        raise PSNAWPForbidden(await response.text())
    elif response.status == 404:
        raise PSNAWPNotFound(await response.text())
    elif response.status == 405:
        raise PSNAWPNotAllowed(await response.text())
    elif response.status >= 500:
        raise PSNAWPServerError(await response.text())
    else:
        response.raise_for_status()


class RequestBuilder:
    """Handles all the HTTP Requests and provides a gateway to interacting with PSN API."""

    def __init__(self, authenticator: Authenticator, accept_language: str, country: str, timeout: float = 10.0):
        """Initialized Request Handler and saves the instance of authenticator for future use.

        :param Authenticator authenticator: The instance of :class: `Authenticator`. Represents single authentication to PSN API.
        :param str accept_language: The preferred language(s) for content negotiation in HTTP headers.
        :param str country: The client's country for HTTP headers.

        """
        self.timeout = timeout
        self.authenticator = authenticator
        self.default_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36",
            "Content-Type": "application/json",
            "Accept-Language": accept_language,
            "Country": country,
        }

    async def auth_headers(self, session: ClientSession = None, **kwargs: Any) -> dict:
        access_token = await self.authenticator.obtain_fresh_access_token(session)
        headers = {**self.default_headers, "Authorization": f"Bearer {access_token}"}
        if "headers" in kwargs.keys():
            headers = {**headers, **kwargs["headers"]}
        return headers

    async def get(self, session: ClientSession, **kwargs: Any) -> ClientResponse:
        """Handles the GET requests and returns the requests.Response object.

        :param session: aiohttp  ClientSession.
        :param kwargs: The query parameters to add to the request.

        :returns: The Request Response Object.
        :rtype: requests.Response

        """

        headers = await self.auth_headers(session=session, **kwargs)
        params = kwargs.get("params")
        data = kwargs.get("data")

        response = await session.get(url=kwargs["url"], headers=headers, params=params, data=data, timeout=self.timeout)
        await response_checker(response)
        return response

    async def patch(self, session: ClientSession, **kwargs: Any) -> ClientResponse:
        """Handles the POST requests and returns the requests.Response object.

        :param session: aiohttp  ClientSession.
        :param kwargs: The query parameters to add to the request.

        :returns: The Request Response Object.
        :rtype: requests.Response

        """
        headers = await self.auth_headers(session=session, **kwargs)

        params = kwargs.get("params")
        data = kwargs.get("data")

        response = await session.patch(url=kwargs["url"], headers=headers, data=data, params=params)

        await response_checker(response)
        return response

    async def post(self, session: ClientSession, **kwargs: Any) -> ClientResponse:
        """Handles the POST requests and returns the requests.Response object.

        :param session: aiohttp  ClientSession.
        :param kwargs: The query parameters to add to the request.

        :returns: The Request Response Object.
        :rtype: requests.Response

        """
        headers = kwargs.pop('headers', None)
        if not headers:
            headers = await self.auth_headers(session)

        response = await session.post(**kwargs, headers=headers)

        await response_checker(response)
        return response

    async def multipart_post(self, session: ClientSession, **kwargs: Any) -> ClientResponse:
        """Handles the Multipart POST requests and returns the requests.Response object.

        :param session: aiohttp  ClientSession.
        :param kwargs: The query parameters to add to the request.

        :returns: The Request Response Object.
        :rtype: requests.Response

        """
        headers = await self.auth_headers(session)

        data = kwargs.get("data")

        response = await session.post(
            url=kwargs["url"],
            headers=headers,
            files={
                kwargs["name"]: (
                    None,
                    json.dumps(data),
                    "application/json; charset=utf-8",
                )
            },
        )
        await response_checker(response)
        return response

    async def delete(self, session: ClientSession, **kwargs: Any) -> ClientResponse:
        """Handles the DELETE requests and returns the requests.Response object.

        :param session: aiohttp  ClientSession.
        :param kwargs: The query parameters to add to the request.

        :returns: The Request Response Object.
        :rtype: requests.Response

        """
        headers = await self.auth_headers(session)

        params = kwargs.get("params")
        data = kwargs.get("data")

        response = await session.delete(url=kwargs["url"], headers=headers, params=params, data=data)
        await response_checker(response)
        return response
