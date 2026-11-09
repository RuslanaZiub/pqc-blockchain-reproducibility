# Reproducibility package v1.0-rc1

Associated manuscript: **Network propagation and node-level performance of post-quantum signatures in blockchain systems**.

## Status

This is a **release-candidate Zenodo package** containing the final corrected SimBlock/network datasets and the exact Solochain/Locust v3b code, datasets, and binary artifacts supplied for the reported controlled experiment.

The remaining pre-publication actions are listed in `PENDING_ITEMS.md` (primarily DOI/license finalization, the unavailable repetition-level Rust microbenchmark CSV files, and synchronization of two manuscript details).

## Directory structure

```text
PQC_blockchain_Zenodo_v1.0-rc1/
  README.md
  DATA_DICTIONARY.md
  PENDING_ITEMS.md
  KNOWN_MANUSCRIPT_CORRECTIONS.md
  MANIFEST_SHA256.csv
  PACKAGE_SUMMARY.json
  data/
    microbenchmarks/
    simblock_primary/
    simblock_stable_pilot/
    simblock_stable_full/
    simblock_cbr/
    loadtest_duration/
    solochain_v3b/
    solochain_repeat_v3/
  code/
    simblock/
    solochain/v3b/
    solochain/binaries/
    analysis/
  derived/
    figure_data/
    tables/
  docs/
    solochain/
```

## Network/SimBlock component

### Base simulator
- SimBlock upstream: https://github.com/dsg-titech/simblock
- Base: v0.8.1 + 15 commits
- Commit: `8a1285aa37b832385b0be2ae6f804885a4a7031f`
- Upstream license: Apache License 2.0
- Gradle Wrapper: 6.7.1
- JDK: 17
- Main simulation environment: Ubuntu 22.04.5 LTS VM, 2 CPU cores, 3.8 GB RAM; host Intel Core i5-6200U, 8 GB RAM.

### Primary FULL/ZERO experiment
`data/simblock_primary/run_coverage6s.csv`: 1200 run-level rows (600 FULL + 600 paired ZERO).
Grid: 3 schemes × 4 transaction loads × 5 node counts × 10 seeds × 2 modes.

`data/simblock_primary/scenario_coverage6s.csv`: scenario summaries over ten seeds.

The corrected parser groups fragmented SimBlock log entries by unique block identifier and deduplicates node IDs before computing coverage.

### Stable-regime pilot
`data/simblock_stable_pilot/`: ECDSA, 2000 tx/block, N=4000, intervals 30/60/120 s, five seeds each.

### Stable-regime final series
`data/simblock_stable_full/`: ECDSA, Dilithium2, SPHINCS+; 2000 tx/block; N=4000; interval=120 s; FULL; ten seeds per scheme.

### Compact block relay sensitivity
`data/simblock_cbr/`: the same three schemes; 2000 tx/block; N=2000; interval=6 s; `CBR_USAGE_RATE=1.0`; FULL; ten seeds per scheme. SimBlock compact block size was 18,000 B and the default CBR failure rates were retained.

## Solochain/Locust component

### Final controlled dataset (v3b)
`data/solochain_v3b/surowe_wyniki_v3b.csv`: 90 restarted run-level observations.

`data/solochain_v3b/suma_wyniki_v3b.csv`: 18 condition-level summaries (3 schemes × 3 user levels × 2 runtime variants).

The exact v3b code is under `code/solochain/v3b/`. Its `MANIFEST.txt` is preserved as `docs/solochain/MANIFEST_v3b.txt`.

Key final v3b settings verified from `run_matrix_v3b.sh`:
- users: 1, 10, 100;
- five repetitions per condition;
- 120 s measurement window;
- warm-up: U/20 + 12 s;
- six Locust worker processes, spawn rate 20 users/s;
- `--stop-timeout 10`;
- node restart and clean base path before each run;
- experiment aborts if the transaction pool does not empty;
- transaction-pool monitoring during each run;
- default and raised runtime variants use the same RPC/pool limits.

