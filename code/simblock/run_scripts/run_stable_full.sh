#!/bin/bash
# Pelna seria "stable regime" - 30 uruchomien.
# ECDSA + Dilithium2 + SPHINCS+, 2000 tx, N = 4000, 10 seedow, FULL.
# Interval podaje sie jako argument, np.:  ./run_stable_full.sh 30
#
# CBR swiadomie NIE jest podawane - zostaje domyslne 0.0, tak jak
# w dotychczasowych przebiegach. To jest eksperyment o intervalu,
# nie o compact block relay.
set -u

if [ $# -ne 1 ]; then
  echo "Uzycie: $0 <interval_w_sekundach>    np. $0 30" >&2
  exit 1
fi
IV=$1
case "$IV" in (*[!0-9]*|"") echo "BLAD: interval musi byc liczba sekund" >&2; exit 1;; esac

if [ ! -x ./gradlew ]; then
  echo "BLAD: nie widze ./gradlew - uruchom skrypt z katalogu ~/simblock" >&2
  exit 1
fi

OUT=wyniki_stable_full
mkdir -p "$OUT"

NODES=4000
SEEDS="10 20 30 40 50 60 70 80 90 100"

# algorytm  blocksize  verifms   (wartosci przeliczone, te same co w serii 1200)
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
LACZNIE=$(( ${#SCENARIOS[@]} * $(echo $SEEDS | wc -w) ))

echo "Interval: ${IV} s   Przebiegow do wykonania: $LACZNIE"
echo

for scen in "${SCENARIOS[@]}"; do
  set -- $scen
  ALG=$1; BSIZE=$2; VMS=$3
  for s in $SEEDS; do
    PLIK="$OUT/${ALG}_2000_N${NODES}_int${IV}_seed${s}.txt"
    if kompletny "$PLIK"; then
      echo "pomijam (kompletny): $PLIK"
      zrobione=$((zrobione + 1))
      continue
    fi
    [ -e "$PLIK" ] && echo "plik niekompletny, licze od nowa: $PLIK"
    echo ">>> $ALG  interval=${IV}s  seed=$s  $(date +%H:%M:%S)"
    if ./gradlew run -q \
         -Dseed=$s \
         -Dnodes=$NODES \
         -Dblocksize=$BSIZE \
         -Dverifms=$VMS \
         -Dinterval=$((IV * 1000)) \
         > "$PLIK" < /dev/null
    then
      if kompletny "$PLIK"; then
        zrobione=$((zrobione + 1))
      else
        echo "UWAGA: $PLIK nie ma poprawnego konca - usuwam" >&2
        rm -f "$PLIK"; bledy=$((bledy + 1))
      fi
    else
      echo "UWAGA: gradlew zwrocil blad dla $ALG seed=$s - usuwam plik" >&2
      rm -f "$PLIK"; bledy=$((bledy + 1))
    fi
  done
done

echo
echo "Kompletnych plikow: $zrobione / $LACZNIE,  bledow: $bledy"
[ "$bledy" -eq 0 ] || echo "Uruchom skrypt ponownie z tym samym intervalem - dolicza tylko brakujace."
echo "Analiza:  python3 analiza_okno.py $OUT"
