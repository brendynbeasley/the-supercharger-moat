"""Katz and Shapiro (1985) on Washington State electric cars: does a brand sell more where its
own charging network is bigger, and does that edge disappear once networks become compatible?

Katz and Shapiro's model says that when rival networks are incompatible, a seller whose buyers
can reach a bigger network sells more (and charges more) by the value of the extra network, and
that once networks are compatible the network-size edge disappears and industry output rises.
Tesla's Supercharger network was usable only by Teslas until Tesla published its connector in
November 2022 and began opening stations to other brands in 2024. This script measures, for every
Washington ZIP code and year, the Tesla share of new battery-electric cars titled there and the
Tesla share of the public DC fast-charging ports within 25 km on 1 January of that year, then asks
whether the link between the two weakened once compatibility arrived.

Inputs (fetched into data/raw/ if missing):
    AFDC station file   developer.nlr.gov/api/alt-fuel-stations/v1.csv (DEMO_KEY; 31 MB, not committed;
                        reduced to data/processed/afdc_dcfast_stations.csv, which is committed)
    WA EV titles        data.wa.gov/resource/rpr4-cgyd.json, aggregated on the server to ZIP x year x make
    ZIP points          www2.census.gov 2020 Gazetteer ZCTA file

Run from the repository root:
    python src/supercharger_moat.py
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests
import statsmodels.formula.api as smf

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
PROC = ROOT / "data" / "processed"
OUT = ROOT / "results"

AFDC_URL = ("https://developer.nlr.gov/api/alt-fuel-stations/v1.csv"
            "?api_key=DEMO_KEY&fuel_type=ELEC&status=all&access=all&limit=all")
WA_URL = "https://data.wa.gov/resource/rpr4-cgyd.json"   # Electric Vehicle Title and Registration Activity
WA_WHERE = "new_or_used_vehicle='New' AND transaction_type='Original Title'"   # a first title on a new car = a sale
AFDC_RAW = RAW / "afdc_elec_all_2026-11-01.csv"
WA_RAW = RAW / "wa_new_ev_titles_zip_year_make_2026-11-01.csv"
GAZ_RAW = RAW / "2020_Gaz_zcta_national.zip"
AFDC_PROC = PROC / "afdc_dcfast_stations.csv"

RADIUS_KM = 25            # a local charging market: roughly a 15-mile drive (judgment; 10 and 50 km as checks)
ALT_RADII = [10, 50]
FIRST_YEAR, LAST_YEAR = 2016, 2026   # Tesla's network became a statewide system around 2016; 2026 runs through September
# Compatibility timeline (Tesla blog, 11 Nov 2022: connector published; Ford access 29 Feb 2024, others through 2024-25)
PERIODS = {"pre": range(FIRST_YEAR, 2023), "transition": range(2023, 2025), "post": range(2025, LAST_YEAR + 1)}
MIN_BEV = 1               # a ZIP-year needs at least one new battery-electric car to have a share


def download(url, path):
    print(f"  downloading {url[:70]}... -> {path.name}")
    tmp = path.with_suffix(".part")
    with requests.get(url, stream=True, timeout=600) as r:
        r.raise_for_status()
        with open(tmp, "wb") as f:
            for chunk in r.iter_content(1 << 20):
                f.write(chunk)
    tmp.rename(path)


def build_afdc():
    """Reduce the national AFDC electric station file to public, open DC fast-charging stations."""
    if AFDC_PROC.exists():
        st = pd.read_csv(AFDC_PROC, parse_dates=["open_date"])
        print(f"AFDC: loaded {len(st):,} DC fast stations from {AFDC_PROC.relative_to(ROOT)}")
        return st
    if not AFDC_RAW.exists():
        download(AFDC_URL, AFDC_RAW)
    d = pd.read_csv(AFDC_RAW, low_memory=False)
    print(f"AFDC: loaded {len(d):,} electric stations from {AFDC_RAW.name}")
    keep = d["EV DC Fast Count"].fillna(0) > 0
    print(f"  dropped {(~keep).sum():,} stations with no DC fast ports")
    d = d[keep]
    pub = d["Access Code"].eq("public") & d["Status Code"].isin(["E", "T"])
    print(f"  dropped {(~pub).sum():,} private or planned DC fast stations")
    d = d[pub]
    st = pd.DataFrame({
        "station_id": d["ID"], "name": d["Station Name"], "network": d["EV Network"],
        "city": d["City"], "state": d["State"], "zip": d["ZIP"],
        "lat": d["Latitude"], "lon": d["Longitude"], "open_date": pd.to_datetime(d["Open Date"]),
        "dc_ports": d["EV DC Fast Count"].astype(int), "connectors": d["EV Connector Types"],
        "access_days_time": d["Access Days Time"], "facility_type": d["Facility Type"],
    })
    PROC.mkdir(parents=True, exist_ok=True)
    st.to_csv(AFDC_PROC, index=False)
    print(f"  wrote {len(st):,} stations to {AFDC_PROC.relative_to(ROOT)}")
    return st


def fetch_titles():
    """New battery-electric and plug-in hybrid cars titled in Washington, by ZIP, year and make.

    The aggregation runs on the state's open-data server (Socrata SoQL), so the download is small.
    """
    if WA_RAW.exists():
        c = pd.read_csv(WA_RAW, dtype={"zip": str})
        print(f"WA titles: loaded {len(c):,} ZIP-year-make cells from {WA_RAW.relative_to(ROOT)}")
        return c
    params = {"$select": "zip, county, transaction_year, make, electric_vehicle_type, count(*) AS vehicles",
              "$where": WA_WHERE, "$group": "zip, county, transaction_year, make, electric_vehicle_type",
              "$order": "zip, transaction_year, make, county, electric_vehicle_type", "$limit": 50000}
    parts, offset = [], 0
    while True:
        r = requests.get(WA_URL, params=params | {"$offset": offset}, timeout=300)
        r.raise_for_status()
        rows = r.json()
        if not rows:
            break
        parts.append(pd.DataFrame(rows))
        offset += len(rows)
        print(f"  fetched {offset:,} cells")
    c = pd.concat(parts, ignore_index=True)
    c.to_csv(WA_RAW, index=False)
    print(f"WA titles: wrote {len(c):,} cells to {WA_RAW.relative_to(ROOT)}")
    return pd.read_csv(WA_RAW, dtype={"zip": str})


def zip_points():
    """Census 2020 ZCTA internal points for Washington ZIP codes (98xxx and 99xxx)."""
    g = pd.read_csv(GAZ_RAW, sep="\t", dtype={"GEOID": str})
    g.columns = [c.strip() for c in g.columns]
    g = g[g["GEOID"].str[:2].isin(["98", "99"])]
    return g.rename(columns={"GEOID": "zip", "INTPTLAT": "lat", "INTPTLONG": "lon"})[["zip", "lat", "lon"]]


def clean_titles(c):
    c = c.rename(columns={"transaction_year": "year"})
    c["type"] = np.where(c["electric_vehicle_type"].str.startswith("Battery"), "BEV", "PHEV")
    bad = c["zip"].isna() | ~c["zip"].astype(str).str[:2].isin(["98", "99"])
    print(f"  dropped {int(c.loc[bad, 'vehicles'].sum()):,} new cars with a missing or non-Washington ZIP")
    c = c[~bad].copy()
    county = (c.groupby(["zip", "county"])["vehicles"].sum().reset_index()
                .sort_values("vehicles").drop_duplicates("zip", keep="last")[["zip", "county"]])
    c = c.drop(columns="county").groupby(["zip", "year", "make", "type"], as_index=False)["vehicles"].sum()
    pts = zip_points()
    c = c.merge(county, on="zip").merge(pts, on="zip", how="left")
    nopt = c["lat"].isna()
    print(f"  dropped {int(c.loc[nopt, 'vehicles'].sum()):,} new cars in ZIPs with no Census ZCTA point")
    return c[~nopt]


def haversine_km(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(np.radians, (lat1, lon1, lat2, lon2))
    a = np.sin((lat2 - lat1) / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2
    return 6371.0 * 2 * np.arcsin(np.sqrt(a))


def local_ports(zips, st, years, radius):
    """Tesla and other DC fast ports within `radius` km of each ZIP point on 1 January of each year."""
    near = st[st["lat"].between(44.5, 50.0) & st["lon"].between(-125.5, -115.5)]
    rows = []
    for z in zips.itertuples():
        dist = haversine_km(z.lat, z.lon, near["lat"].values, near["lon"].values)
        s = near[dist <= radius]
        for y in years:
            open_s = s[s["open_date"] < pd.Timestamp(f"{y}-01-01")]
            tesla = open_s.loc[open_s["network"].eq("Tesla"), "dc_ports"].sum()
            rows.append((z.zip, y, tesla, open_s["dc_ports"].sum() - tesla))
    out = pd.DataFrame(rows, columns=["zip", "year", "tesla_ports", "other_ports"])
    out["all_ports"] = out["tesla_ports"] + out["other_ports"]
    out["tesla_port_share"] = out["tesla_ports"] / out["all_ports"].replace(0, np.nan)
    return out


def period_of(y):
    return next(k for k, r in PERIODS.items() if y in r)


def build_panel(cars, st, radius):
    bev = cars[cars["type"].eq("BEV") & cars["year"].between(FIRST_YEAR, LAST_YEAR)]
    zy = (bev.assign(tesla=np.where(bev["make"].eq("TESLA"), bev["vehicles"], 0))
             .groupby(["zip", "year"]).agg(bev=("vehicles", "sum"), tesla=("tesla", "sum")).reset_index())
    zy["other"] = zy["bev"] - zy["tesla"]
    zips = cars.drop_duplicates("zip")[["zip", "county", "lat", "lon"]]
    ports = local_ports(zips, st, range(FIRST_YEAR, LAST_YEAR + 1), radius)
    p = zy.merge(ports, on=["zip", "year"], how="left").merge(zips[["zip", "county"]], on="zip")
    p["tesla_share"] = p["tesla"] / p["bev"]
    p["period"] = p["year"].map(period_of)
    return p


def fe_regression(p, outcome="tesla_share", weight="bev", fe="C(zip) + C(year)"):
    """Tesla port share interacted with period; ZIP and year fixed effects by default; clustered by county."""
    d = p.dropna(subset=["tesla_port_share"]).copy()
    for k in PERIODS:
        d[f"T_{k}"] = d["tesla_port_share"] * d["period"].eq(k)
    f = f"{outcome} ~ T_pre + T_transition + T_post + {fe}"
    m = smf.wls(f, data=d, weights=d[weight]).fit(cov_type="cluster",
                                                 cov_kwds={"groups": pd.factorize(d["county"])[0]})
    diff = m.t_test("T_post - T_pre = 0")
    within = d["tesla_port_share"] - d.groupby("zip")["tesla_port_share"].transform("mean")
    row = {"outcome": outcome, "n": int(m.nobs), "zips": d["zip"].nunique(), "counties": d["county"].nunique(),
           "sd_within_zip_T": within.std(), "mean_outcome": np.average(d[outcome], weights=d[weight])}
    for k in PERIODS:
        lo, hi = m.conf_int().loc[f"T_{k}"]
        row.update({f"b_{k}": m.params[f"T_{k}"], f"se_{k}": m.bse[f"T_{k}"], f"p_{k}": m.pvalues[f"T_{k}"],
                    f"lo_{k}": lo, f"hi_{k}": hi})
    row.update({"b_post_minus_pre": float(np.squeeze(diff.effect)), "se_post_minus_pre": float(np.squeeze(diff.sd)),
                "p_post_minus_pre": float(np.squeeze(diff.pvalue))})
    return row


def yearly_slopes(p):
    """Cross-section of ZIPs, one year at a time: Tesla share on Tesla port share, county FE."""
    rows = []
    for y, d in p.dropna(subset=["tesla_port_share"]).groupby("year"):
        m = smf.wls("tesla_share ~ tesla_port_share + C(county)", data=d, weights=d["bev"]).fit(
            cov_type="cluster", cov_kwds={"groups": pd.factorize(d["county"])[0]})
        lo, hi = m.conf_int().loc["tesla_port_share"]
        rows.append({"year": y, "slope": m.params["tesla_port_share"], "se": m.bse["tesla_port_share"],
                     "lo": lo, "hi": hi, "zips": len(d), "bev": int(d["bev"].sum())})
    return pd.DataFrame(rows)


def share_by_bin(p):
    """Tesla share of new BEVs grouped by the Tesla share of nearby fast-charging ports."""
    d = p.dropna(subset=["tesla_port_share"]).copy()
    d["bin"] = pd.cut(d["tesla_port_share"], [-0.01, 0.0, 0.4, 0.6, 0.8, 1.0],
                      labels=["0%", "1-40%", "40-60%", "60-80%", "80-100%"])
    g = d.groupby(["period", "bin"], observed=True).agg(zip_years=("zip", "size"), bev=("bev", "sum"),
                                                       tesla=("tesla", "sum")).reset_index()
    g["tesla_share"] = g["tesla"] / g["bev"]
    order = {k: i for i, k in enumerate(PERIODS)}
    return g.sort_values(["period", "bin"], key=lambda c: c.map(order) if c.name == "period" else c)


def statewide(cars, st):
    bev = cars[cars["type"].eq("BEV") & cars["year"].between(2012, LAST_YEAR)]
    s = bev.groupby("year").agg(bev=("vehicles", "sum")).join(
        bev[bev["make"].eq("TESLA")].groupby("year")["vehicles"].sum().rename("tesla"))
    s["tesla_share"] = s["tesla"] / s["bev"]
    wa = st[st["state"].eq("WA")]
    for y in s.index:
        o = wa[wa["open_date"] < pd.Timestamp(f"{y}-01-01")]
        s.loc[y, "wa_tesla_ports"] = o.loc[o["network"].eq("Tesla"), "dc_ports"].sum()
        s.loc[y, "wa_all_ports"] = o["dc_ports"].sum()
    s["wa_tesla_port_share"] = s["wa_tesla_ports"] / s["wa_all_ports"]
    return s.reset_index()


def brands(cars):
    """The best-selling battery-electric brands in Washington, before and after compatibility."""
    bev = cars[cars["type"].eq("BEV")]
    pre = bev[bev["year"].between(2018, 2022)].groupby("make")["vehicles"].sum()
    post = bev[bev["year"].between(2025, 2026)].groupby("make")["vehicles"].sum()
    t = pd.DataFrame({"bev_2018_22": pre, "bev_2025_26": post}).fillna(0).astype(int)
    t["share_2018_22"] = t["bev_2018_22"] / t["bev_2018_22"].sum()
    t["share_2025_26"] = t["bev_2025_26"] / t["bev_2025_26"].sum()
    return t.sort_values("bev_2025_26", ascending=False).head(12).reset_index(names="make")


def example_zips(p, zips=("98926", "99201", "98101", "98632")):
    """Worked examples: a few ZIPs whose local network changed a lot."""
    e = p[p["zip"].isin(zips) & p["year"].isin([2019, 2022, 2025])]
    return e[["zip", "county", "year", "tesla_ports", "other_ports", "tesla_port_share",
              "bev", "tesla", "tesla_share"]].sort_values(["zip", "year"])


def town_stations(st, city="Ellensburg", state="WA"):
    """Every public DC fast station in one town, for the README's opening example."""
    t = st[st["city"].eq(city) & st["state"].eq(state)]
    return t[["name", "network", "zip", "open_date", "dc_ports", "connectors",
              "access_days_time"]].sort_values("open_date")


