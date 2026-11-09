#!/usr/bin/env bash
set -euo pipefail

# run_article_ablation.sh
# Additional paired ablation for the scientific article.
# Keeps the original block size, N and seed, but sets verification delay to 0 ms.
# Expected to be run from the SimBlock project root (where ./gradlew exists).

OUTDIR="${OUTDIR:-wyniki_zero_verify}"
mkdir -p "$OUTDIR"

SEEDS=(10 20 30 40 50 60 70 80 90 100)
NODES=(500 1000 1500 2000 4000)

# name blocksize_bytes original_verifms_ms
SCENARIOS=(
  "ecdsa_500 125000 33"
  "ecdsa_1000 250000 65"
  "ecdsa_1500 375000 110"
  "ecdsa_2000 500000 161"
  "dilithium_500 1941000 40"
  "dilithium_1000 3882000 75"
  "dilithium_1500 5823000 129"
  "dilithium_2000 7764000 135"
  "sphincs_500 4019000 1141"
  "sphincs_1000 8038000 2282"
  "sphincs_1500 12057000 3410"
  "sphincs_2000 16076000 4938"
)

MANIFEST="$OUTDIR/manifest_zero_verify.csv"
if [[ ! -f "$MANIFEST" ]]; then
  echo "run_id,algorithm,tx_count,nodes,seed,block_size_B,verifms_full,verifms_run,mode,output_file,exit_code" > "$MANIFEST"
fi

echo "Building SimBlock..."
./gradlew build -x test

total=$(( ${#SCENARIOS[@]} * ${#NODES[@]} * ${#SEEDS[@]} ))
i=0

for scen in "${SCENARIOS[@]}"; do
  read -r NAME BSIZE VMS_FULL <<< "$scen"
  ALGO="${NAME%_*}"
  TX="${NAME##*_}"

  for n in "${NODES[@]}"; do
    for s in "${SEEDS[@]}"; do
      i=$((i+1))
      OUT="$OUTDIR/${NAME}_N${n}_seed${s}_zero.txt"
      RUN_ID="${NAME}_N${n}_seed${s}_zero"

      if [[ -s "$OUT" ]]; then
        echo "[$i/$total] SKIP existing: $OUT"
        continue
      fi

      echo "[$i/$total] $NAME N=$n seed=$s blocksize=$BSIZE verifms=0"

      set +e
      ./gradlew run -q \
        -Dseed="$s" \
        -Dnodes="$n" \
        -Dblocksize="$BSIZE" \
        -Dverifms=0 \
        > "$OUT"
      code=$?
      set -e

      echo "$RUN_ID,$ALGO,$TX,$n,$s,$BSIZE,$VMS_FULL,0,zero_verify,$OUT,$code" >> "$MANIFEST"

      if [[ "$code" -ne 0 ]]; then
        echo "ERROR: run failed ($code): $RUN_ID" >&2
      fi
    done
  done
done

echo "Done. Results: $OUTDIR/"
echo "Manifest: $MANIFEST"
