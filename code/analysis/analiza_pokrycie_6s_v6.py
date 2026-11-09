#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
v6 - wersja uwzgledniajaca fragmentacje dziennika propagacji.

CO DIAGNOSTYKA POKAZALA

W logach z duzym obciazeniem ten sam blok wystepuje w dzienniku propagacji
WIELOKROTNIE, za kazdym razem z czescia swoich linii odbioru:

    sphincs_2000_N4000_seed10:  624 352 wpisy naglowkowe -> 2 103 rozne bloki
    dilithium_2000_N4000_seed10: 71 617 wpisow            ->   827 roznych blokow
    ecdsa_500_N500_seed10:          129 wpisow            ->   129 roznych blokow

Identyfikator "@<hash>:<wysokosc>" JEST unikalny na blok - potwierdza to lista
osieroconych, w ktorej 2 005 wpisow to 2 005 roznych kluczy. Powtarzaja sie
natomiast same wpisy naglowkowe.

Wszystkie poprzednie wersje liczyly pokrycie na WPIS naglowkowy, czyli na
fragment, a nie na blok. Dlatego dla SPHINCS+ wychodzily wartosci rzedu 1e-6:
pojedynczy fragment zawiera kilkanascie odbiorow z 4000 wezlow.

CO ROBI v6

  * grupuje wszystkie fragmenty po identyfikatorze bloku,
  * dla kazdego bloku bierze ZBIOR roznych wezlow (mapa bitowa), wiec
    powtorzone odbiory tego samego wezla nie licza sie dwa razy,
  * wezel wchodzi do okna, jesli MA CHOCIAZ JEDNA linie odbioru z t <= 6000 ms,
    liczone od utworzenia bloku,
  * blok bez ani jednej linii odbioru w calym dzienniku dostaje coverage = 0
    i zostaje w mianowniku (wymaganie promotorki),
  * wpisy z listy osieroconych nie tworza nowych blokow - to te same bloki,
    ktore wystepuja wyzej z odbiorami.

Pamiec: mapa bitowa N bitow na blok, czyli 500 B przy N = 4000. Przy kilku
tysiacach blokow na przebieg to kilka MB - bez ryzyka OOM.

Uruchomienie:
    python3 analiza_pokrycie_6s_v6.py --kontrola
    nohup python3 -u analiza_pokrycie_6s_v6.py > v6.log 2>&1 &
