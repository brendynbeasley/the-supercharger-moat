# Katz and Shapiro (1985) on modern data: findings

## In plain English

Katz and Shapiro predicted that when rival networks are incompatible, the brand with the bigger network sells more,
that making networks compatible erases that edge, and that the firm with the biggest network resists compatibility.
This study tests those predictions on Tesla's Supercharger network, which was closed to other brands until 2024.

- **Teslas did not cluster where Superchargers were.** From 2016 to 2022, Washington ZIP codes where every nearby
  fast charger belonged to another network still bought Teslas 61% of the time, against 69% where nearly every charger was a Tesla Supercharger. Following the same ZIP codes over time,
  the link is zero or slightly negative.
- **Opening the network changed the state, not the neighborhood.** Tesla's share of new battery-electric cars in
  Washington fell from 67.5% in 2018–22 to 45.1% in 2025 through September 2026, while Hyundai, Ford and Rivian,
  whose drivers gained Supercharger access, grew. The local relationship barely moved, so the ZIP-level test cannot
  credit that shift to compatibility.
- **The biggest network opened most of its stations.** Tesla, with half of America's public fast-charging ports,
  lists 72% of its Supercharger ports as open to other brands. Electrify America, the largest rival, has a Tesla plug
  at stations holding 3% of its ports, while at Ionna, Walmart and Mercedes-Benz the stations with one hold 92% to 100% of
  ports. Network size does not
  predict who opened.
- **Tesla keeps its most contested stations closed.** Among Superchargers built since 2020, the ones with many rival
  chargers nearby are the ones still reserved for Teslas, while 96% of stations with no rival within 25 km are open.

A friendlier tour is in the [README](../README.md). The rest of this page is the technical detail.

**Key to the labels below.** *T* = Tesla's share of public DC fast-charging ports within 25 km of a ZIP code's
center on January 1 of the year. *Tesla share* = Tesla's share of new battery-electric cars (BEVs) titled in the ZIP
that year. *Pre* = 2016–2022, *transition* = 2023–2024, *post* = 2025–2026 (2026 is January to September).
*Open* = an AFDC access note of "NACS partner enabled" or "Open to all vehicles." *Tesla plug* = a NACS (SAE J3400)
connector, listed as `TESLA` in the station file.

## Sample (`sample_counts.csv`, `extension_counts.csv`)

| Item | Value |
|---|---|
| New BEVs titled in Washington ZIPs, 2016 to Sept. 2026 | 242,996 |
| ZIP-years with at least one new BEV | 4,312 (552 ZIPs) |
| ZIP-years with no fast port within 25 km (dropped) | 1,227 (10,893 cars) |
| Washington public DC fast stations and ports, Nov. 2026 | 562 stations, 2,505 ports, 1,065 of them Tesla |
| US public DC fast stations and ports, Nov. 2026 | 16,460 stations, 80,930 ports |
| Tesla stations opened 2012–2019, and those open to other brands | 726, of which 13 |

## Washington statewide (`statewide_by_year.csv`)

| Year | New BEVs | Teslas | Tesla share | WA Tesla ports, Jan 1 | WA all ports, Jan 1 | Tesla port share |
|---|---|---|---|---|---|---|
| 2016 | 3,248 | 1,221 | 37.6% | 45 | 62 | 72.6% |
| 2017 | 4,681 | 1,538 | 32.9% | 53 | 83 | 63.9% |
| 2018 | 9,071 | 6,531 | 72.0% | 89 | 121 | 73.6% |
| 2019 | 9,863 | 7,040 | 71.4% | 147 | 193 | 76.2% |
| 2020 | 10,245 | 7,637 | 74.5% | 199 | 338 | 58.9% |
| 2021 | 17,199 | 11,866 | 69.0% | 289 | 467 | 61.9% |
| 2022 | 26,194 | 15,887 | 60.7% | 333 | 581 | 57.3% |
| 2023 | 43,217 | 23,222 | 53.7% | 389 | 691 | 56.3% |
| 2024 | 47,895 | 23,138 | 48.3% | 605 | 1,042 | 58.1% |
| 2025 | 44,455 | 19,013 | 42.8% | 785 | 1,491 | 52.6% |
| 2026 (Jan–Sept) | 26,928 | 13,150 | 48.8% | 933 | 1,883 | 49.5% |

