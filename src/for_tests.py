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
    # print(await client.get_profile_legacy())
    async for friend in client.friends_list(5):
        print(friend)
    async for blocked in client.blocked_list():
        print(blocked)
    print([available async for available in client.available_to_play()])
    groups = [group async for group in client.get_groups()]
    print(groups)


# asyncio.run(client_test())
async def user_test():
    # Getting user from online
    example_user_1 = await psnawp.user(online_id="some user name")
    # example_user_2 = psnawp.user(online_id="test")
    print(example_user_1.online_id)
    print(example_user_1.account_id)
    print(example_user_1.prev_online_id)
    print(await example_user_1.profile())
    print(await example_user_1.get_presence())
    print(await example_user_1.friendship())
    print(await example_user_1.is_blocked())


asyncio.run(user_test())

# Getting user from Account ID
# user_account_id = psnawp.user(account_id='9122947611907501295')
# print(user_account_id.online_id)
#
# # Sending Message
# group = psnawp.group(group_id='38335156987791a6750a33ae452ec8666177b65e-103')
# print(group.get_group_information())
# print(group.get_conversation(10))
# print(group.send_message("Hello World"))
# print(group.change_name("API Testing 3"))
# print(group.leave_group())
#
# # Creating new group
# new_group = psnawp.group(users_list=[example_user_1, example_user_2])
#
# search = psnawp.search()
# print(search.get_title_id(title_name="GTA 5"))
# print(search.universal_search("GTA 5"))

# Get Play Times (PS4, PS5 above only)
# titles_with_stats = client.title_stats()
