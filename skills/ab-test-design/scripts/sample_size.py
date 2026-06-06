"""
Sample size calculator for A/B tests.

Supports:
- Proportion tests (binary outcomes)
- Mean tests (continuous outcomes)

Usage:
    python sample_size.py --metric-type proportion --baseline 0.12 --mde 0.01
    python sample_size.py --metric-type mean --baseline-mean 45.2 --baseline-std 18.4 --mde 2.0
"""

from __future__ import annotations

import argparse
import math
import sys


def z_score(p: float) -> float:
    """Inverse standard normal CDF via rational approximation (Beasley-Springer-Moro)."""
    a = [-39.69683028665376, 220.9460984245205, -275.9285104469687,
         138.3577518672690, -30.66479806614716, 2.506628277459239]
    b = [-54.47609879822406, 161.5858368580409, -155.6989798598866,
         66.80131188771972, -13.28068155288572]
    c = [-0.007784894002430293, -0.3223964580411365, -2.400758277161838,
         -2.549732539343734, 4.374664141464968, 2.938163982698783]
    d = [0.007784695709041462, 0.3224671290700398, 2.445134137142996,
         3.754408661907416]
    p_low = 0.02425
    p_high = 1 - p_low

    if p < p_low:
        q = math.sqrt(-2 * math.log(p))
        return (((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / \
               ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    elif p <= p_high:
        q = p - 0.5
        r = q * q
        return (((((a[0]*r+a[1])*r+a[2])*r+a[3])*r+a[4])*r+a[5])*q / \
               (((((b[0]*r+b[1])*r+b[2])*r+b[3])*r+b[4])*r+1)
    else:
        q = math.sqrt(-2 * math.log(1 - p))
        return -(((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / \
                ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)


def sample_size_proportion(
    baseline: float,
    mde: float,
    alpha: float = 0.05,
    power: float = 0.80,
    relative: bool = False,
    two_sided: bool = True,
) -> int:
    """Sample size per arm for two-proportion test."""
    if relative:
        p2 = baseline * (1 + mde)
    else:
        p2 = baseline + mde

    if not 0 < p2 < 1:
        raise ValueError(f"Treatment proportion out of [0,1]: {p2}")

    z_a = z_score(1 - alpha / 2) if two_sided else z_score(1 - alpha)
    z_b = z_score(power)

    numerator = (z_a + z_b) ** 2 * (baseline * (1 - baseline) + p2 * (1 - p2))
    denominator = (baseline - p2) ** 2
    n = numerator / denominator
    return math.ceil(n)


def sample_size_mean(
    baseline_std: float,
    mde: float,
    alpha: float = 0.05,
    power: float = 0.80,
    two_sided: bool = True,
) -> int:
    """Sample size per arm for two-sample mean test."""
    z_a = z_score(1 - alpha / 2) if two_sided else z_score(1 - alpha)
    z_b = z_score(power)

    n = 2 * ((z_a + z_b) * baseline_std / mde) ** 2
    return math.ceil(n)


def main() -> int:
    parser = argparse.ArgumentParser(description="A/B test sample size calculator")
    parser.add_argument("--metric-type", choices=["proportion", "mean"], required=True)
    parser.add_argument("--baseline", type=float, help="Baseline proportion (for proportion test)")
    parser.add_argument("--baseline-mean", type=float, help="Baseline mean (for mean test, informational)")
    parser.add_argument("--baseline-std", type=float, help="Baseline std dev (for mean test)")
    parser.add_argument("--mde", type=float, required=True, help="Minimum detectable effect (absolute by default)")
    parser.add_argument("--relative", action="store_true", help="Treat MDE as relative (e.g., 0.05 = 5%% lift)")
    parser.add_argument("--alpha", type=float, default=0.05)
    parser.add_argument("--power", type=float, default=0.80)
    parser.add_argument("--one-sided", action="store_true")
    parser.add_argument("--variants", type=int, default=2, help="Total variants including control")
    parser.add_argument("--daily-exposure", type=float, help="Expected users per arm per day; prints runtime")
    args = parser.parse_args()

    two_sided = not args.one_sided

    if args.variants > 2:
        adjusted_alpha = args.alpha / (args.variants - 1)
        print(f"Bonferroni-adjusted alpha (for {args.variants - 1} treatments vs control): {adjusted_alpha:.5f}")
    else:
        adjusted_alpha = args.alpha

    if args.metric_type == "proportion":
        if args.baseline is None:
            print("ERROR: --baseline required for proportion test", file=sys.stderr)
            return 1
        n = sample_size_proportion(
            baseline=args.baseline,
            mde=args.mde,
            alpha=adjusted_alpha,
            power=args.power,
            relative=args.relative,
            two_sided=two_sided,
        )
    else:
        if args.baseline_std is None:
            print("ERROR: --baseline-std required for mean test", file=sys.stderr)
            return 1
        n = sample_size_mean(
            baseline_std=args.baseline_std,
            mde=args.mde,
            alpha=adjusted_alpha,
            power=args.power,
            two_sided=two_sided,
        )

    print(f"\nRequired sample size per arm: {n:,}")
    print(f"Total sample (all arms):       {n * args.variants:,}")

    if args.daily_exposure:
        days = math.ceil(n / args.daily_exposure)
        print(f"\nAt {args.daily_exposure:,.0f} users/arm/day:")
        print(f"  Minimum runtime: {days} days")
        if days < 14:
            print("  WARNING: Runtime < 14 days. Extend to cover one weekly cycle.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
