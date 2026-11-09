# Data dictionary

## `data/simblock_primary/run_coverage6s.csv`

Key fields:
- `run_id`: unique run identifier.
- `algorithm`: `ecdsa`, `dilithium`, `sphincs`.
- `tx_count`: transactions per simulated block.
- `nodes`: configured node count N.
- `seed`: random seed.
- `mode`: `full` or `zero_verify`.
- `blokow`: number of unique block identifiers after fragment grouping.
- `pokrycie6s_srednie`: run mean of C_b(6s), fraction 0..1.
- `pokrycie6s_mediana`, `pokrycie6s_q25`, `pokrycie6s_q75`: distribution of per-block 6 s coverage.
- `udzial_blokow_90proc_w_6s`: fraction of unique blocks reaching >=90% of nodes within 6 s.
- `udzial_blokow_50proc_w_6s`: fraction reaching >=50% within 6 s.
- `pokrycie_koncowe_srednie`: mean final observed coverage from all retained reception records.
- `fragmentow_na_blok`: mean number of log fragments per unique block.
- `wezly_poza_zakresem`: validation field; expected 0.

## Stable/CBR `run_coverage.csv`

Additional fields:
- `interval_s`: configured mean block interval.
- `cbr_usage_rate`: CBR usage rate; blank/0 for full relay, 1.0 for CBR sensitivity.
- `okno_s`: coverage evaluation window.
- `orphan_blokow`, `orphan_rate`, `orphan_unikalnych`: available for stable-regime files.
- `pokrycie_okno_srednie`: mean C_b(W), fraction 0..1.
- `udzial_blokow_90proc_w_oknie`, `udzial_blokow_50proc_w_oknie`: fixed-window threshold fractions.
- `max_propagacja_ms`: maximum recorded propagation delay in the run.
- `N_zgodne`: validation flag for node-ID range.

## Units

Coverage columns in raw run/scenario CSV files are fractions in [0,1] unless the column name explicitly states otherwise. Derived figure/table files convert coverage to percentage values where indicated by column names.


## `data/solochain_v3b/surowe_wyniki_v3b.csv`

One row per restarted controlled run (90 rows). Key fields:
- `tag`, `runtime`, `algo`, `users`, `run`: run identity.
- `tps_post_warmup`: included throughput in the 120 s measurement window.
- `request_rate`, `fail_rate`, `error_types`: generator-side submission metrics.
- `inclusion_ratio`, `not_included`: fate of transactions submitted in the measurement window.
- `lat_mean_s`, `lat_median_s`, `lat_p95_s`: submission-to-detected-inclusion latency, included transactions only.
- `cpu_pct`, `ram_mb`: whole-VM resource use in the measurement window.
- `ext_bytes_mean`, `ext_bytes_max`, `len_used_pct_of_normal`: block/extrinsic byte metrics.
- `weight_measured_mean`, `weight_est_mean`, `weight_est_pct_of_normal`: block-weight metrics.
- `build_ms_mean`, `build_ms_per_tx`, `blocks_hit_deadline_frac`: proposer/build-time diagnostics.
- `pool_*`: transaction-pool monitoring metrics.

## `data/solochain_v3b/suma_wyniki_v3b.csv`

Condition-level mean/SD/min/max summaries over five restarted runs for each of 18 conditions (3 schemes × 3 user levels × 2 runtime variants).

## `data/solochain_repeat_v3/`

The first complete controlled series used only as an independent repeat. The v3-v3b comparison is in `derived/tables/v3_vs_v3b_reproducibility.csv`.

## `data/loadtest_duration/wyniki_duration_sweep.csv`

225 run-level observations from the preliminary duration study: 3 algorithms × 3 user levels (10, 100, 300) × 5 durations (30, 60, 90, 120, 180 s) × 5 repetitions. `tps_po_rozgrzewce` is the throughput after warm-up used in Fig. 4.

## Binary provenance

`code/solochain/binaries/SHA256SUMS.txt` contains SHA-256 checksums of the exact default and raised binaries supplied for v3b.
