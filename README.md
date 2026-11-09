# rsa-bond-calculator

![tests](https://github.com/sihlangu-mthembu/rsa-bond-calculator/actions/workflows/tests.yml/badge.svg)

A Python command-line tool and library for South African government bonds: **coupon schedules, accrued interest, clean and all-in prices, and yields**, using coupon and maturity data from National Treasury's published schedule.

It exists because getting this static data right matters. While testing AI models, I found one stating the wrong coupon months and maturity for the R2030 and citing Treasury as its source. Wrong dates flow straight into accrued interest and settlement amounts, so this tool takes its dates from the source document instead of from memory.

## Quick start

```bash
pip install -e ".[dev]"
rsabond list                                              # bonds, coupons, maturities, coupon dates
rsabond schedule R2032 --settle 2026-11-09                # remaining cash flows per R100
rsabond price R2032 --settle 2026-11-09 --ytm 8.9         # accrued, clean and all-in price
rsabond yield R2035 --settle 2026-11-09 --price 95        # yield from a clean price
pytest -q                                                 # 11 tests
```

Example:

```
$ rsabond price R2032 --settle 2026-11-09 --ytm 8.9
R2032 settling 2026-11-09 at 8.900%
  Ex-coupon:        no
  Accrued interest: 0.90411
  Clean price:      97.22148
  All-in price:     98.12559
```

## Conventions

| Item | Convention used |
| --- | --- |
| Day count | Actual/365 for accrued interest |
| Coupons | Semi-annual, half the annual rate on each printed coupon date |
| Books closed | 10 calendar days before each payment; settling inside that window is ex-coupon, so accrued interest is negative and the buyer does not get the next coupon |
| Discounting | Semi-annual compounding, time measured in half-years of 365/2 days |

These are close to, but **not identical with, the JSE's official bond pricing formula** (which has its own broken-period and rounding rules). Treat prices as close approximations, not settlement figures.

## Data

`rsabond/bonds.py` holds 11 conventional fixed-rate bonds, transcribed from National Treasury's *Schedule of domestic government bonds as at 31 July 2025*. Bonds the schedule marks as having staggered or special redemptions (such as R186) are left out.

**One data point to note:** the schedule lists the **R2030** as maturing on 31 January 2030 with interest dates of 28/02 and 31/08. Because the maturity date is not a coupon date, the final payment here includes a coupon accrued actual/365 from 31 August 2029 to maturity. That treatment is an assumption; check the R2030's listing terms before relying on its final cash flow.

## Project structure

```
rsa-bond-calculator/
├── rsabond/
│   ├── bonds.py   # bond static data (Treasury schedule)
│   ├── calc.py    # coupon dates, accrued interest, price, yield
│   └── cli.py     # command-line interface
├── tests/test_calc.py
├── .github/workflows/tests.yml   # runs ruff and pytest on every push
├── WALKTHROUGH.md                 # file-by-file explanation
└── pyproject.toml
```

## About

Built with AI assistance (Claude) by Sihlangu Mthembu, Economics & Politics (UCT); Fixed Income and Quantitative Methods for Investment (Milpark, NQF 8). Companion to [sa-rates-toolkit](https://github.com/sihlangu-mthembu/sa-rates-toolkit).
