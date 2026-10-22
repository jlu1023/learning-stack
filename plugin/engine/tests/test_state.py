import datetime as dt

from vault_learning.state import State, apply_result

D = dt.date(2025, 10, 2)


def day(n):
    return D + dt.timedelta(days=n)


def test_first_pass_unseen_to_learning_interval_1():
    s = apply_result(State(), True, D)
    assert (s.mastery, s.mastery_since, s.review_interval, s.review) == ("learning", D, 1, day(1))


def test_learning_to_secure_needs_3_days():
    s = apply_result(State(), True, D)
    s2 = apply_result(s, True, day(1))                 # too soon: stays learning, ladder climbs
    assert s2.mastery == "learning" and s2.review_interval == 3
    s3 = apply_result(s2, True, day(4))
    assert s3.mastery == "secure" and s3.mastery_since == day(4) and s3.review_interval == 7


def test_secure_to_mastered_needs_21_days_after_secure():
    s = State("secure", D, D, D, 7)
    s = apply_result(s, True, day(7))                  # routine review, 7 days: stays secure
    assert s.mastery == "secure" and s.mastery_since == D and s.review_interval == 21
    s = apply_result(s, True, day(28))
    assert s.mastery == "mastered" and s.review_interval == 60


def test_ladder_tops_out_at_60():
    s = apply_result(State("mastered", D, D, D, 60), True, day(60))
    assert s.review_interval == 60 and s.review == day(120)


def test_fail_resets_interval_and_drops_one_level():
    s = apply_result(State("secure", D, D, D, 21), False, day(21))
    assert (s.mastery, s.review_interval, s.review, s.mastery_since) == ("learning", 1, day(22), day(21))
    s = apply_result(State(), False, D)                # unseen cannot drop further
    assert s.mastery == "unseen" and s.review == day(1)


def test_state_parsing_is_lenient():
    s = State.from_mapping({"mastery": "Secure", "review": "2025-10-06T10:00", "review_interval": "7"})
    assert s.mastery == "secure" and s.review == dt.date(2025, 10, 6) and s.review_interval == 7
    assert State.from_mapping({}).mastery == "unseen"
