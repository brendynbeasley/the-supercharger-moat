# Technical notes

This is the technical companion to the [README](README.md). It covers the data, the method, the full set of test
statistics and how to reproduce everything. Every table is in [results/FINDINGS.md](results/FINDINGS.md).

## The original study

Michael L. Katz and Carl Shapiro, "Network Externalities, Competition, and Compatibility," *American Economic
Review* 75(3), June 1985, pp. 424–440. It is a theory paper. Buyers value a brand at their own taste plus a term
that rises with the network they expect the brand to have, sellers compete in quantities, and expectations are
fulfilled in equilibrium. Its headline results, as summarized by Economides (1996, p. 684) and Nagler (2008), are
that industry output is greater under compatibility than in any equilibrium with some incompatible firms, that
firms with large networks or good reputations are biased against compatibility while firms with small networks or
weak reputations favor it, and that private and social incentives for compatibility can diverge in either
direction. There is no data table to replicate, so I test the two sharpest predictions on present-day data.

## Headline results

| Test | Estimate | Standard error | 95% interval | N |
|---|---|---|---|---|
| Tesla sales share on local Tesla port share, before compatibility (2016–22), ZIP and year effects | −0.039 | 0.020 | −0.078 to −0.000 | 3,085 ZIP-years |
| Same, after compatibility (2025–26) | −0.064 | 0.029 | −0.120 to −0.008 | 3,085 |
| After minus before | −0.025 | 0.025 | p = 0.32 | 3,085 |
| Non-Tesla station has a Tesla plug, per log point of network size, open-year effects | −0.006 | 0.013 | p = 0.66 | 12,615 stations |
| Tesla station open to other brands, per log point of rival ports within 25 km | −0.023 | 0.005 | −0.033 to −0.012 | 2,228 stations |

The model predicts a positive first row, a negative third row and a negative fourth row. Read simply, it also
predicts that Tesla keeps closed the stations where its local share is highest, a negative coefficient on that
share and a positive one on rival ports in the last test. The data give a zero or slightly negative first row,
an insignificant third row, no size gradient in the fourth, and a Tesla that keeps its most contested stations
closed.

## Data

- **Sales.** Washington State Department of Licensing, Electric Vehicle Title and Registration Activity
  (data.wa.gov dataset `rpr4-cgyd`), transactions through September 30, 2026. The script aggregates on the server to
  ZIP × transaction year × make × vehicle type, keeping `new_or_used_vehicle = 'New'` and
  `transaction_type = 'Original Title'`. Saved as `data/raw/wa_new_ev_titles_zip_year_make_2026-11-01.csv`
  (51,382 cells).
- **Chargers.** US Department of Energy, Alternative Fuels Data Center station file, all electric stations, all
  statuses, from `developer.nlr.gov/api/alt-fuel-stations/v1.csv` with the public `DEMO_KEY`, downloaded November 1,
  2026 (91,095 stations, 31 MB, not committed). Reduced to public, open or temporarily unavailable stations with at
  least one DC fast port, `data/processed/afdc_dcfast_stations.csv` (16,460 stations, 80,930 ports).
- **ZIP locations.** US Census Bureau 2020 Gazetteer ZCTA file, `data/raw/2020_Gaz_zcta_national.zip`.

## Method

Rules fixed before looking at results:

- The local market is a 25 km radius around a ZIP's Census internal point; 10 km and 50 km are checks.
- A station counts toward year $`t`$ if its AFDC opening date is before January 1 of year $`t`$.
- Periods are before compatibility (2016–2022), transition (2023–2024) and after compatibility (2025–2026).
  Tesla published its connector on November 11, 2022, and Ford drivers gained Supercharger access on February 29,
  2024, with other brands following through early 2025.
- ZIP-years with no fast port within the radius are dropped (1,227 ZIP-years, 10,893 cars). Cars with a missing
  or non-Washington ZIP (319) or a ZIP with no Census point (35) are dropped.
- Regressions are weighted by new battery-electric cars, with standard errors clustered by county (37 clusters).

The main specification is

```math
\begin{aligned}
s_{z,t} &= \alpha_z + \gamma_t + \sum_{k \in \{\text{pre},\,\text{tr},\,\text{post}\}} \beta_k\, T_{z,t}\, \mathbf{1}[t \in k] + \varepsilon_{z,t} \\
T_{z,t} &= \frac{\text{Tesla ports within 25 km on Jan 1 of } t}{\text{all public DC fast ports within 25 km on Jan 1 of } t}
\end{aligned}
```

where $`s_{z,t}`$ is Tesla's share of new battery-electric cars titled in ZIP $`z`$ in year $`t`$. It follows from
the model's first-order condition, under which brand $`i`$'s output exceeds brand $`j`$'s by
$`v(N_i) - v(N_j)`$ when networks are incompatible and by zero when they are compatible. The output prediction uses
$`\ln(1 + \text{non-Tesla BEVs}_{z,t})`$ on the left-hand side, unweighted.

