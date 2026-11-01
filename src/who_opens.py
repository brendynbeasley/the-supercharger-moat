"""Katz and Shapiro (1985), second prediction: firms with large networks resist compatibility and
firms with small networks seek it. Who opened their fast chargers to the other side's cars?

Uses the public DC fast-charging stations in the DOE Alternative Fuels Data Center file
(data/processed/afdc_dcfast_stations.csv, written by src/supercharger_moat.py), as of 1 November 2026.

Two tests:
  1. Across charging networks: is a network's share of ports with a Tesla-style (NACS, SAE J3400)
     connector lower for bigger networks, holding the year a station opened fixed?
  2. Inside Tesla: among Superchargers opened 2020-2025 (third-generation hardware or later, which
     can serve other brands), did Tesla keep the stations exclusive where its local share of fast
     charging is highest?

Run from the repository root, after src/supercharger_moat.py:
    python src/who_opens.py
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy import stats

ROOT = Path(__file__).resolve().parent.parent
STATIONS = ROOT / "data" / "processed" / "afdc_dcfast_stations.csv"
OUT = ROOT / "results"

RADIUS_KM = 25                 # same local market as the main script
MIN_NETWORK_PORTS = 150        # networks big enough to describe by name (judgment)
TESLA_YEARS = range(2020, 2026)  # Ford's access (29 Feb 2024) excluded second-generation (V2) sites, which opened before 2020
ACCESS = {"NACS partner enabled": "open", "Open to all vehicles": "open", "Open to Teslas only": "tesla only"}
NAMES = {"eVgo Network": "EVgo", "ChargePoint Network": "ChargePoint", "Blink Network": "Blink",
         "IONNA": "Ionna", "RIVIAN_ADVENTURE": "Rivian Adventure Network", "FORD_CHARGE": "Ford Charge",
         "WALMART": "Walmart", "BP_PULSE": "bp pulse", "MERCEDES_BENZ": "Mercedes-Benz", "RED_E": "Red E",
         "SHELL_RECHARGE": "Shell Recharge", "Non-Networked": "Non-networked", "EV Connect": "EV Connect"}


def load():
    st = pd.read_csv(STATIONS, parse_dates=["open_date"])
    print(f"Loaded {len(st):,} public DC fast stations, {st['dc_ports'].sum():,} ports")
    nodate = st["open_date"].isna()
    print(f"  dropped {nodate.sum():,} stations with no opening date")
    st = st[~nodate].copy()
    st["open_year"] = st["open_date"].dt.year
    st["has_nacs"] = st["connectors"].fillna("").str.contains("TESLA").astype(int)
    st["has_ccs"] = st["connectors"].fillna("").str.contains("J1772COMBO")
    acc = st["access_days_time"].fillna("").str.extract("(" + "|".join(ACCESS) + ")")[0]
    st["tesla_access"] = acc.map(ACCESS)
    return st


def local_shares(st, radius):
    """For each station: Tesla ports, other ports and the Tesla share within `radius` km (itself included)."""
    lat, lon = np.radians(st["lat"].values), np.radians(st["lon"].values)
    tesla = st["network"].eq("Tesla").values
    ports = st["dc_ports"].values
    t_near, o_near = np.zeros(len(st)), np.zeros(len(st))
    for i in range(len(st)):
        box = (np.abs(st["lat"].values - st["lat"].values[i]) < 0.5)
        a = (np.sin((lat[box] - lat[i]) / 2) ** 2 +
             np.cos(lat[i]) * np.cos(lat[box]) * np.sin((lon[box] - lon[i]) / 2) ** 2)
        near = 6371.0 * 2 * np.arcsin(np.sqrt(a)) <= radius
        t_near[i] = ports[box][near & tesla[box]].sum()
        o_near[i] = ports[box][near & ~tesla[box]].sum()
    st = st.assign(tesla_ports_near=t_near, other_ports_near=o_near)
    st["tesla_share_near"] = st["tesla_ports_near"] / (st["tesla_ports_near"] + st["other_ports_near"])
    return st


def network_table(st):
    us = st["dc_ports"].sum()
    g = st.groupby("network")
    t = pd.DataFrame({"stations": g.size(), "ports": g["dc_ports"].sum()})
    t["share_of_us_ports"] = t["ports"] / us
    t["nacs_port_share"] = st[st["has_nacs"].eq(1)].groupby("network")["dc_ports"].sum().reindex(t.index).fillna(0) / t["ports"]
    t["ccs_port_share"] = st[st["has_ccs"]].groupby("network")["dc_ports"].sum().reindex(t.index).fillna(0) / t["ports"]
    tes = st[st["network"].eq("Tesla") & st["tesla_access"].notna()]
    t.loc["Tesla", "tesla_open_port_share"] = tes.loc[tes["tesla_access"].eq("open"), "dc_ports"].sum() / tes["dc_ports"].sum()
    t["median_open_year"] = g["open_year"].median()
    t = t[t["ports"] >= MIN_NETWORK_PORTS].sort_values("ports", ascending=False)
    t.insert(0, "name", [NAMES.get(n, n) for n in t.index])
    return t.reset_index()


def across_networks(st):
    """Station-level: NACS connector on a non-Tesla station against the log size of its network."""
    nt = st[~st["network"].eq("Tesla") & ~st["network"].eq("Non-Networked")].copy()
    size = nt.groupby("network")["dc_ports"].transform("sum")
    nt["log_network_ports"] = np.log(size)
    m = smf.ols("has_nacs ~ log_network_ports + C(open_year)", data=nt).fit(
        cov_type="cluster", cov_kwds={"groups": pd.factorize(nt["network"])[0]})
    nets = network_table(st)
    others = nets[~nets["network"].isin(["Tesla", "Non-Networked"])]
    rho, p_rho = stats.spearmanr(np.log(others["ports"]), others["nacs_port_share"])
    return {"test": "non-Tesla station has NACS connector ~ log network ports + open-year FE",
            "n": int(m.nobs), "clusters": nt["network"].nunique(),
            "coef": m.params["log_network_ports"], "se": m.bse["log_network_ports"],
            "p": m.pvalues["log_network_ports"], "spearman_rho_networks": rho, "spearman_p": p_rho,
            "networks_in_rho": len(others)}


def inside_tesla(st):
    t = st[st["network"].eq("Tesla") & st["open_year"].isin(TESLA_YEARS)].copy()
    print(f"Tesla stations opened {TESLA_YEARS.start}-{TESLA_YEARS.stop - 1}: {len(t):,}")
    miss = t["tesla_access"].isna()
    print(f"  dropped {miss.sum():,} with no access note")
    t = t[~miss].copy()
    t["open"] = t["tesla_access"].eq("open").astype(int)
    t["log_stalls"] = np.log(t["dc_ports"])
    t["log_other_near"] = np.log1p(t["other_ports_near"])
    rows = []
    specs = {"local Tesla share, open-year FE": "open ~ tesla_share_near + log_stalls + C(open_year)",
             "local Tesla share, open-year and state FE": "open ~ tesla_share_near + log_stalls + C(open_year) + C(state)",
             "log(1 + rival ports nearby), open-year and state FE": "open ~ log_other_near + log_stalls + C(open_year) + C(state)"}
    for name, f in specs.items():
        m = smf.ols(f, data=t).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(t["state"])[0]})
        var = f.split("~")[1].split("+")[0].strip()
        lo, hi = m.conf_int().loc[var]
        rows.append({"spec": name, "variable": var, "n": int(m.nobs), "coef": m.params[var], "se": m.bse[var],
                     "p": m.pvalues[var], "lo": lo, "hi": hi, "mean_open": t["open"].mean()})
    t["bin"] = pd.cut(t["tesla_share_near"], [0, 0.5, 0.7, 0.9, 0.999, 1.0],
                      labels=["under 50%", "50-70%", "70-90%", "90-99.9%", "100%"], include_lowest=True)
    bins = t.groupby("bin", observed=True).agg(stations=("open", "size"), open_share=("open", "mean"),
                                               mean_rival_ports=("other_ports_near", "mean")).reset_index()
    by_year = t.groupby("open_year").agg(stations=("open", "size"), open_share=("open", "mean")).reset_index()
    return pd.DataFrame(rows), bins, by_year, t


def plot(nets):
    d = nets[~nets["network"].eq("Non-Networked")].copy()
    d["compat"] = np.where(d["network"].eq("Tesla"), d["tesla_open_port_share"], d["nacs_port_share"])
    fig, ax = plt.subplots(figsize=(7.5, 4.6))
    ax.scatter(d["ports"], 100 * d["compat"], color=np.where(d["network"].eq("Tesla"), "#b2182b", "#2166ac"))
    for r in d.itertuples():
        if r.ports > 700 or r.compat > 0.5:
            ax.annotate(r.name, (r.ports, 100 * r.compat), fontsize=7, xytext=(4, 3), textcoords="offset points")
    ax.set_xscale("log"); ax.set_ylim(-3, 103)
    ax.set_xlabel("public DC fast-charging ports in the network, November 2026 (log scale)")
    ax.set_ylabel("percent of ports open to the other plug")
    ax.set_title("Tesla: ports at Superchargers open to other brands. Others: ports at stations with a Tesla plug.",
                 fontsize=8)
    fig.text(0.5, -0.02, "Source: DOE Alternative Fuels Data Center station file, 1 November 2026.", ha="center", fontsize=7)
    fig.tight_layout()
    fig.savefig(OUT / "who_opens.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def main():
    OUT.mkdir(exist_ok=True)
    st = local_shares(load(), RADIUS_KM)
    nets = network_table(st)
    nets.to_csv(OUT / "networks.csv", index=False)
    pd.DataFrame([("US public DC fast stations, Nov 2026", len(st)),
                  ("US public DC fast ports, Nov 2026", int(st["dc_ports"].sum())),
                  ("Tesla stations opened 2012-2019", int((st["network"].eq("Tesla") & st["open_year"].le(2019)).sum())),
                  ("of which open to other brands", int((st["network"].eq("Tesla") & st["open_year"].le(2019)
                                                         & st["tesla_access"].eq("open")).sum()))],
                 columns=["item", "value"]).to_csv(OUT / "extension_counts.csv", index=False)
    print("\nNetworks with at least", MIN_NETWORK_PORTS, "ports:")
    print(nets.round(3).to_string(index=False))

    tesla_all = st[st["network"].eq("Tesla")]
    acc = (tesla_all.assign(access=tesla_all["tesla_access"].fillna("no note"))
                    .groupby(["open_year", "access"]).size().unstack(fill_value=0))
    acc.to_csv(OUT / "tesla_access_by_open_year.csv")
    print("\nTesla stations by opening year and access note:")
    print(acc.to_string())

    nt = st[~st["network"].eq("Tesla")]
    plug_by_year = (nt[nt["open_year"] >= 2018].groupby("open_year")
                      .agg(stations=("has_nacs", "size"), tesla_plug_share=("has_nacs", "mean")).reset_index())
    plug_by_year.to_csv(OUT / "nacs_by_open_year.csv", index=False)
    print("\nNon-Tesla stations with a Tesla plug, by opening year:")
    print(plug_by_year.round(3).to_string(index=False))

    across = pd.DataFrame([across_networks(st)])
    across.to_csv(OUT / "across_networks_test.csv", index=False)
    print("\nAcross networks:")
    print(across.round(4).to_string(index=False))

    regs, bins, by_year, t = inside_tesla(st)
    regs.to_csv(OUT / "inside_tesla_regressions.csv", index=False)
    bins.to_csv(OUT / "inside_tesla_bins.csv", index=False)
    by_year.to_csv(OUT / "inside_tesla_by_year.csv", index=False)
    print("\nInside Tesla (1 = open to other brands):")
    print(regs.round(4).to_string(index=False))
    print(bins.round(3).to_string(index=False))
    print(by_year.round(3).to_string(index=False))

    wa = t[t["state"].eq("WA")]
    print(f"\nWashington Tesla stations in the inside-Tesla sample: {len(wa)}, open share {wa['open'].mean():.3f}")
    plot(nets)
    print(f"\nWrote results to {OUT.relative_to(ROOT)}/")


if __name__ == "__main__":
    main()
