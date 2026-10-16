"""UK home retrofit market model: size and scenario analysis (England).

Question: how large is the spend needed to bring England's homes below
EPC band C up to band C by 2035, and how much of it does public money cover?

Run:  python src/model.py
Outputs are written to ../outputs/.
"""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs"
OUT.mkdir(exist_ok=True)

# ---------------------------------------------------------------- inputs
inp = pd.read_csv(ROOT / "data" / "inputs.csv").set_index("parameter")["value"]


def num(name):
    return float(inp[name])


STOCK = {
    "Private rented": num("dwellings_private_rented"),
    "Social": num("dwellings_social"),
    "Owner occupied": num("dwellings_owner_occupied"),
}
SHARE_D = num("share_epc_d")
SHARE_EG = num("share_epc_e_to_g")
COST_D = num("cost_d_to_c")
COST_EG = num("cost_e_to_g_to_c")
START = int(num("model_start_year"))
END = int(num("owner_occupier_horizon_year"))
YEARS = list(range(START, END + 1))
DEADLINE = {
    "Private rented": int(num("prs_deadline_year")),   # sourced
    "Social": int(num("social_deadline_year")),        # assumption
    "Owner occupied": int(num("owner_occupier_horizon_year")),  # assumption
}
PUBLIC_FUNDING = num("public_funding_total")

# Share of below-C homes upgraded by the deadline year (assumptions).
SCENARIOS = {
    "Slow":        {"Private rented": 0.60, "Social": 0.50, "Owner occupied": 0.15},
    "Base":        {"Private rented": 0.85, "Social": 0.80, "Owner occupied": 0.35},
    "Accelerated": {"Private rented": 0.95, "Social": 0.95, "Owner occupied": 0.60},
}


# ---------------------------------------------------------------- model
def cost_per_below_c_home(cost_d=COST_D, cost_eg=COST_EG, share_d=SHARE_D, share_eg=SHARE_EG):
    """Weighted average cost to lift a below-C home to band C."""
    return (share_d * cost_d + share_eg * cost_eg) / (share_d + share_eg)


def run(uptake, cost_d=COST_D, cost_eg=COST_EG, share_d=SHARE_D, share_eg=SHARE_EG):
    """Return a DataFrame of homes upgraded and spend (GBP) by year and tenure.

    Each tenure's cumulative uptake follows a quadratic curve from 0 to its target
    at its deadline year, then holds. This means annual deployment rises steadily
    as supply chains and installer capacity build, instead of starting at full speed.
    Annual homes = change in cumulative uptake x below-C homes.
    """
    avg_cost = cost_per_below_c_home(cost_d, cost_eg, share_d, share_eg)
    rows = []
    for tenure, stock in STOCK.items():
        below_c = stock * (share_d + share_eg)
        span = DEADLINE[tenure] - START + 1
        cum_prev = 0.0
        for y in YEARS:
            cum = uptake[tenure] * min(1.0, (y - START + 1) / span) ** 2
            homes = below_c * (cum - cum_prev)
            rows.append({"year": y, "tenure": tenure, "homes": homes,
                         "spend_gbp": homes * avg_cost})
            cum_prev = cum
    return pd.DataFrame(rows)


def total_spend(uptake, **kw):
    return run(uptake, **kw)["spend_gbp"].sum()