The CSV also covers 2012–2015. Ports count stations still in the federal file; closed stations are missing.

## Tesla share by nearby network (`share_by_network_bin.csv`)

| Period | T | ZIP-years | New BEVs | Tesla share |
|---|---|---|---|---|
| Pre | 0% | 669 | 13,196 | 61.0% |
| Pre | 1–40% | 111 | 5,102 | 67.5% |
| Pre | 40–60% | 401 | 37,125 | 67.0% |
| Pre | 60–80% | 234 | 10,842 | 68.6% |
| Pre | 80–100% | 214 | 6,557 | 68.7% |
| Transition | 0% | 115 | 2,627 | 43.4% |
| Transition | 1–40% | 63 | 5,283 | 48.5% |
| Transition | 40–60% | 371 | 73,939 | 52.3% |
| Transition | 60–80% | 101 | 6,119 | 45.0% |
| Transition | 80–100% | 38 | 1,018 | 39.4% |
| Post | 0% | 160 | 2,263 | 39.1% |
| Post | 1–40% | 111 | 5,396 | 39.1% |
| Post | 40–60% | 406 | 58,970 | 46.1% |
| Post | 60–80% | 65 | 3,055 | 42.5% |
| Post | 80–100% | 26 | 611 | 36.7% |

## Main regressions (`fe_regressions.csv`)

Coefficient on *T* by period (standard error), ZIP and year effects unless stated, weighted by new BEVs unless
stated, standard errors clustered by county.

| Specification | N | Pre | Transition | Post | Post − pre | p |
|---|---|---|---|---|---|---|
| Main, 25 km | 3,085 | −0.039 (0.020) | −0.048 (0.033) | −0.064 (0.029) | −0.025 | 0.32 |
| 10 km | 1,768 | 0.009 (0.011) | −0.008 (0.020) | −0.021 (0.029) | −0.030 | 0.29 |
| 50 km | 3,984 | 0.035 (0.020) | 0.035 (0.072) | −0.078 (0.042) | −0.113 | 0.01 |
| Drop 2026 | 2,701 | −0.041 (0.019) | −0.063 (0.034) | −0.082 (0.029) | −0.041 | 0.09 |
| ZIP-years with 10+ BEVs | 2,127 | −0.041 (0.022) | −0.048 (0.031) | −0.069 (0.032) | −0.028 | 0.32 |
| Unweighted | 3,085 | −0.027 (0.029) | −0.025 (0.066) | −0.070 (0.072) | −0.044 | 0.50 |
| Across ZIPs, year effects only | 3,085 | −0.003 (0.022) | 0.083 (0.047) | 0.127 (0.034) | 0.130 | 0.002 |
| Outcome ln(1 + non-Tesla BEVs), unweighted | 3,085 | 0.168 (0.100) | 0.297 (0.185) | 0.278 (0.208) | 0.110 | 0.59 |

The within-ZIP standard deviation of *T* in the main sample is 0.21, and the weighted mean Tesla share is 0.541.

## Cross-sections by year (`yearly_slopes.csv`)

Tesla share on *T* across ZIPs, county effects, weighted, clustered by county.

| Year | Slope | 95% interval | ZIPs | New BEVs |
|---|---|---|---|---|
| 2016 | −0.238 | −0.289 to −0.187 | 130 | 1,432 |
| 2017 | −0.058 | −0.379 to 0.262 | 159 | 2,231 |
| 2018 | −0.018 | −0.031 to −0.005 | 212 | 7,975 |
| 2019 | 0.031 | −0.012 to 0.074 | 258 | 9,425 |
| 2020 | −0.138 | −0.182 to −0.093 | 275 | 9,833 |
| 2021 | −0.018 | −0.098 to 0.061 | 287 | 16,535 |
| 2022 | 0.019 | −0.119 to 0.157 | 308 | 25,391 |
| 2023 | 0.037 | −0.094 to 0.167 | 327 | 42,139 |
| 2024 | −0.027 | −0.123 to 0.069 | 361 | 46,847 |
| 2025 | 0.022 | −0.084 to 0.127 | 384 | 43,735 |
| 2026 | 0.015 | −0.129 to 0.160 | 384 | 26,560 |

## Example ZIP codes (`example_zips.csv`)

