#!/bin/bash
# Pilot "stable regime" - 15 uruchomien.
# ECDSA, 2000 tx, N = 4000, interval = 30 / 60 / 120 s, 5 seedow.
#
# verifms = 161 ms to wartosc PRZELICZONA, ta sama, ktora byla uzyta w serii
# 1200 przebiegow (potwierdzona przez t_min_ms w 1200/1200). NIE jest to
# 255 ms ze starej tabeli scenariuszy.
#
# CBR swiadomie NIE jest tu podawane - zostaje wartosc domyslna 0.0,
# czyli taka jak w dotychczasowych przebiegach.
set -u

if [ ! -x ./gradlew ]; then
  echo "BLAD: nie widze ./gradlew - uruchom skrypt z katalogu ~/simblock" >&2
  exit 1
fi

OUT=wyniki_stable
mkdir -p "$OUT"

BSIZE=500000      # ECDSA, 2000 tx
VMS=161           # ECDSA, 2000 tx, wartosc przeliczona
NODES=4000
SEEDS="10 20 30 40 50"

# Log SimBlocka konczy sie dwiema liczbami bez przecinka (averageOrphansSize
# i simulationTime). Plik urwany w polowie ich nie ma - dzieki temu
# wznawianie nie pomija przebiegow przerwanych w trakcie zapisu.
kompletny() {
  [ -s "$1" ] && tail -n 1 "$1" | grep -qE '^[0-9]+$'
}

zrobione=0
bledy=0

for iv in 30 60 120; do
  for s in $SEEDS; do
    PLIK="$OUT/ecdsa_2000_N${NODES}_int${iv}_seed${s}.txt"
    if kompletny "$PLIK"; then
      echo "pomijam (kompletny): $PLIK"
      zrobione=$((zrobione + 1))
      continue
    fi
    if [ -e "$PLIK" ]; then
      echo "plik niekompletny, licze od nowa: $PLIK"
    fi
    echo ">>> interval=${iv}s  seed=$s  $(date +%H:%M:%S)"
    if ./gradlew run -q \
         -Dseed=$s \
         -Dnodes=$NODES \
         -Dblocksize=$BSIZE \
         -Dverifms=$VMS \
         -Dinterval=$((iv * 1000)) \
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
      echo "UWAGA: gradlew zwrocil blad dla interval=${iv}s seed=$s - usuwam plik" >&2
      rm -f "$PLIK"
      bledy=$((bledy + 1))
    fi
  done
done

echo
echo "Kompletnych plikow: $zrobione / 15,  bledow: $bledy"
[ "$bledy" -eq 0 ] || echo "Uruchom skrypt ponownie - dolicza tylko brakujace."
