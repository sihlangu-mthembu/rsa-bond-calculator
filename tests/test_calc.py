from datetime import date

import pytest

from rsabond import (
    accrued_interest,
    all_in_price,
    clean_price,
    coupon_dates,
    get_bond,
    is_ex_coupon,
    schedule,
    yield_from_price,
)
from rsabond.cli import main


def test_r2032_pays_on_31_march_and_30_september():
    dates = coupon_dates(get_bond("R2032"), date(2026, 1, 1), date(2027, 12, 31))
    assert dates == [date(2026, 3, 31), date(2026, 9, 30), date(2027, 3, 31), date(2027, 9, 30)]


def test_final_payment_is_redemption_plus_coupon():
    bond = get_bond("R2032")
    final_date, final_amount = schedule(bond, date(2031, 12, 1))[-1]
    assert final_date == bond.maturity
    assert final_amount == pytest.approx(100 + 4.125)


def test_accrued_is_zero_on_coupon_date():
    assert accrued_interest(get_bond("R2032"), date(2026, 9, 30)) == pytest.approx(0.0)


def test_accrued_actual_365():
    # 30 days after the 30 Sep coupon: 8.25 * 30 / 365
    assert accrued_interest(get_bond("R2032"), date(2026, 10, 30)) == pytest.approx(8.25 * 30 / 365)


def test_ex_coupon_window_gives_negative_accrued():
    bond = get_bond("R2032")
    settle = date(2027, 3, 25)               # 6 days before the 31 Mar coupon
    assert is_ex_coupon(bond, settle)
    assert accrued_interest(bond, settle) == pytest.approx(-8.25 * 6 / 365)


def test_price_at_coupon_yield_on_coupon_date_is_close_to_par():
    bond = get_bond("R2032")
    assert clean_price(bond, date(2026, 9, 30), 0.0825) == pytest.approx(100, abs=0.15)


def test_higher_yield_means_lower_price():
    bond = get_bond("R2040")
    settle = date(2026, 11, 9)
    assert clean_price(bond, settle, 0.11) < clean_price(bond, settle, 0.10)


def test_yield_round_trip():
    bond = get_bond("R2035")
    settle = date(2026, 11, 9)
    price = clean_price(bond, settle, 0.0975)
    assert yield_from_price(bond, settle, price) == pytest.approx(0.0975, abs=1e-8)


def test_all_in_equals_clean_plus_accrued():
    bond = get_bond("R213")
    settle = date(2026, 11, 9)
    assert all_in_price(bond, settle, 0.09) == pytest.approx(
        clean_price(bond, settle, 0.09) + accrued_interest(bond, settle))


def test_unknown_bond_raises():
    with pytest.raises(KeyError):
        get_bond("R999")


def test_cli_price_runs(capsys):
    assert main(["price", "R2032", "--settle", "2026-11-09", "--ytm", "8.9"]) == 0
    assert "Clean price" in capsys.readouterr().out