"""

import csv
import re
import sys
from pathlib import Path

import numpy as np

# ------------------------------------------------------------------ ustawienia

KATALOGI = [
    (Path("wyniki"), "full"),
    (Path("wyniki_zero_verify"), "zero_verify"),
]
REF_COVERAGE = Path("wyniki_koncowe/run_coverage6s.csv")   # lista run_id do kontroli
OUT = Path("wyniki_v6")

OKNO_MS = 6000
PROGI = (0.90, 0.50)

RE_RUN = re.compile(
    r"^(?P<alg>ecdsa|dilithium|sphincs)_(?P<tx>\d+)_N(?P<n>\d+)_seed(?P<seed>\d+)"
    r"(?:_(?P<mode>full|zero_verify|zero))?$"
)


def run_id_z_pliku(sciezka: Path, mode: str):
    m = RE_RUN.match(sciezka.stem)
    if not m:
        return None
    base = f"{m.group('alg')}_{m.group('tx')}_N{m.group('n')}_seed{m.group('seed')}"
    return (f"{base}_{mode}", m.group("alg"), int(m.group("tx")),
            int(m.group("n")), int(m.group("seed")), mode)


def przetworz_log(sciezka: Path, n_wezlow: int):
    # SimBlock numeruje wezly od 1 do N, wiec mapa musi objac indeks N
    bajtow = (n_wezlow + 8) // 8
    w_oknie = {}      # klucz bloku -> mapa bitowa wezlow z t <= OKNO_MS
    wszystkie = {}    # klucz bloku -> mapa bitowa wszystkich wezlow
    ogon = []

    bm_okno = None
    bm_wsz = None
    wpisow = 0
    linii = 0
    poza_zakresem = 0
    max_znacznik = 0

    with open(sciezka, "r", buffering=1 << 20) as f:
        for linia in f:
            if not linia or linia == "\n":
                continue
            c = linia[0]
            if c == "s":
                klucz = linia.rstrip("\n")
                wpisow += 1
                bm_wsz = wszystkie.get(klucz)
                if bm_wsz is None:
                    bm_wsz = bytearray(bajtow)
                    wszystkie[klucz] = bm_wsz
                    bm_okno = bytearray(bajtow)
                    w_oknie[klucz] = bm_okno
                else:
                    bm_okno = w_oknie[klucz]
            elif c.isdigit():
                przecinek = linia.find(",")
                if przecinek < 0:
                    ogon.append(int(linia))
                    continue
                if bm_wsz is None:
                    continue
                nid = int(linia[:przecinek])
                t = int(linia[przecinek + 1:])
                linii += 1
                if t > max_znacznik:
                    max_znacznik = t
                if nid > n_wezlow:
                    poza_zakresem += 1
                    continue
                bm_wsz[nid >> 3] |= 1 << (nid & 7)
                if t <= OKNO_MS:
                    bm_okno[nid >> 3] |= 1 << (nid & 7)

    pokrycia = []
    pokrycia_konc = []
    for klucz, bm in wszystkie.items():
        ile_wsz = int.from_bytes(bm, "little").bit_count()
        ile_okn = int.from_bytes(w_oknie[klucz], "little").bit_count()
        pokrycia.append(ile_okn / n_wezlow)
        pokrycia_konc.append(ile_wsz / n_wezlow)

    p = np.asarray(pokrycia, dtype=np.float64)
    pk = np.asarray(pokrycia_konc, dtype=np.float64)

    wynik = {
        "blokow": int(p.size),
        "wpisow_naglowkow": wpisow,
        "fragmentow_na_blok": round(wpisow / p.size, 3) if p.size else 0.0,
        "linii_odbioru": linii,
        "wezlow_unikalnych_lacznie": int(round(pk.sum() * n_wezlow)),
        "blokow_bez_odbioru": int((pk == 0).sum()),
        "pokrycie6s_srednie": float(p.mean()) if p.size else 0.0,
        "pokrycie6s_mediana": float(np.median(p)) if p.size else 0.0,
        "pokrycie6s_q25": float(np.quantile(p, 0.25)) if p.size else 0.0,
        "pokrycie6s_q75": float(np.quantile(p, 0.75)) if p.size else 0.0,
        "pokrycie_koncowe_srednie": float(pk.mean()) if pk.size else 0.0,
        "max_propagacja_ms": max_znacznik,
        "wezly_poza_zakresem": poza_zakresem,
    }
    for prog in PROGI:
        wynik[f"udzial_blokow_{int(prog * 100)}proc_w_6s"] = (
            float((p >= prog).mean()) if p.size else 0.0)
    wynik["ogon"] = ogon
    return wynik


KOL_RUN = [
    "run_id", "algorithm", "tx_count", "nodes", "seed", "mode",
    "blokow", "blokow_bez_odbioru",
    "pokrycie6s_srednie", "pokrycie6s_mediana", "pokrycie6s_q25", "pokrycie6s_q75",
    "udzial_blokow_90proc_w_6s", "udzial_blokow_50proc_w_6s",
    "pokrycie_koncowe_srednie",
    "wpisow_naglowkow", "fragmentow_na_blok", "linii_odbioru",
    "wezlow_unikalnych_lacznie", "wezly_poza_zakresem",
]
KOL_TIME = ["run_id", "algorithm", "tx_count", "nodes", "seed", "mode",
            "average_orphans_size", "simulation_time_ms", "simulation_time_s",
            "ogon_wartosci", "max_propagacja_ms"]
METRYKI = ["pokrycie6s_srednie", "pokrycie6s_mediana",
           "udzial_blokow_90proc_w_6s", "udzial_blokow_50proc_w_6s",
           "pokrycie_koncowe_srednie"]


def wczytaj_zrobione(plik: Path):
    if not plik.exists():
        return set()
    with open(plik, newline="") as f:
        return {w["run_id"] for w in csv.DictReader(f) if w.get("run_id")}


def main():
    kontrola_only = "--kontrola" in sys.argv

    brak = [str(d) for d, _ in KATALOGI if not d.is_dir()]
    if brak:
        sys.exit("BLAD: nie ma katalogow: " + ", ".join(brak) + f"\n(jestem w {Path.cwd()})")

    znalezione = {}
    pominiete = []
    for katalog, mode in KATALOGI:
        ile = 0
        for p in sorted(katalog.rglob("*.txt")):
            info = run_id_z_pliku(p, mode)
            if info is None:
                pominiete.append(str(p))
                continue
            if info[0] in znalezione:
                continue
            znalezione[info[0]] = (p,) + info[1:]
            ile += 1
        print(f"  {katalog}/ -> tryb {mode}: {ile} plikow")
    print(f"Razem: {len(znalezione)} plikow")
    if pominiete:
        print(f"Pominieto {len(pominiete)}, np.: {pominiete[:5]}")

    if REF_COVERAGE.exists():
        ref = wczytaj_zrobione(REF_COVERAGE)
        print(f"Kontrola wzgledem {REF_COVERAGE}: oczekiwano {len(ref)}")
        print(f"  brakuje logow : {len(sorted(ref - set(znalezione)))}")
        print(f"  spoza listy   : {len(sorted(set(znalezione) - ref))}")

    if kontrola_only:
        print("\nTryb --kontrola: nic nie policzylam.")
        return

    OUT.mkdir(exist_ok=True)
    plik_run = OUT / "run_coverage6s.csv"
    plik_time = OUT / "run_simulation_time.csv"
    zrobione = wczytaj_zrobione(plik_run)
    if zrobione:
        print(f"Wznawiam: {len(zrobione)} juz policzonych.")

    nowy_r, nowy_t = not plik_run.exists(), not plik_time.exists()
    f_run = open(plik_run, "a", newline="")
    f_time = open(plik_time, "a", newline="")
    w_run = csv.DictWriter(f_run, fieldnames=KOL_RUN)
    w_time = csv.DictWriter(f_time, fieldnames=KOL_TIME)
    if nowy_r:
        w_run.writeheader()
    if nowy_t:
        w_time.writeheader()

    do_zrobienia = [k for k in sorted(znalezione) if k not in zrobione]
    print(f"Do policzenia: {len(do_zrobienia)}\n", flush=True)

    for i, run_id in enumerate(do_zrobienia, 1):
        sciezka, alg, tx, nodes, seed, mode = znalezione[run_id]
        m = przetworz_log(sciezka, nodes)
        wiersz = {"run_id": run_id, "algorithm": alg, "tx_count": tx,
                  "nodes": nodes, "seed": seed, "mode": mode}
        for k in KOL_RUN[6:]:
            wiersz[k] = m[k]
        w_run.writerow(wiersz)
        ogon = m["ogon"]
        w_time.writerow({
            "run_id": run_id, "algorithm": alg, "tx_count": tx,
            "nodes": nodes, "seed": seed, "mode": mode,
            "average_orphans_size": ogon[0] if len(ogon) > 0 else "",
            "simulation_time_ms": ogon[-1] if len(ogon) > 1 else "",
            "simulation_time_s": round(ogon[-1] / 1000.0, 3) if len(ogon) > 1 else "",
            "ogon_wartosci": " ".join(str(x) for x in ogon),
            "max_propagacja_ms": m["max_propagacja_ms"],
        })
        f_run.flush()
        f_time.flush()
        print(f"[{i}/{len(do_zrobienia)}] {run_id}: blokow {m['blokow']}, "
              f"fragmentow/blok {m['fragmentow_na_blok']}, "
              f"bez odbioru {m['blokow_bez_odbioru']}, "
              f"pokrycie6s {m['pokrycie6s_srednie']:.4f}, "
              f">=90% {m['udzial_blokow_90proc_w_6s']:.4f}", flush=True)

    f_run.close()
    f_time.close()

    import pandas as pd
    df = pd.read_csv(plik_run)
    klucz = ["algorithm", "tx_count", "nodes", "mode"]
    agg = df.groupby(klucz)[METRYKI].agg(["mean", "median", "std", "count"])
    agg.columns = [f"{a}_{'sd' if b == 'std' else ('n' if b == 'count' else b)}"
                   for a, b in agg.columns]
    dod = df.groupby(klucz).agg(
        blokow_mean=("blokow", "mean"),
        blokow_bez_odbioru_mean=("blokow_bez_odbioru", "mean"),
        fragmentow_na_blok_mean=("fragmentow_na_blok", "mean"),
    )
    sce = agg.join(dod).reset_index()
    sce.to_csv(OUT / "scenario_coverage6s.csv", index=False)

    print(f"\nGotowe. {len(df)} przebiegow, {len(sce)} scenariuszy.")
    print(f"  {plik_run}\n  {OUT/'scenario_coverage6s.csv'}\n  {plik_time}")
    print(f"\nFragmentacja dziennika: srednio {df.fragmentow_na_blok.mean():.1f} "
          f"wpisow naglowkowych na blok (min {df.fragmentow_na_blok.min():.1f}, "
          f"max {df.fragmentow_na_blok.max():.1f})")
    print(f"Blokow bez ani jednej linii odbioru: lacznie "
          f"{int(df.blokow_bez_odbioru.sum())}, max na przebieg "
          f"{int(df.blokow_bez_odbioru.max())}")
    poza = int(df.wezly_poza_zakresem.sum())
    print(f"Linii z id wezla >= N (powinno byc 0): {poza}")
    nadmiar = df.linii_odbioru - df.wezlow_unikalnych_lacznie
    print(f"Linii odbioru powtorzonych (ta sama para blok-wezel): "
          f"lacznie {int(nadmiar.sum()):,}, "
          f"czyli {100*nadmiar.sum()/max(df.linii_odbioru.sum(),1):.1f}% wszystkich linii")


if __name__ == "__main__":
    main()
