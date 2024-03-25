from __future__ import annotations

import json
from typing import Optional, Iterator, Any

from aiohttp import ClientSession

from psnawp_api.core.psnawp_exceptions import PSNAWPNotFound, PSNAWPBadRequest, PSNAWPForbidden
from psnawp_api.models.user import User
from psnawp_api.utils.endpoints import BASE_PATH, API_PATH
from psnawp_api.utils.misc import create_session
from psnawp_api.utils.request_builder import RequestBuilder


class Group:
    """The Group class manages PSN group endpoints related to messages (Group and Direct Messages)."""

    def __init__(self, request_builder: RequestBuilder, group_id: Optional[str], users: Optional[Iterator[User]]):
        """Constructor of Group.

        .. note::

            This class is intended to be interfaced with through PSNAWP.

        :param request_builder: The instance of RequestBuilder. Used to make HTTPRequests.
        :type request_builder: RequestBuilder
        :param group_id: The Group ID of a group.
        :type group_id: Optional[str]
        :param users: A list of users of the members in the group.
        :type users: Optional[Iterator[User]]

        :raises: ``PSNAWPNotFound`` If group id does not exist or is invalid.

        :raises: ``PSNAWPForbidden`` If you are Dming a user who has blocked you. blocked you.

        """

        self._request_builder = request_builder
        self.group_id = group_id
        self.users = users

        if self.group_id is not None:
            self.get_group_information()
        elif self.users is not None:
            self._create_group()

    @create_session
    async def _create_group(self, session: ClientSession = None) -> None:
        """Creates a new group if it doesn't exist. Doesn't work if user's privacy settings block invites.

        :raises: ``PSNAWPForbidden`` If you are Dming a user who has blocked you.

        """
        if self.users is not None:
            invitees = [{"accountId": user.account_id} for user in self.users]
            data = {"invitees": invitees}

            try:
                response = await self._request_builder.post(
                    url=f"{BASE_PATH['gaming_lounge']}{API_PATH['create_group']}", data=json.dumps(data),
                    session=session)
                response = await response.json()
                self.group_id = response["groupId"]
            except PSNAWPForbidden as forbidden:
                raise PSNAWPForbidden(
                    "The group cannot be created because the user has either "
                    "set messages to private or has blocked you.") from forbidden

    @create_session
    async def change_name(self, group_name: str, session: ClientSession = None) -> None:
        """Changes the group name to one specified in arguments.

        .. note::

            You cannot change the name of DM groups. i.e. Groups with only two people (including you).

        :param group_name: The name of the group that will be set.
        :param session: aiohttp.ClientSession object
        :type group_name: str

        :returns: None

        :raises: ``PSNAWPBadRequest`` If you are not part of group or the group is a DM.

        """

        data = {"groupName": {"value": group_name}}
        try:
            await self._request_builder.patch(
                url=f"{BASE_PATH['gaming_lounge']}{API_PATH['group_settings'].format(group_id=self.group_id)}",
                data=json.dumps(data), session=session)
        except PSNAWPBadRequest as bad_req:
            raise PSNAWPBadRequest(
                f"The group name of Group ID {self.group_id} does cannot be changed. "
                f"Group is either a dm or does not exist.") from bad_req

    @create_session
    async def get_group_information(self, session: ClientSession = None) -> dict[str, Any]:
        """Gets the group chat information such as about me, avatars, languages etc...

        :returns: A dict containing info similar to what is shown below:
        :rtype: dict[str, Any]

        :raises: ``PSNAWPNotFound`` If group id does not exist or is invalid.

        .. literalinclude:: examples/group/group_information.json
            :language: json

        """

        param = {
            "includeFields": "groupName,groupIcon,members,mainThread,joinedTimestamp,"
                             "modifiedTimestamp,isFavorite,existsNewArrival,partySessions,"
                             "notificationSetting"
        }

        try:
            response = await self._request_builder.get(
                url=f"{BASE_PATH['gaming_lounge']}{API_PATH['group_members'].format(group_id=self.group_id)}",
                params=param, session=session)
            return await response.json()
        except PSNAWPNotFound as not_found:
            raise PSNAWPNotFound(f"Group ID {self.group_id} does not exist.") from not_found

    @create_session
    async def send_message(self, message: str, session: ClientSession = None) -> dict[str, str]:
        """Sends a message in the group.

        .. note::

            For now only text based messaging is supported.

        :param message: Message Body
        :param session: aiohttp.ClientSession object
        :returns: A dict containing info similar to what is shown below:
        :rtype: dict[str, str]

        .. code-block:: json

            {
                "messageUid": "1#425961448584099",
                "createdTimestamp": "1663911908531"
            }

        """

        data = {"messageType": 1, "body": message}

        response = await self._request_builder.post(
            url=f"{BASE_PATH['gaming_lounge']}{API_PATH['send_group_message'].format(group_id=self.group_id)}",
            data=json.dumps(data), session=session)

        return await response.json()

    @create_session
    async def get_conversation(self, limit: int = 20, session: ClientSession = None) -> dict[str, Any]:
        """Gets the conversations in a group.

        :param limit: The number of conversations to receive.
        :type limit: int
        :param session: aiohttp.ClientSession object
        :returns: A dict containing info similar to what is shown below:
        :rtype: dict[str, Any]

            .. code-block::

                {
                    "messages": [
                        {
                            "messageUid": "1#425961448584099",
                            "messageType": 1,
                            "alternativeMessageType": 1,
                            "body": "Hello World",
                            "createdTimestamp": "1663911908531",
                            "sender": {
                                "accountId": "8520698476712646544",
                                "onlineId": "VaultTec_Trading"
                            }
                        }
                    ],
                    "previous": "1#425961448584099",
                    "next": "1#425961448584099",
                    "reachedEndOfPage": false,
                    "messageCount": 1
                }

        """

        param = {"limit": limit}

        response = await self._request_builder.get(
            url=f"{BASE_PATH['gaming_lounge']}{API_PATH['conversation'].format(group_id=self.group_id)}",
            params=param, session=session)

        return await response.json()

    @create_session
    async def leave_group(self, session: ClientSession = None) -> None:
        """Leave the current group

        :raises: ``PSNAWPNotFound`` If you are not part of the group.

        """

        await self._request_builder.delete(
            url=f"{BASE_PATH['gaming_lounge']}{API_PATH['leave_group'].format(group_id=self.group_id)}",
            session=session)

    def __repr__(self) -> str:
        return f"<Group group_id:{self.group_id}>"

    def __str__(self) -> str:
        return f"Group ID: {self.group_id}"
