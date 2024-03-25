import asyncio

from psnawp_api import PSNAWP

token = ''

psnawp = PSNAWP(token)


async def client_test():
    # This is you
    client = await psnawp.me()
    print(await client.online_id())
    print(await client.account_id())
    print(await client.get_account_devices())
    print(await client.get_profile_legacy())
    async for friend in client.friends_list(5):
        print(friend)
    async for blocked in client.blocked_list():
        print(blocked)
    print([available async for available in client.available_to_play()])
    groups = [group async for group in client.get_groups()]
    print(groups)


# asyncio.run(client_test())
async def user_by_online_id_test():
    # Getting user from online
    example_user_1 = await psnawp.user(online_id="")
    print(example_user_1.online_id)
    print(example_user_1.account_id)
    print(example_user_1.prev_online_id)
    print(await example_user_1.profile())
    print(await example_user_1.get_presence())
    print(await example_user_1.friendship())
    print(await example_user_1.is_blocked())

    user_account_id = await psnawp.user(account_id='')
    print(user_account_id.online_id)






async def groups():
    # Sending Message
    group = await psnawp.group(group_id='')
    print(await group.get_group_information())
    print(await group.get_conversation(10))
    print(await group.send_message("Hello World"))
    print(await group.change_name("API Testing 3"))
    print(await group.leave_group())
    example_user_1 = await psnawp.user(online_id="jeygavrus")
    example_user_2 = await psnawp.user(online_id="test")
    # Creating new group
    new_group = await psnawp.group(users_list=[example_user_1, example_user_2])

async def game_search():
    # search = await psnawp.search()
    # print(await search.get_title_id(title_name="GTA 5"))
    # print(await search.universal_search("GTA 5"))
    client = await psnawp.me()
    # Get Play Times (PS4, PS5 above only)
    async for title in client.title_stats():
        print(title)
        break

async def game_trophies():
    game_title = 'PPSA08668_00' # FF7.2
    client = await psnawp.me()

    _id = await client.account_id()
    game = await psnawp.game_title(title_id=game_title, account_id=_id)
    result = await game.get_details()
    print(result)
    print(await game.trophy_groups_summary('PS5'))
    user_game_trophy = await client.trophy_groups_summary(game.np_communication_id, "PS5", include_metadata=True)
    print(user_game_trophy)
    async for trophy in game.trophies('PS5'):
        print(trophy)
        break

asyncio.run(client_test())
asyncio.run(user_by_online_id_test())
asyncio.run(game_search())
asyncio.run(game_trophies())
