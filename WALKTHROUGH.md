# Walkthrough

Read this before any interview where this project might come up. Each section explains what a file does and the questions you are likely to be asked about it.

## `rsabond/bonds.py`: the data

- `Bond` is a **frozen dataclass**: a simple record type whose fields cannot be changed after creation. That suits static data: nothing should accidentally change a bond's coupon.
- `coupon_per_period` is a **property**: computed on access. 8.25% a year paid twice a year gives 4.125 per R100 each half-year.
- `BONDS` is a dictionary built with a **dict comprehension**, keyed by bond code so lookups are instant.
- `get_bond()` looks a bond up and, if the code is wrong, raises a `KeyError` with a helpful message listing valid codes. `from None` hides the less useful original error.

*Likely question:* "Why hard-code the data?" Answer: it is small, rarely changes and must be traceable to a source document. A next step would be loading it from a CSV or an API.

## `rsabond/calc.py`: the finance

- `_on()` builds a date but **clips the day to the month's end**, so "31" in a 30-day month becomes the 30th, and 28 Feb stays valid in any year.
- `coupon_dates()` loops through every year from settlement to maturity, creates both coupon dates for each year, and keeps those strictly after settlement and before maturity. Maturity is always added as the last payment.
- `previous_coupon_date()` finds the latest coupon date on or before settlement; accrued interest counts days from here.
- `schedule()` turns dates into cash flows. Regular payments are half the annual coupon. The final payment is 100 (the redemption) plus a coupon.
- `is_ex_coupon()`: South African bonds stop registering new owners for the next coupon shortly before it is paid ("books closed"). If you settle in that window, the seller keeps the coupon.
- `accrued_interest()`: coupon × days since last coupon ÷ 365. In the ex-coupon window it is **negative**: coupon × days until the next coupon ÷ 365, because the buyer pays less to compensate for missing that coupon.
- `all_in_price()`: discounts every remaining cash flow at the yield, compounding semi-annually: `amount / (1 + ytm/2) ** t`, where `t` is time in half-years. Ex-coupon, the next coupon is removed first.
- `clean_price()` = all-in price minus accrued interest. Markets quote clean prices so that prices do not jump on coupon dates.
- `yield_from_price()` uses **bisection**: it starts with a low and a high yield that bracket the answer, and repeatedly halves the interval. 200 halvings give far more precision than needed. Price falls as yield rises, which is why this works.

*Likely questions:* "Why does accrued interest go negative?" (ex-coupon, above). "Why is the clean price below 100?" (the yield is above the coupon rate). "What does `t` measure?" (half-years, because coupons are semi-annual).

## `rsabond/cli.py`: the command line

- Uses `argparse` **subcommands** (`list`, `schedule`, `price`, `yield`), each with its own arguments.
- `--settle` is parsed with `date.fromisoformat`, so dates are written YYYY-MM-DD.
- Yields are entered in percent (8.9) and divided by 100 internally.
- `main()` returns 0 for success, which the shell uses as the exit code.

## `tests/test_calc.py`: the tests

Eleven `pytest` tests check the things a fixed income person would check by hand: coupon dates for R2032, final payment = 100 + coupon, zero accrued on a coupon date, the actual/365 formula, negative accrued when ex-coupon, a price near par when the yield equals the coupon, price falling as yield rises, the yield solver recovering the input yield, all-in = clean + accrued, a bad code raising an error, and the CLI running end to end. `pytest.approx` compares decimals without failing on tiny rounding differences.

## `.github/workflows/tests.yml`: continuous integration

On every push, GitHub starts a fresh Linux machine, installs the package with Python 3.10 and 3.12, runs the `ruff` linter and runs the tests. The badge at the top of the README shows whether they pass.

## `pyproject.toml`: packaging

Defines the package name, version and dependencies, and the `rsabond` command (`[project.scripts]` points it at `rsabond.cli:main`). `pip install -e .` installs it in editable mode, so code changes take effect immediately.

## Ideas to extend it yourself

1. Add a `duration` command (modified duration and DV01 per R100).
2. Load bond data from a CSV instead of `bonds.py`.
3. Add the R186's staggered redemptions.
4. Compare your prices with published JSE prices for one day and document the differences.
