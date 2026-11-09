#!/bin/bash
# CBR sensitivity - 30 uruchomien.
# CBR_USAGE_RATE = 1.0, interval = 6 s, N = 2000, 2000 tx,
# ECDSA + Dilithium2 + SPHINCS+, 10 seedow.
#
# verifms to wartosci PRZELICZONE (161 / 135 / 4938), te same, ktore byly uzyte
# w serii 1200 przebiegow. NIE sa to 255 / 233 / 5105 ze starej tabeli.
#
# -Dinterval=6000 rowna sie wartosci domyslnej - podane jawnie, zeby
# w logu uruchomienia bylo widac, z czym przebieg poszedl.
set -u

if [ ! -x ./gradlew ]; then
  echo "BLAD: nie widze ./gradlew - uruchom skrypt z katalogu ~/simblock" >&2
  exit 1
fi

OUT=wyniki_cbr
mkdir -p "$OUT"

NODES=2000
INTERVAL_MS=6000
CBR=1.0
SEEDS="10 20 30 40 50 60 70 80 90 100"

# algorytm  blocksize  verifms
SCENARIOS=(
  "ecdsa      500000    161"
  "dilithium  7764000   135"
  "sphincs    16076000  4938"
)

kompletny() {
  [ -s "$1" ] && tail -n 1 "$1" | grep -qE '^[0-9]+$'
}

zrobione=0
bledy=0

for scen in "${SCENARIOS[@]}"; do
  set -- $scen
  ALG=$1; BSIZE=$2; VMS=$3
  for s in $SEEDS; do
    PLIK="$OUT/${ALG}_2000_N${NODES}_cbr100_int6_seed${s}.txt"
    if kompletny "$PLIK"; then
      echo "pomijam (kompletny): $PLIK"
      zrobione=$((zrobione + 1))
      continue
    fi
    if [ -e "$PLIK" ]; then
      echo "plik niekompletny, licze od nowa: $PLIK"
    fi
    echo ">>> $ALG  seed=$s  $(date +%H:%M:%S)"
    if ./gradlew run -q \
         -Dseed=$s \
         -Dnodes=$NODES \
         -Dblocksize=$BSIZE \
         -Dverifms=$VMS \
         -Dinterval=$INTERVAL_MS \
         -Dcbr=$CBR \
         > "$PLIK"
    then
      if kompletny "$PLIK"; then
        zrobione=$((zrobione + 1))
      else
        echo "UWAGA: $PLIK nie ma poprawnego konca - usuwam" >&2
        rm -f "$PLIK"
        bledy=$((bledy + 1))
      fi
    else
      echo "UWAGA: gradlew zwrocil blad dla $ALG seed=$s - usuwam plik" >&2
      rm -f "$PLIK"
      bledy=$((bledy + 1))
    fi
  done
done

echo
echo "Kompletnych plikow: $zrobione / 30,  bledow: $bledy"
[ "$bledy" -eq 0 ] || echo "Uruchom skrypt ponownie - dolicza tylko brakujace."
