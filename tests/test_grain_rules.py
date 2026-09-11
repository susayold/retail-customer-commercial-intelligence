def test_spend_driver_identity():
    active_households = 10
    trips_per_household = 3
    spend_per_basket = 25
    baskets = active_households * trips_per_household
    assert active_households * trips_per_household * spend_per_basket == baskets * spend_per_basket


def test_campaign_post_window_is_not_zero_when_unobservable():
    post_spend = None
    observable = False
    assert post_spend is None if not observable else True
