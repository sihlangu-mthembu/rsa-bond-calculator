"""Command-line interface.

Examples:
    rsabond list
    rsabond schedule R2032 --settle 2026-11-09
    rsabond price R2032 --settle 2026-11-09 --ytm 8.95
    rsabond yield R2032 --settle 2026-11-09 --price 97.50
"""

import argparse
from datetime import date

from .bonds import BONDS, get_bond
from .calc import accrued_interest, all_in_price, clean_price, is_ex_coupon, schedule, yield_from_price


def _date(s: str) -> date:
    return date.fromisoformat(s)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="rsabond", description="RSA government bond calculator")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list", help="list available bonds")

    for name, help_text in [("schedule", "remaining cash flows"), ("price", "price from yield"),
                            ("yield", "yield from clean price")]:
        p = sub.add_parser(name, help=help_text)
        p.add_argument("bond", help="bond code, e.g. R2032")
        p.add_argument("--settle", type=_date, default=date.today(), help="settlement date YYYY-MM-DD")
        if name == "price":
            p.add_argument("--ytm", type=float, required=True, help="yield in percent, e.g. 8.95")
        if name == "yield":
            p.add_argument("--price", type=float, required=True, help="clean price per R100")

    args = parser.parse_args(argv)

    if args.command == "list":
        print(f"{'Bond':<7}{'Coupon':>8}  {'Maturity':<12}Coupon dates")
        for b in sorted(BONDS.values(), key=lambda b: b.maturity):
            days = " & ".join(f"{d:02d}/{m:02d}" for m, d in b.coupon_days)
            print(f"{b.code:<7}{b.coupon:>8.3%}  {b.maturity.isoformat():<12}{days}")
        return 0

    bond = get_bond(args.bond)
    if args.command == "schedule":
        print(f"{bond.code} cash flows per R100 nominal after {args.settle}:")
        for d, amount in schedule(bond, args.settle):
            print(f"  {d.isoformat()}  {amount:>10.4f}")
    elif args.command == "price":
        y = args.ytm / 100
        ai = accrued_interest(bond, args.settle)
        print(f"{bond.code} settling {args.settle} at {args.ytm:.3f}%")
        print(f"  Ex-coupon:        {'yes' if is_ex_coupon(bond, args.settle) else 'no'}")
        print(f"  Accrued interest: {ai:.5f}")
        print(f"  Clean price:      {clean_price(bond, args.settle, y):.5f}")
        print(f"  All-in price:     {all_in_price(bond, args.settle, y):.5f}")
    elif args.command == "yield":
        y = yield_from_price(bond, args.settle, args.price)
        print(f"{bond.code} settling {args.settle} at clean price {args.price:.4f}: yield {y:.4%}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