### Independent repeat series (v3)
`data/solochain_repeat_v3/` contains the first complete controlled series retained only as a reproducibility check. `code/analysis/compare_v3_v3b.py` reproduces the reported maximum differences: about 0.72% in throughput and 0.77 percentage points in inclusion ratio.

### Binary artifacts
`code/solochain/binaries/` contains the exact `node-default` and `node-raised` binaries supplied with the v3b package. Their SHA-256 hashes are given in `SHA256SUMS.txt` and match the hashes in the v3b manifest.

Base Solochain source commit: `2610f22b838f65bfeec9791ede17827b74e1ac50` (Polkadot SDK Solochain Template stable2503). Build instructions and the local runtime patch are documented in `docs/solochain/MANIFEST_v3b.txt` and included under `code/solochain/v3b/`.

**Final v3b build environment recorded in the supplied manifest:** Ubuntu 26.04 LTS, Linux 7.0.0-31-generic, glibc 2.43, rustc/cargo 1.97.1, Python 3.14.4, Locust 2.46.2, 8 vCPU and 7.2 GiB RAM. See `KNOWN_MANUSCRIPT_CORRECTIONS.md` for the manuscript version discrepancy discovered during archive assembly.

## Load-test duration data

`data/loadtest_duration/wyniki_duration_sweep.csv` contains 225 run-level observations used to select the 120 s measurement window. `derived/figure_data/fig4_duration_summary.csv` is the aggregated source for Fig. 4.

`derived/figure_data/fig5_runtime_summary.csv` and `derived/tables/table6_runtime_results_source.csv` are concise extracts from the final v3b summary underlying Fig. 5 and Table 6.

## Reproducing network analysis

Primary analysis (with raw logs available):
```bash
python3 code/analysis/analiza_pokrycie_6s_v6.py --kontrola
```
Stable/CBR analysis:
```bash
python3 code/analysis/analiza_okno.py wyniki_stable
python3 code/analysis/analiza_okno.py wyniki_cbr --okno 6
```
Bootstrap/figure derivations:
```bash
python3 code/analysis/bootstrap_statistics.py
python3 code/analysis/make_figure_data.py
```

Raw SimBlock propagation logs are not included because they contain hundreds of millions of reception records and occupy several GB. The run-level CSVs are the minimal processed numerical dataset underlying the reported network tables, figures and statistics.

## Reproducing Solochain analysis

Install the Python environment from:
```text
code/solochain/v3b/requirements_pqc_env.txt
```
Build the node from the base commit and apply the included runtime patch/pallet as described in `docs/solochain/MANIFEST_v3b.txt`, or use the exact archived binaries.

The recorded v3b launch command was:
```bash
M_LOGDIR=logs_final_v3b bash run_matrix_v3b.sh
```
with `NODE_BIN_DEFAULT=~/node-default` and `NODE_BIN_RAISED=~/node-raised`.

## Important provenance notes
1. Do not use older T90/stale-rate outputs that treated SimBlock log fragments as independent blocks.
2. A max timestamp in the propagation log is a propagation delay, not the simulated end time; per-run simulated end times were not retained.
3. `NetworkConfiguration.java` was not modified and is included only as an unmodified reference.
4. Final observed coverage uses all retained reception records; it is not an unlimited-time endpoint.
5. Inclusion latency is conditional on inclusion and must be interpreted with the inclusion ratio.
6. CPU/RAM in the load test describe the whole VM, because node and Locust shared the same eight vCPUs.

## Data/code availability statement draft

> All run-level processed datasets underlying the figures, tables and statistical analyses, together with the analysis scripts, corrected SimBlock parser and configuration changes, Solochain runtime patch, custom pallet, test vectors, final v3b load-test harness and exact experimental node binaries, are archived in Zenodo at **[DOI TO BE INSERTED]**.

## Version
- Package version: **1.0-rc1**
- Status: **release candidate; not yet the final public Zenodo release**

## Package scope

This archive contains only files required to reproduce or verify the results reported in the manuscript: processed run-level data, derived figure/table data, analysis scripts, modified simulation/runtime code, load-test code, test vectors, binaries and provenance metadata. Internal reports, diagnostic run logs, draft notes and duplicate PNG summary tables are intentionally excluded.