The extension has two parts. Across networks, a linear probability model of whether a non-Tesla station has a
Tesla (NACS) connector on the log of its network's national port count, with opening-year effects and errors
clustered by network (75 networks). Inside Tesla, for Superchargers opened 2020–2025 (newer hardware that can serve
other brands), a linear probability model

```math
\text{open}_s = \theta\, x_s + \lambda \ln(\text{stalls}_s) + \mu_{\text{year}(s)} + \eta_{\text{state}(s)} + u_s
```

with $`x_s`$ either the Tesla share of fast ports within 25 km or $`\ln(1 + R_s)`$, the log of rival ports
within 25 km plus one, and errors clustered by state. A station is open if its AFDC access note reads "NACS partner
enabled" or "Open to all vehicles" and closed if it reads "Open to Teslas only." Most Superchargers opened in 2026 (325 of
356) have no access note yet, so the national figure of 72% of Supercharger ports open to other brands counts only
ports at stations with a note.

## Full test statistics

Main panel, coefficient on $`T`$ by period (standard errors in parentheses):

| Specification | N | Before | Transition | After | After − before | p |
|---|---|---|---|---|---|---|
| Main, 25 km | 3,085 | −0.039 (0.020) | −0.048 (0.033) | −0.064 (0.029) | −0.025 | 0.32 |
| 10 km | 1,768 | 0.009 (0.011) | −0.008 (0.020) | −0.021 (0.029) | −0.030 | 0.29 |
| 50 km | 3,984 | 0.035 (0.020) | 0.035 (0.072) | −0.078 (0.042) | −0.113 | 0.01 |
| Drop 2026 | 2,701 | −0.041 (0.019) | −0.063 (0.034) | −0.082 (0.029) | −0.041 | 0.09 |
| ZIP-years with 10+ cars | 2,127 | −0.041 (0.022) | −0.048 (0.031) | −0.069 (0.032) | −0.028 | 0.32 |
| Unweighted | 3,085 | −0.027 (0.029) | −0.025 (0.066) | −0.070 (0.072) | −0.044 | 0.50 |
| Across ZIPs, year effects only | 3,085 | −0.003 (0.022) | 0.083 (0.047) | 0.127 (0.034) | 0.130 | 0.002 |
| ln(1 + non-Tesla cars) | 3,085 | 0.168 (0.100) | 0.297 (0.185) | 0.278 (0.208) | 0.110 | 0.59 |

Only the 50 km version gives an after-minus-before difference with the predicted sign at conventional
significance, and its before coefficient is itself insignificant. The across-ZIP version moves the other way.
Year-by-year cross-sections with county effects are in `results/yearly_slopes.csv`; none from 2018 on is
significantly positive.

Inside Tesla (N = 2,228, mean open share 0.905): local Tesla share 0.039 (0.026) with opening-year effects and
0.046 (0.031) adding state effects; $`\ln(1 + R_s)`$ −0.023 (0.005), p < 0.001. Across non-Tesla networks with at
least 150 ports, the Spearman correlation of log size with Tesla-plug share is 0.15 (p = 0.40, 33 networks).

## Reproducing the results

1. Install the packages (Python 3.12 or later):

   ```bash
   pip install -r requirements.txt
   ```

2. Run the two scripts from the repository root. The first fetches the 31 MB station file into `data/raw/` if
   it is missing (the processed station file and the sales file are committed, so it runs offline as shipped):

   ```bash
   python src/supercharger_moat.py
   python src/who_opens.py
   ```

3. Outputs land in `results/`. Deleting `data/processed/afdc_dcfast_stations.csv` or the sales file forces a fresh
   download.

## Repository layout

| Path | What it is |
|---|---|
| [src/supercharger_moat.py](src/supercharger_moat.py) | Data download and reduction, ZIP panel, main regressions, statewide series, figure 1 |
| [src/who_opens.py](src/who_opens.py) | Network table, compatibility tests across networks and inside Tesla, figure 2 |
| [results/FINDINGS.md](results/FINDINGS.md) | Plain-English summary and every table |
| `data/raw/`, `data/processed/` | Sales cells, ZIP points, reduced station file |

## References

- Economides, N. (1996). The economics of networks. *International Journal of Industrial Organization* 14(6),
  673–699.
- Farrell, J. & Saloner, G. (1985). Standardization, compatibility, and innovation. *RAND Journal of Economics*
  16(1), 70–83.
- Katz, M. L. & Shapiro, C. (1985). Network externalities, competition, and compatibility. *American Economic
  Review* 75(3), 424–440.
- Katz, M. L. & Shapiro, C. (1994). Systems competition and network effects. *Journal of Economic Perspectives*
  8(2), 93–115.
- Liebowitz, S. J. & Margolis, S. E. (1994). Network externality: an uncommon tragedy. *Journal of Economic
  Perspectives* 8(2), 133–150.
- Nagler, M. G. (2008). Network externalities, mutuality, and compatibility. NET Institute Working Paper 08-37,
  New York University.
