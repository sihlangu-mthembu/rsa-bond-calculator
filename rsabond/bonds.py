"""Static data for RSA conventional (fixed-rate) government bonds.

Source: National Treasury, "Schedule of domestic government bonds as at 31 July 2025"
(investor.treasury.gov.za). Coupon rates, maturity dates and interest payment dates are
transcribed as printed in that schedule.

Bonds marked with an asterisk in the schedule (staggered or special redemptions, e.g. R186)
are deliberately left out, because a single maturity date does not describe them.
Always check static data against the current Treasury schedule or the JSE listing before use.
"""

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class Bond:
    code: str
    coupon: float                      # annual coupon rate, e.g. 0.08 for 8.00%
    maturity: date
    coupon_days: tuple                 # ((month, day), (month, day)) interest payment dates

    @property
    def coupon_per_period(self) -> float:
        """Coupon paid each half-year per R100 nominal."""
        return 100 * self.coupon / 2


BONDS = {
    b.code: b
    for b in [
        Bond("R213", 0.0700, date(2031, 2, 28), ((2, 28), (8, 31))),
        Bond("R2030", 0.0800, date(2030, 1, 31), ((2, 28), (8, 31))),
        Bond("R2032", 0.0825, date(2032, 3, 31), ((3, 31), (9, 30))),
        Bond("R2033", 0.1000, date(2033, 3, 31), ((3, 31), (9, 30))),
        Bond("R2035", 0.08875, date(2035, 2, 28), ((2, 28), (8, 31))),
        Bond("R209", 0.0625, date(2036, 3, 31), ((3, 31), (9, 30))),
        Bond("R2037", 0.0850, date(2037, 1, 31), ((1, 31), (7, 31))),
        Bond("R2038", 0.10875, date(2038, 3, 31), ((3, 31), (9, 30))),
        Bond("R2040", 0.0900, date(2040, 1, 31), ((1, 31), (7, 31))),
        Bond("R214", 0.0650, date(2041, 2, 28), ((2, 28), (8, 31))),
        Bond("R2053", 0.11625, date(2053, 3, 31), ((3, 31), (9, 30))),
    ]
}


def get_bond(code: str) -> Bond:
    try:
        return BONDS[code.upper()]
    except KeyError:
        raise KeyError(f"Unknown bond {code!r}. Available: {', '.join(sorted(BONDS))}") from None