def plot(state, slopes):
    fig, ax = plt.subplots(1, 2, figsize=(11, 4.2))
    s = state[state["year"] >= 2014]
    ax[0].plot(s["year"], 100 * s["tesla_share"], marker="o", color="#b2182b", label="Tesla share of new BEVs")
    ax[0].plot(s["year"], 100 * s["wa_tesla_port_share"], marker="s", color="#2166ac",
               label="Tesla share of WA fast-charging ports (Jan 1)")
    ax[0].axvspan(2024.5, 2026.5, color="0.9", zorder=0)
    ax[0].set_ylim(0, 100); ax[0].set_ylabel("percent"); ax[0].set_xlabel("year of sale")
    ax[0].set_title("Washington State", fontsize=10); ax[0].legend(fontsize=8, loc="lower left")
    ax[1].errorbar(slopes["year"], slopes["slope"], yerr=[slopes["slope"] - slopes["lo"],
                   slopes["hi"] - slopes["slope"]], fmt="o", color="#333333", capsize=3)
    ax[1].axhline(0, color="0.5", lw=0.8); ax[1].axvspan(2024.5, 2026.5, color="0.9", zorder=0)
    ax[1].set_xlabel("year of sale"); ax[1].set_ylabel("slope, with 95% interval")
    ax[1].set_title("Tesla sales share on local Tesla port share, across ZIP codes", fontsize=10)
    fig.text(0.5, -0.02, "Shaded: 2025-26 sales, after Superchargers opened to other brands (2026 is January-September). "
             "Sources: WA Dept. of Licensing; DOE Alternative Fuels Data Center.", ha="center", fontsize=8)
    fig.tight_layout()
    fig.savefig(OUT / "tesla_share_and_network.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def main():
    OUT.mkdir(exist_ok=True)
    st = build_afdc()
    cars = clean_titles(fetch_titles())
    print(f"Window: sales years {FIRST_YEAR}-{LAST_YEAR}; radius {RADIUS_KM} km")

    p = build_panel(cars, st, RADIUS_KM)
    print(f"Panel: {len(p):,} ZIP-years with at least {MIN_BEV} new BEV, {p['zip'].nunique()} ZIPs")
    miss = p["tesla_port_share"].isna()
    print(f"  dropped from regressions {miss.sum():,} ZIP-years ({int(p.loc[miss, 'bev'].sum()):,} cars) "
          f"with no fast-charging port within {RADIUS_KM} km")
    p.to_csv(OUT / "zip_year_panel.csv", index=False)
    pd.DataFrame([
        ("new BEVs titled in panel ZIPs, all years", int(p["bev"].sum())),
        ("ZIP-years with at least one new BEV", len(p)),
        ("ZIPs", p["zip"].nunique()),
        ("ZIP-years with no fast port within radius (dropped)", int(miss.sum())),
        ("new BEVs in dropped ZIP-years", int(p.loc[miss, "bev"].sum())),
        ("WA public DC fast stations, Nov 2026", int(st["state"].eq("WA").sum())),
        ("WA public DC fast ports, Nov 2026", int(st.loc[st["state"].eq("WA"), "dc_ports"].sum())),
        ("WA Tesla DC fast ports, Nov 2026", int(st.loc[st["state"].eq("WA") & st["network"].eq("Tesla"), "dc_ports"].sum())),
    ], columns=["item", "value"]).to_csv(OUT / "sample_counts.csv", index=False)

    main_rows = [fe_regression(p) | {"spec": f"main, {RADIUS_KM} km"}]
    for r in ALT_RADII:
        main_rows.append(fe_regression(build_panel(cars, st, r)) | {"spec": f"radius {r} km"})
    main_rows.append(fe_regression(p[p["year"] <= 2025]) | {"spec": "drop 2026 (January to September only)"})
    main_rows.append(fe_regression(p[p["bev"] >= 10]) | {"spec": "ZIP-years with 10+ BEVs"})
    main_rows.append(fe_regression(p.assign(ones=1.0), weight="ones") | {"spec": "unweighted"})
    main_rows.append(fe_regression(p, fe="C(year)") | {"spec": "across ZIPs: year effects only, no ZIP effects"})
    # Katz and Shapiro's output prediction: other brands should gain most where Tesla held the network
    q = p.assign(log_other=np.log1p(p["other"]), ones=1.0)
    main_rows.append(fe_regression(q, outcome="log_other", weight="ones")
                     | {"spec": "outcome: log(1 + non-Tesla BEVs)"})
    reg = pd.DataFrame(main_rows)
    reg = reg[["spec"] + [c for c in reg.columns if c != "spec"]]
    reg.to_csv(OUT / "fe_regressions.csv", index=False)
    print("\nFixed-effects regressions (coefficient on Tesla port share by period):")
    print(reg[["spec", "n", "b_pre", "se_pre", "b_transition", "b_post", "se_post",
               "b_post_minus_pre", "p_post_minus_pre"]].round(3).to_string(index=False))

    slopes = yearly_slopes(p)
    slopes.to_csv(OUT / "yearly_slopes.csv", index=False)
    print("\nCross-sectional slopes by year of sale:")
    print(slopes.round(3).to_string(index=False))

    bins = share_by_bin(p)
    bins.to_csv(OUT / "share_by_network_bin.csv", index=False)
    print("\nTesla share of new BEVs by nearby Tesla port share:")
    print(bins.round(3).to_string(index=False))

    state = statewide(cars, st)
    state.to_csv(OUT / "statewide_by_year.csv", index=False)
    print("\nStatewide:")
    print(state.round(3).to_string(index=False))

    b = brands(cars)
    b.to_csv(OUT / "brands.csv", index=False)
    print("\nBrands:")
    print(b.round(3).to_string(index=False))

    ex = example_zips(p)
    ex.to_csv(OUT / "example_zips.csv", index=False)
    print("\nExample ZIPs:")
    print(ex.round(3).to_string(index=False))

    town = town_stations(st)
    town.to_csv(OUT / "ellensburg_stations.csv", index=False)
    print(f"\nEllensburg, WA: {len(town)} public DC fast stations in the station file")

    plot(state, slopes)
    print(f"\nWrote results to {OUT.relative_to(ROOT)}/")


if __name__ == "__main__":
    main()