| ZIP | County | Year | Tesla ports | Other ports | T | New BEVs | Teslas | Tesla share |
|---|---|---|---|---|---|---|---|---|
| 98101 (downtown Seattle) | King | 2019 | 8 | 5 | 0.615 | 49 | 43 | 87.8% |
| 98101 | King | 2022 | 64 | 66 | 0.492 | 128 | 103 | 80.5% |
| 98101 | King | 2025 | 168 | 155 | 0.520 | 172 | 92 | 53.5% |
| 98632 (Kelso) | Cowlitz | 2019 | 0 | 2 | 0.000 | 12 | 6 | 50.0% |
| 98632 | Cowlitz | 2022 | 12 | 6 | 0.667 | 39 | 20 | 51.3% |
| 98632 | Cowlitz | 2025 | 12 | 12 | 0.500 | 85 | 32 | 37.6% |
| 98926 (Ellensburg) | Kittitas | 2019 | 5 | 0 | 1.000 | 7 | 7 | 100.0% |
| 98926 | Kittitas | 2022 | 5 | 4 | 0.556 | 43 | 18 | 41.9% |
| 98926 | Kittitas | 2025 | 17 | 12 | 0.586 | 57 | 20 | 35.1% |
| 99201 (Spokane) | Spokane | 2019 | 0 | 2 | 0.000 | 7 | 4 | 57.1% |
| 99201 | Spokane | 2022 | 8 | 12 | 0.400 | 16 | 11 | 68.8% |
| 99201 | Spokane | 2025 | 20 | 46 | 0.303 | 32 | 8 | 25.0% |

## Ellensburg's fast chargers (`ellensburg_stations.csv`)

Every public DC fast station in Ellensburg, Washington, in the November 1, 2026 station file.

| Station | Network | Opened | DC ports | Access note |
|---|---|---|---|---|
| Ellensburg, WA - Tesla Supercharger | Tesla | 2013-12-23 | 5 | Open to Teslas only |
| Taco Bell Ellensburg | Electrify America | 2020-12-18 | 4 | |
| Ellensburg, WA - Canyon Road - Tesla Supercharger | Tesla | 2022-04-28 | 12 | NACS partner enabled |
| Flying J 1195 | EVgo | 2023-11-23 | 8 | |
| Ellensburg, WA | Rivian Adventure Network | 2026-01-30 | 8 | |
| Fred Meyer - Tesla Supercharger | Tesla | 2026-03-20 | 16 | |
| ESD Ellensburg DCFC | ChargePoint | 2026-06-18 | 1 | |
| Rechargery Relay @ Circle K - Canyon Road | Ionna | 2026-09-05 | 6 | |

## Brands (`brands.csv`)

| Make | New BEVs 2018–22 | Share | New BEVs 2025–Sept. 2026 | Share |
|---|---|---|---|---|
| Tesla | 48,961 | 67.5% | 32,163 | 45.1% |
| Hyundai | 1,142 | 1.6% | 4,851 | 6.8% |
| Ford | 2,166 | 3.0% | 4,350 | 6.1% |
| Rivian | 992 | 1.4% | 3,951 | 5.5% |
| Chevrolet | 4,445 | 6.1% | 3,722 | 5.2% |
| Kia | 2,875 | 4.0% | 3,535 | 5.0% |
| Toyota | 3 | 0.0% | 2,173 | 3.0% |
| Cadillac | 0 | 0.0% | 2,066 | 2.9% |
| Subaru | 24 | 0.0% | 1,970 | 2.8% |
| Honda | 0 | 0.0% | 1,833 | 2.6% |
| BMW | 579 | 0.8% | 1,776 | 2.5% |
| Nissan | 5,240 | 7.2% | 1,653 | 2.3% |

## Networks (`networks.csv`)

Public DC fast-charging networks with at least 150 ports, November 1, 2026. *Tesla plug* and *CCS* are shares of
the network's ports at stations offering that connector. *Open* applies to Tesla only and counts ports at stations
with an access note.