# ---------------------------------------------------------------- results
def main():
    below_c_homes = sum(STOCK.values()) * (SHARE_D + SHARE_EG)
    tam = below_c_homes * cost_per_below_c_home()
    print(f"Homes below band C: {below_c_homes/1e6:.2f}m")
    print(f"Average cost per below-C home: GBP {cost_per_below_c_home():,.0f}")
    print(f"Full upgrade of every below-C home (TAM): GBP {tam/1e9:.1f}bn")

    summary, detail = [], []
    for name, up in SCENARIOS.items():
        df = run(up)
        df["scenario"] = name
        detail.append(df)
        spend = df["spend_gbp"].sum()
        homes = df["homes"].sum()
        annual = df.groupby("year")["spend_gbp"].sum()
        summary.append({
            "scenario": name,
            "homes_upgraded_m": homes / 1e6,
            "total_spend_gbp_bn": spend / 1e9,
            "peak_year": int(annual.idxmax()),
            "peak_annual_spend_gbp_bn": annual.max() / 1e9,
            "public_funding_share_pct": 100 * PUBLIC_FUNDING / spend,
            "private_capital_needed_gbp_bn": max(spend - PUBLIC_FUNDING, 0) / 1e9,
        })
    summary = pd.DataFrame(summary).round(2)
    detail = pd.concat(detail)
    summary.to_csv(OUT / "scenario_summary.csv", index=False)
    detail.round(0).to_csv(OUT / "scenario_detail_by_year_tenure.csv", index=False)
    print("\n", summary.to_string(index=False))

    # ---- sensitivity (one at a time, base case, +/- ranges are assumptions)
    base_up = SCENARIOS["Base"]
    base = total_spend(base_up)
    tests = {
        "Cost per D-rated home (+/-30%)": (dict(cost_d=COST_D * 0.7), dict(cost_d=COST_D * 1.3)),
        "Cost per E to G home (+/-30%)": (dict(cost_eg=COST_EG * 0.7), dict(cost_eg=COST_EG * 1.3)),
        "Owner-occupier uptake (15% / 60%)": ({**base_up, "Owner occupied": 0.15}, {**base_up, "Owner occupied": 0.60}),
        "Social uptake (50% / 95%)": ({**base_up, "Social": 0.50}, {**base_up, "Social": 0.95}),
        "Private rented uptake (60% / 95%)": ({**base_up, "Private rented": 0.60}, {**base_up, "Private rented": 0.95}),
        "Share of homes below C (+/-3 pts, within D)": (dict(share_d=SHARE_D - 0.03), dict(share_d=SHARE_D + 0.03)),
    }
    sens = []
    for label, (lo, hi) in tests.items():
        def calc(arg):
            if set(arg) <= set(STOCK):  # uptake dict
                return total_spend(arg)
            return total_spend(base_up, **arg)
        sens.append({"driver": label, "low_gbp_bn": calc(lo) / 1e9, "high_gbp_bn": calc(hi) / 1e9})
    sens = pd.DataFrame(sens)
    sens["swing_gbp_bn"] = (sens["high_gbp_bn"] - sens["low_gbp_bn"]).abs()
    sens = sens.sort_values("swing_gbp_bn", ascending=False).round(2)
    sens.to_csv(OUT / "sensitivity.csv", index=False)
    print("\nBase case total (GBP bn):", round(base / 1e9, 2))
    print(sens.to_string(index=False))

    # ---- two-way table: owner-occupier uptake x cost multiplier
    ups = [0.15, 0.25, 0.35, 0.45, 0.60]
    mults = [0.7, 0.85, 1.0, 1.15, 1.3]
    grid = pd.DataFrame(
        [[total_spend({**base_up, "Owner occupied": u}, cost_d=COST_D * m, cost_eg=COST_EG * m) / 1e9
          for u in ups] for m in mults],
        index=[f"cost x{m}" for m in mults], columns=[f"OO uptake {int(u*100)}%" for u in ups]).round(1)
    grid.to_csv(OUT / "two_way_table.csv")

    # ---- charts
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
    colours = {"Private rented": "#1b4965", "Social": "#5fa8d3", "Owner occupied": "#bee9e8"}

    # 1: base-case annual spend by tenure
    d = detail[detail.scenario == "Base"].pivot(index="year", columns="tenure", values="spend_gbp") / 1e9
    fig, ax = plt.subplots(figsize=(8, 4.5))
    d[list(colours)].plot.bar(stacked=True, ax=ax, color=list(colours.values()), width=0.8)
    ax.set_title("Base case: annual retrofit spend to reach EPC C, England (GBP bn)", loc="left")
    ax.set_xlabel("")
    ax.set_ylabel("GBP bn")
    ax.tick_params(axis="x", rotation=0)
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(OUT / "chart_base_case_annual_spend.png", dpi=160)
    plt.close(fig)

    # 2: scenario totals vs public funding
    fig, ax = plt.subplots(figsize=(7, 4.2))
    ax.bar(summary["scenario"], summary["total_spend_gbp_bn"], color="#1b4965", width=0.55)
    ax.axhline(PUBLIC_FUNDING / 1e9, color="#c1121f", ls="--",
               label="Warm Homes Plan public funding (GBP 15bn)")
    ax.legend(frameon=False, loc="upper left")
    for i, v in enumerate(summary["total_spend_gbp_bn"]):
        ax.text(i, v + 0.8, f"{v:.0f}", ha="center")
    ax.set_title("Total spend 2026 to 2035 by scenario vs public funding (GBP bn)", loc="left")
    ax.set_ylabel("GBP bn")
    fig.tight_layout()
    fig.savefig(OUT / "chart_scenarios_vs_public_funding.png", dpi=160)
    plt.close(fig)

    # 3: tornado
    s = sens.iloc[::-1]
    fig, ax = plt.subplots(figsize=(8, 4.2))
    lo = s[["low_gbp_bn", "high_gbp_bn"]].min(axis=1)
    hi = s[["low_gbp_bn", "high_gbp_bn"]].max(axis=1)
    ax.barh(s["driver"], hi - lo, left=lo, color="#5fa8d3")
    ax.axvline(base / 1e9, color="#1b4965")
    ax.set_xlim(lo.min() - 2, hi.max() + 2)
    ax.set_title(f"Sensitivity of base-case total (GBP {base/1e9:.0f}bn)", loc="left")
    ax.set_xlabel("Total spend 2026 to 2035 (GBP bn)")
    fig.tight_layout()
    fig.savefig(OUT / "chart_sensitivity.png", dpi=160)
    plt.close(fig)


if __name__ == "__main__":
    main()
