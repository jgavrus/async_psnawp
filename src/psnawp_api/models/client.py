from __future__ import annotations

from typing import Any, AsyncIterator, Optional, Literal

import aiohttp
from aiohttp import ClientSession

from psnawp_api.models.group import Group
from psnawp_api.models.listing.pagination_arguments import PaginationArguments
from psnawp_api.models.title_stats import TitleStatsListing
from psnawp_api.models.trophies.trophy import Trophy, TrophyBuilder
from psnawp_api.models.trophies.trophy_group import (
    TrophyGroupsSummary,
    TrophyGroupsSummaryBuilder,
)
from psnawp_api.models.trophies.trophy_summary import TrophySummary
from psnawp_api.models.trophies.trophy_titles import TrophyTitles, TrophyTitle
from psnawp_api.models.user import User
from psnawp_api.utils.endpoints import BASE_PATH, API_PATH
from psnawp_api.utils.misc import create_session
from psnawp_api.utils.request_builder import RequestBuilder


class Client:
    """The Client class provides the information and methods for the currently authenticated user."""

    def __init__(self, request_builder: RequestBuilder):
        """Initialize a Client instance.

        .. note::

            This class is intended to be interfaced with through PSNAWP.

        :param request_builder: The instance of RequestBuilder. Used to make HTTPRequests.
        :type request_builder: RequestBuilder

        """
        self._account_id = ''
        self._online_id = ''
        self._request_builder = request_builder

    @create_session
    async def online_id(self, session: ClientSession = None) -> str:
        """Gets the online ID of the client logged in the api.

        :returns: onlineID
        :rtype: str

        .. code-block:: Python

            client = psnawp.me()
            print(client.online_id)

        """
        response = await self._request_builder.get(
            url=f"{BASE_PATH['profile_uri']}{API_PATH['profiles'].format(account_id=await self.account_id())}",
            session=session)
        response = await response.json()
        self._online_id: str = response["onlineId"]
        return self._online_id

    @create_session
    async def account_id(self, session: ClientSession = None) -> str:
        """Gets the account ID of the client logged in the api.

        :returns: accountID
        :rtype: str

        .. code-block:: Python

            client = psnawp.me()
            print(client.account_id)

        """
        if self._account_id:
            return self._account_id
        response = await self._request_builder.get(url=f"{BASE_PATH['account_uri']}{API_PATH['my_account']}",
                                                   session=session)
        response = await response.json()
        account_id: str = response["accountId"]
        self._account_id = account_id
        return account_id

    @create_session
    async def get_profile_legacy(self, session: ClientSession = None) -> dict[str, Any]:
        """Gets the profile info from legacy api endpoint. Useful for legacy console (PS3, PS4) presence.

        :returns: A dict containing info similar to what is shown below:
        :rtype: dict[str, Any]

            .. literalinclude:: examples/client/get_profile_legacy.json
                :language: json


        .. code-block:: Python

            client = psnawp.me()
            print(client.get_profile_legacy())

        """
        params = {
            "fields": "npId,onlineId,accountId,avatarUrls,plus,aboutMe,"
                      "languagesUsed,trophySummary(@default,level,progress,earnedTrophies),"
                      "isOfficiallyVerified,personalDetail(@default,profilePictureUrls),"
                      "personalDetailSharing,personalDetailSharingRequestMessageFlag,"
                      "primaryOnlineStatus,presences(@default,@titleInfo,platform,"
                      "lastOnlineDate,hasBroadcastData),requestMessageFlag,blocking,friendRelation,"
                      "following,consoleAvailability"
        }
        if not self._online_id:
            await self.online_id(session)
        response = await self._request_builder.get(
            url=f"{BASE_PATH['legacy_profile_uri']}{API_PATH['legacy_profile'].format(online_id=self._online_id)}",
            params=params, session=session)

        return await response.json()

    @create_session
    async def get_account_devices(self, session: ClientSession = None) -> list[dict[str, Any]]:
        """Gets the list of devices the client is logged into.

        :returns: A dict containing info similar to what is shown below:
        :rtype: list[dict[str, Any]]

            .. literalinclude:: examples/client/get_account_devices.json
                :language: json


        .. code-block:: Python

            client = psnawp.me()
            print(client.get_account_devices())

        """
        params = {
            "includeFields": "device,systemData",
            "platform": "PS5,PS4,PS3,PSVita",
        }

        response = await self._request_builder.get(url=f"{BASE_PATH['account_uri']}{API_PATH['my_account']}",
                                                   params=params, session=session)
        response = await response.json()
        # Just so mypy doesn't complain
        account_devices: list[dict[str, Any]] = response.get("accountDevices", [])
        return account_devices

    async def friends_list(self, limit: int = 1000) -> AsyncIterator[User]:
        """Gets the friends list and return their account ids.

        :param limit: The number of items from input max is 1000.
        :type limit: int

        :returns: All friends in your friends list.
        :rtype: Iterator[User]

        .. code-block:: Python

            client = psnawp.me()
            friends_list = client.friends_list()

            for friend in friends_list:
                ...

        """
        limit = min(1000, limit)

        params = {"limit": limit}
        async with aiohttp.ClientSession() as session:
            response = await self._request_builder.get(url=f"{BASE_PATH['profile_uri']}{API_PATH['friends_list']}",
                                                       params=params, session=session)
            response = await response.json()
        for account_id in response["friends"]:
            user = await User.from_account_id(request_builder=self._request_builder, account_id=account_id)
            yield user

    async def available_to_play(self) -> AsyncIterator[User]:
        """Gets the list of users on your "Notify when available" subscription list.

        :returns: Iterator of user objects.
        :rtype: Iterator[User]

        .. code-block:: Python

            client = psnawp.me()
            available_to_play = client.available_to_play()

            for user in available_to_play:
                ...

        """
        async with aiohttp.ClientSession() as session:
            response = await self._request_builder.get(url=f"{BASE_PATH['profile_uri']}{API_PATH['available_to_play']}",
                                                       session=session)
            response = await response.json()
        for account_id_dict in response["settings"]:
            yield await User.from_account_id(request_builder=self._request_builder,
                                             account_id=account_id_dict["accountId"])

    async def blocked_list(self) -> AsyncIterator[User]:
        """Gets the blocked list and return their account ids.

        :returns: Al blocked users on your block list.
        :rtype: Iterator[User]

        .. code-block:: Python

            client = psnawp.me()
            blocked_list = client.blocked_list()

            for blocked_users in blocked_list:
                ...

        """
        async with aiohttp.ClientSession() as session:
            response = await self._request_builder.get(url=f"{BASE_PATH['profile_uri']}{API_PATH['blocked_users']}",
                                                       session=session)
            response = await response.json()
        for account_id in response["blockList"]:
            user = await User.from_account_id(request_builder=self._request_builder, account_id=account_id)
            yield user

    @create_session
    async def get_groups(self, limit: int = 200, offset: int = 0) -> AsyncIterator[Group]:
        """Gets all the groups you have participated in.

        :param limit: The number of groups to receive.
        :type limit: int
        :param offset: Lets you exclude first N items groups. Offset = 10 lets you skip the first 10 groups.
        :type offset: int

        :returns: Iterator of Group Objects.
        :rtype: Iterator[Group]

        """
        param = {"includeFields": "members", "limit": limit, "offset": offset}
        async with aiohttp.ClientSession() as session:
            response = await self._request_builder.get(url=f"{BASE_PATH['gaming_lounge']}{API_PATH['my_groups']}",
                                                       params=param, session=session)
            response = await response.json()
        for group_info in response["groups"]:
            group = Group(request_builder=self._request_builder, group_id=group_info["groupId"], users=None)
            yield group

    async def trophy_summary(self) -> TrophySummary:
        """Retrieve an overall summary of the number of trophies earned for a user broken down by

        - type
        - overall trophy level
        - progress towards the next level
        - current tier

        :returns: Trophy Summary Object containing all information
        :rtype: TrophySummary

        .. code-block:: Python

            client = psnawp.me()
            print(client.trophy_summary())

        """
        return await TrophySummary.from_endpoint(request_builder=self._request_builder, account_id="me")

    async def trophy_titles(self, limit: Optional[int] = None) -> AsyncIterator[TrophyTitle]:
        """Retrieve all game titles associated with an account, and a summary of trophies earned from them.

        :param limit: Limit of titles returned, None means to return all trophy titles.
        :type limit: Optional[int]

        :returns: Generator object with TitleTrophySummary objects
        :rtype: Iterator[TrophyTitle]

        .. code-block:: Python

            client = psnawp.me()
            for trophy_title in client.trophy_titles(limit=None):
                print(trophy_title)

        """
        return TrophyTitles(request_builder=self._request_builder, account_id="me").get_trophy_titles(limit=limit)

    def trophy_titles_for_title(self, title_ids: list[str]) -> AsyncIterator[TrophyTitle]:
        """Retrieve a summary of the trophies earned by a user for specific titles.

        .. note::

            ``title_id`` can be obtained from https://andshrew.github.io/PlayStation-Titles/ or
            from :py:meth:`psnawp_api.models.search.Search.get_title_id`

        :param title_ids: Unique ID of the title
        :type title_ids: list[str]

        :returns: Generator object with TitleTrophySummary objects
        :rtype: Iterator[TrophyTitle]

        .. code-block:: Python

            client = psnawp.me()
            for trophy_title in client.trophy_titles_for_title(title_ids=['CUSA00265_00']):
                print(trophy_title)

        """
        return TrophyTitles(request_builder=self._request_builder, account_id="me").get_trophy_summary_for_title(
            title_ids=title_ids)

    def trophies(self, np_communication_id: str, platform: Literal["PS Vita", "PS3", "PS4", "PS5"],
                 trophy_group_id: str = "default", limit: Optional[int] = None,
                 include_metadata: bool = False) -> AsyncIterator[Trophy]:
        """Retrieves the earned status individual trophy detail of a single - or all - trophy groups for a title.

        :param np_communication_id: Unique ID of a game title used to request trophy information.
        This can be obtained from ``GameTitle`` class.
        :type np_communication_id: str
        :param platform: The platform this title belongs to.
        :type platform: Literal
        :param trophy_group_id: ID for the trophy group. Each game expansion is represented by a separate ID.
        all to return all trophies for the title, default
            for the game itself, and additional groups starting from 001 and so on return expansions trophies.
        :type trophy_group_id: str
        :param limit: Limit of trophies returned, None means to return all trophy titles.
        :type limit: Optional[int]
        :param include_metadata: If True, will fetch metadata for trophy such as name and detail
        :type include_metadata: bool

        .. warning::

            Setting ``include_metadata`` to ``True`` will use twice the amount of rate limit since
            the API wrapper has to obtain metadata from a separate
            endpoint.

        :returns: Returns the Trophy Generator object with all the information
        :rtype: Iterator[Trophy]

        """

        if not include_metadata:
            return TrophyBuilder(
                request_builder=self._request_builder,
                np_communication_id=np_communication_id,
            ).earned_game_trophies(
                account_id="me",
                platform=platform,
                trophy_group_id=trophy_group_id,
                limit=limit,
            )
        else:
            return TrophyBuilder(
                request_builder=self._request_builder,
                np_communication_id=np_communication_id,
            ).earned_game_trophies_with_metadata(
                account_id="me",
                platform=platform,
                trophy_group_id=trophy_group_id,
                limit=limit,
            )

    async def trophy_groups_summary(self, np_communication_id: str, platform: Literal["PS Vita", "PS3", "PS4", "PS5"],
                                    include_metadata: bool = False) -> TrophyGroupsSummary:
        """Retrieves the trophy groups for a title and their respective trophy count.

        This is most commonly seen in games which have expansions where additional trophies are added.

        :param np_communication_id: Unique ID of a game title used to request trophy information.
        This can be obtained from ``GameTitle`` class.
        :type np_communication_id: str
        :param platform: The platform this title belongs to.
        :param platform: The platform this title belongs to.
        :type platform: Literal
        :param include_metadata: If True, will fetch results from another endpoint and include
        metadata for trophy group such as name and detail
        :type include_metadata: bool

        .. warning::

            Setting ``include_metadata`` to ``True`` will use twice the amount of rate
            limit since the API wrapper has to obtain metadata from a separate
            endpoint.

        :returns: TrophyGroupSummary object containing title and title groups trophy information.
        :rtype: TrophyGroupsSummary

        """
        if not include_metadata:
            return await TrophyGroupsSummaryBuilder(
                request_builder=self._request_builder,
                np_communication_id=np_communication_id,
            ).user_trophy_groups_summary(account_id="me", platform=platform)
        else:
            return await TrophyGroupsSummaryBuilder(
                request_builder=self._request_builder,
                np_communication_id=np_communication_id,
            ).user_trophy_groups_summary_with_metadata(account_id="me", platform=platform)

    def title_stats(self, *, limit: Optional[int] = None, offset: int = 0, page_size: int = 200) -> TitleStatsListing:
        """Retrieve a list of titles with their stats and basic meta-data

        :param limit: Limit of titles returned.
        :type limit: Optional[int]
        :param page_size: The number of items to receive per api request.
        :type page_size: int
        :param offset: Specifies the offset for paginator
        :type offset: int

        .. warning::

            Only returns data for PS4 games and above.

        :returns: Iterator class for TitleStats
        :rtype: Iterator[TitleStatsListing]

        .. code-block:: Python

            user_example = psnawp.client()
            titles = list(user_example.title_stats())

        """
        pg_args = PaginationArguments(total_limit=limit, offset=offset, page_size=page_size)
        return TitleStatsListing(request_builder=self._request_builder, account_id="me", pagination_arguments=pg_args)

    # def __repr__(self) -> str:
    #     return f"<User online_id:{self.online_id} account_id:{self.account_id}>"
    #
    # def __str__(self) -> str:
    #     return f"Online ID: {self.online_id} Account ID: {self.account_id}"