| Network | Stations | Ports | Share of US ports | Tesla plug | CCS | Open | Median opening year |
|---|---|---|---|---|---|---|---|
| Tesla | 3,310 | 40,504 | 50.0% | 100.0% | 9.3% | 72.2% | 2023 |
| Electrify America | 1,196 | 6,081 | 7.5% | 3.0% | 99.8% | | 2021 |
| EVgo | 1,213 | 5,414 | 6.7% | 19.4% | 100.0% | | 2024 |
| ChargePoint | 4,602 | 4,996 | 6.2% | 16.7% | 99.5% | | 2024 |
| Red E | 615 | 2,274 | 2.8% | 14.5% | 99.3% | | 2025 |
| Blink | 703 | 2,089 | 2.6% | 6.5% | 99.4% | | 2024 |
| EV Connect | 813 | 1,787 | 2.2% | 5.0% | 99.9% | | 2024 |
| Ionna | 215 | 1,754 | 2.2% | 100.0% | 99.1% | | 2026 |
| Ford Charge | 350 | 1,266 | 1.6% | 0.6% | 100.0% | | 2024 |
| Rivian Adventure Network | 165 | 1,184 | 1.5% | 65.2% | 78.1% | | 2025 |
| Non-networked | 535 | 1,086 | 1.3% | 6.2% | 88.1% | | 2018 |
| Walmart | 110 | 916 | 1.1% | 100.0% | 100.0% | | 2026 |
| EVCS | 223 | 905 | 1.1% | 24.8% | 100.0% | | 2023 |
| bp pulse | 96 | 882 | 1.1% | 66.4% | 100.0% | | 2025 |
| FCN | 172 | 798 | 1.0% | 8.0% | 100.0% | | 2023 |
| Mercedes-Benz | 82 | 752 | 0.9% | 92.2% | 100.0% | | 2026 |

The CSV lists 19 smaller networks as well.

## Compatibility tests (`across_networks_test.csv`, `inside_tesla_regressions.csv`)

| Test | N | Coefficient | SE | p |
|---|---|---|---|---|
| Non-Tesla station has a Tesla plug, on ln(network ports), opening-year effects, clustered by network | 12,615 | −0.006 | 0.013 | 0.66 |
| Spearman correlation of ln(ports) and Tesla-plug share, non-Tesla networks with 150+ ports | 33 | 0.152 | | 0.40 |
| Tesla station open, on local Tesla share, ln(stalls), opening-year effects | 2,228 | 0.039 | 0.026 | 0.14 |
| Same, adding state effects | 2,228 | 0.046 | 0.031 | 0.14 |
| Tesla station open, on ln(1 + rival ports within 25 km), ln(stalls), opening-year and state effects | 2,228 | −0.023 | 0.005 | < 0.001 |

Inside-Tesla tests cover Superchargers opened 2020–2025, with errors clustered by state; 90.5% of them are open.

## Tesla stations by local share and by year (`inside_tesla_bins.csv`, `inside_tesla_by_year.csv`)

| Tesla share of fast ports within 25 km | Stations | Open | Mean rival ports nearby |
|---|---|---|---|
| Under 50% | 763 | 90.8% | 141.3 |
| 50–70% | 1,012 | 88.7% | 197.4 |
| 70–90% | 334 | 93.4% | 32.8 |
| 90–99.9% | 27 | 96.3% | 4.8 |
| 100% | 92 | 95.7% | 0.0 |

| Opening year | Stations | Open |
|---|---|---|
| 2020 | 213 | 70.9% |
| 2021 | 291 | 83.5% |
| 2022 | 374 | 90.1% |
| 2023 | 496 | 91.7% |
| 2024 | 406 | 95.3% |
| 2025 | 448 | 99.1% |

## Rival stations with a Tesla plug, by opening year (`nacs_by_open_year.csv`)

| Opening year | Non-Tesla stations | With a Tesla plug |
|---|---|---|
| 2018 | 206 | 1.0% |
| 2019 | 356 | 1.4% |
| 2020 | 615 | 3.6% |
| 2021 | 989 | 8.4% |
| 2022 | 1,002 | 8.5% |
| 2023 | 1,936 | 9.6% |
| 2024 | 2,624 | 8.8% |
| 2025 | 2,874 | 18.0% |
| 2026 | 2,156 | 38.5% |

`tesla_access_by_open_year.csv` gives every Tesla station by opening year and access note, including the 325
stations opened in 2026 that have no note yet. `zip_year_panel.csv` is the full ZIP-year panel behind the
regressions.
