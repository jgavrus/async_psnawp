import inspect

import pytest

from psnawp_api.core.psnawp_exceptions import PSNAWPNotFound
from tests.unit_tests import my_vcr


@pytest.mark.asyncio.vcr()
def test_game_title__np_communication_id(psnawp_fixture):
    with my_vcr.use_cassette(f"{inspect.currentframe().f_code.co_name}.yaml"):
        game_title = psnawp_fixture.game_title(title_id="PPSA03420_00")
        assert game_title.np_communication_id == "NPWR21647_00"


@pytest.mark.asyncio.vcr()
def test_game_title__wrong_title_id(psnawp_fixture):
    with my_vcr.use_cassette(f"{inspect.currentframe().f_code.co_name}.yaml"):
        with pytest.raises(PSNAWPNotFound):
            psnawp_fixture.game_title(title_id="SSSA01325_00")


@pytest.mark.asyncio.vcr()
def test_game_title__get_title_details(psnawp_fixture):
    with my_vcr.use_cassette(f"{inspect.currentframe().f_code.co_name}.yaml"):
        game_title = psnawp_fixture.game_title(title_id="PPSA03420_00")
        title_details = game_title.get_details()
        assert title_details[0].get("name") == "Grand Theft Auto V (PlayStation®5)"


@pytest.mark.asyncio.vcr()
def test_game_title__trophies(psnawp_fixture):
    with my_vcr.use_cassette(f"{inspect.currentframe().f_code.co_name}.yaml"):
        game_title = psnawp_fixture.game_title(title_id="PPSA03420_00")
        total_count = 0
        actual_count = 0
        for trophy in game_title.trophies(platform="PS5", trophy_group_id="all"):
            actual_count = trophy.total_items_count
            total_count += 1
            assert trophy.trophy_id is not None
            assert trophy.trophy_hidden is not None
            assert trophy.trophy_type is not None
            assert trophy.trophy_name is not None
            assert trophy.trophy_detail is not None
            assert trophy.trophy_icon_url is not None
            assert trophy.trophy_group_id is not None
        assert total_count == actual_count


@pytest.mark.asyncio.vcr()
def test_game_title__trophy_groups_summary(psnawp_fixture):
    with my_vcr.use_cassette(f"{inspect.currentframe().f_code.co_name}.yaml"):
        game_title = psnawp_fixture.game_title(title_id="PPSA01325_00")
        trophy_groups_summary = game_title.trophy_groups_summary(platform="PS5")
        assert trophy_groups_summary.trophy_set_version is not None
        assert trophy_groups_summary.trophy_title_name is not None
        assert trophy_groups_summary.trophy_title_icon_url is not None
        assert trophy_groups_summary.trophy_title_platform is not None
        assert trophy_groups_summary.defined_trophies is not None

        for trophy_group_summary in trophy_groups_summary.trophy_groups:
            assert trophy_group_summary.trophy_group_id is not None
            assert trophy_group_summary.trophy_group_name is not None
            assert trophy_group_summary.trophy_group_icon_url is not None
            assert trophy_group_summary.defined_trophies is not None


@pytest.mark.asyncio.vcr()
def test_game_title__trophies_game_not_owned_by_user(psnawp_fixture):
    with my_vcr.use_cassette(f"{inspect.currentframe().f_code.co_name}.yaml"):
        with pytest.raises(PSNAWPNotFound):
            psnawp_fixture.game_title(title_id="PPSA03420_00", account_id="me")


@pytest.mark.asyncio.vcr()
def test_game_title__trophy_groups_summary_game_not_owned_by_user(psnawp_fixture):
    with my_vcr.use_cassette(f"{inspect.currentframe().f_code.co_name}.yaml"):
        with pytest.raises(PSNAWPNotFound):
            psnawp_fixture.game_title(title_id="PPSA01325_00", account_id="me")


@pytest.mark.asyncio.vcr()
def test_game_title__trophies_invalid_np_communication_id(psnawp_fixture):
    with my_vcr.use_cassette(f"{inspect.currentframe().f_code.co_name}.yaml"):
        with pytest.raises(PSNAWPNotFound):
            game_title = psnawp_fixture.game_title(title_id="PPSA03420_00", account_id="me", np_communication_id="SSSA01325_00")
            for trophy in game_title.trophies(platform="PS5", trophy_group_id="all"):
                print(trophy)


@pytest.mark.asyncio.vcr()
def test_game_title__trophy_groups_summary_invalid_np_communication_id(psnawp_fixture):
    with my_vcr.use_cassette(f"{inspect.currentframe().f_code.co_name}.yaml"):
        with pytest.raises(PSNAWPNotFound):
            game_title = psnawp_fixture.game_title(title_id="PPSA01325_00", account_id="me", np_communication_id="SSSA01325_00")
            trophy_groups_summary = game_title.trophy_groups_summary(platform="PS5")
            for trophy_group_summary in trophy_groups_summary.trophy_groups:
                print(trophy_group_summary)
