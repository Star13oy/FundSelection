from app.store import WATCHLIST, add_watchlist, filter_funds, get_fund, list_watchlist, remove_watchlist


def setup_function() -> None:
    WATCHLIST.clear()


def test_filter_by_channel_and_category() -> None:
    funds = filter_funds(channel="场内", category="行业", min_years=None, max_fee=None, keyword=None)
    assert len(funds) == 1
    assert funds[0].code == "512480"


def test_filter_by_numeric_constraints() -> None:
    funds = filter_funds(channel=None, category=None, min_years=10, max_fee=0.7, keyword=None)
    codes = {f.code for f in funds}
    assert "510300" in codes
    assert "000012" in codes


def test_filter_by_keyword() -> None:
    funds = filter_funds(channel=None, category=None, min_years=None, max_fee=None, keyword="蓝筹")
    assert {f.code for f in funds} == {"005827"}


def test_watchlist_crud() -> None:
    assert add_watchlist("510300")
    assert get_fund("510300") is not None
    items = list_watchlist()
    assert len(items) == 1
    assert items[0].code == "510300"

    remove_watchlist("510300")
    assert list_watchlist() == []


def test_watchlist_add_fail_for_unknown_fund() -> None:
    assert add_watchlist("NOPE") is False
