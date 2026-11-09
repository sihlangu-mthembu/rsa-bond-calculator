"""Coupon schedules, accrued interest and pricing for RSA fixed-rate bonds.

Conventions used (stated so they can be checked and changed):
- Day count: actual/365, the South African bond market convention for accrued interest.
- Books close BOOKS_CLOSED_DAYS calendar days before each coupon date. A bond settling in
  that window trades ex-coupon: the buyer does not receive the next coupon, so accrued
  interest is negative.
- Discounting: semi-annual compounding, with time measured in half-years of 365/2 days.
  The JSE's official bond pricing formula differs in detail (e.g. rounding and the
  broken-period treatment), so prices here are close to, but not identical with, JSE prices.
"""

import calendar
from datetime import date, timedelta

from .bonds import Bond

BOOKS_CLOSED_DAYS = 10
HALF_YEAR_DAYS = 365 / 2


def _on(year: int, month: int, day: int) -> date:
    """Date in a given month, clipped to the month's last day (e.g. 31 Feb -> 28/29 Feb)."""
    return date(year, month, min(day, calendar.monthrange(year, month)[1]))


def coupon_dates(bond: Bond, start: date, end: date | None = None) -> list[date]:
    """All regular coupon dates strictly after `start`, up to and including the maturity date.

    The maturity date is always the final payment date. If a printed coupon date falls after
    maturity in the final year, it is dropped.
    """
    end = end or bond.maturity
    dates = []
    for year in range(start.year, bond.maturity.year + 1):
        for month, day in bond.coupon_days:
            d = _on(year, month, day)
            if start < d < bond.maturity and d <= end:
                dates.append(d)
    if start < bond.maturity <= end:
        dates.append(bond.maturity)
    return sorted(set(dates))


def previous_coupon_date(bond: Bond, settle: date) -> date:
    """Most recent regular coupon date on or before settlement."""
    candidates = [
        _on(y, m, d)
        for y in (settle.year - 1, settle.year)
        for m, d in bond.coupon_days
    ]
    return max(d for d in candidates if d <= settle)


def schedule(bond: Bond, settle: date) -> list[tuple[date, float]]:
    """Remaining cash flows per R100 nominal after `settle`: (payment date, amount).

    Regular coupons pay coupon/2. The final payment at maturity includes the redemption of
    100 plus a coupon: a full half-coupon if maturity falls on a coupon date, otherwise a
    coupon accrued actual/365 since the last regular coupon date (an assumption, see README).
    """
    flows = []
    dates = coupon_dates(bond, settle)
    for d in dates:
        if d == bond.maturity:
            on_cycle = any(d == _on(d.year, m, day) for m, day in bond.coupon_days)
            if on_cycle:
                coupon = bond.coupon_per_period
            else:
                last = previous_coupon_date(bond, d - timedelta(days=1))
                coupon = 100 * bond.coupon * (d - last).days / 365
            flows.append((d, coupon + 100))
        else:
            flows.append((d, bond.coupon_per_period))
    return flows


def is_ex_coupon(bond: Bond, settle: date, books_closed_days: int = BOOKS_CLOSED_DAYS) -> bool:
    """True if settlement falls in the books-closed window before the next payment."""
    upcoming = coupon_dates(bond, settle)
    if not upcoming:
        return False
    return (upcoming[0] - settle).days <= books_closed_days


def accrued_interest(bond: Bond, settle: date, books_closed_days: int = BOOKS_CLOSED_DAYS) -> float:
    """Accrued interest per R100 nominal, actual/365. Negative when trading ex-coupon."""
    if settle >= bond.maturity:
        return 0.0
    if is_ex_coupon(bond, settle, books_closed_days):
        next_date = coupon_dates(bond, settle)[0]
        return -100 * bond.coupon * (next_date - settle).days / 365
    last = previous_coupon_date(bond, settle)
    return 100 * bond.coupon * (settle - last).days / 365


def all_in_price(bond: Bond, settle: date, ytm: float, books_closed_days: int = BOOKS_CLOSED_DAYS) -> float:
    """All-in (dirty) price per R100 for an annual yield `ytm` compounded semi-annually."""
    flows = schedule(bond, settle)
    if flows and is_ex_coupon(bond, settle, books_closed_days):
        # Ex-coupon: the next coupon goes to the previous holder, so the buyer loses it.
        first_date = flows[0][0]
        if first_date == bond.maturity:
            flows[0] = (first_date, 100.0)          # keep the redemption, drop the coupon
        else:
            flows = flows[1:]                        # drop the whole coupon payment
    total = 0.0
    for d, amount in flows:
        t = (d - settle).days / HALF_YEAR_DAYS
        total += amount / (1 + ytm / 2) ** t
    return total


def clean_price(bond: Bond, settle: date, ytm: float, books_closed_days: int = BOOKS_CLOSED_DAYS) -> float:
    """Clean price = all-in price minus accrued interest."""
    return all_in_price(bond, settle, ytm, books_closed_days) - accrued_interest(bond, settle, books_closed_days)


def yield_from_price(bond: Bond, settle: date, price: float, clean: bool = True,
                     books_closed_days: int = BOOKS_CLOSED_DAYS) -> float:
    """Solve for the yield that reproduces `price` (clean by default) using bisection."""
    def f(y: float) -> float:
        pricer = clean_price if clean else all_in_price
        return pricer(bond, settle, y, books_closed_days) - price

    lo, hi = -0.5, 1.0
    if f(lo) * f(hi) > 0:
        raise ValueError("Price is outside the range this solver can match.")
    for _ in range(200):
        mid = (lo + hi) / 2
        if f(lo) * f(mid) <= 0:
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2
