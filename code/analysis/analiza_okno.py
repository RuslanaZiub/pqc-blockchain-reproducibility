#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Analiza pokrycia w oknie o zadanej dlugosci - wersja uogolniona z v6.

Parser jest ten sam, co w finalnej analizie coverage@6s:
  * fragmenty jednego bloku grupowane po identyfikatorze <hash>:<wysokosc>,
  * dla kazdego bloku liczony ZBIOR roznych wezlow (mapa bitowa),
  * wezel wchodzi do okna, jesli ma co najmniej jedna linie odbioru
    ze znacznikiem t <= OKNO, liczonym od utworzenia bloku,
  * blok bez ani jednej linii odbioru dostaje coverage = 0 i zostaje
    w mianowniku,
  * wpisy z listy osieroconych nie tworza nowych blokow.

Dlugosc okna bierze sie z nazwy pliku (czlon int<sekundy>), czyli dla
    ecdsa_2000_N4000_int30_seed10.txt
okno wynosi 30 s. Mozna ja nadpisac przelacznikiem --okno <sekundy>.

Uruchomienie:
    python3 analiza_okno.py wyniki_stable
    python3 analiza_okno.py wyniki_cbr
    python3 analiza_okno.py wyniki_cbr --okno 6

Wyniki trafiaja do <katalog>_analiza/. Skrypt jest wznawialny.
"""

import csv
import re
import sys
from pathlib import Path

import numpy as np

PROGI = (0.90, 0.50)

RE_RUN = re.compile(
    r"^(?P<alg>ecdsa|dilithium|sphincs)_(?P<tx>\d+)_N(?P<n>\d+)"
    r"(?:_cbr(?P<cbr>\d+))?_int(?P<iv>\d+)_seed(?P<seed>\d+)$"
)


def opis_pliku(sciezka: Path):
    m = RE_RUN.match(sciezka.stem)
    if not m:
        return None
    cbr = m.group("cbr")
    return {
        "run_id": sciezka.stem,
        "algorithm": m.group("alg"),
        "tx_count": int(m.group("tx")),
        "nodes": int(m.group("n")),
        "interval_s": int(m.group("iv")),
        "cbr_usage_rate": (int(cbr) / 100.0) if cbr else "",
        "seed": int(m.group("seed")),
    }


def przetworz_log(sciezka: Path, n_wezlow: int, okno_ms: int):
    bajtow = (n_wezlow + 8) // 8      # SimBlock numeruje wezly od 1 do N
    w_oknie, wszystkie = {}, {}
    bm_run = bytearray(bajtow)        # suma wszystkich wezlow w calym przebiegu
    ogon = []
    bm_okno = bm_wsz = None
    wpisow = linii = poza = 0
    max_znacznik = 0
    # Bloki osierocone: SimBlock wypisuje ich liste po dzienniku propagacji
    # (Main.java, linia 188) jako naglowki BEZ ani jednej linii odbioru.
    # Zliczam wlasnie takie wpisy - to jest liczba orphan blocks.
    biezacy_klucz = None
    biezacy_licznik = 0
    naglowkow_bez_odbioru = 0
    klucze_osierocone = set()

    def zamknij_wpis():
        nonlocal naglowkow_bez_odbioru
        if biezacy_klucz is not None and biezacy_licznik == 0:
            naglowkow_bez_odbioru += 1
            klucze_osierocone.add(biezacy_klucz)

    with open(sciezka, "r", buffering=1 << 20) as f:
        for linia in f:
            if not linia or linia == "\n":
                continue
            c = linia[0]
            if c == "s":
                klucz = linia.rstrip("\n")
                zamknij_wpis()
                biezacy_klucz = klucz
                biezacy_licznik = 0
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
                biezacy_licznik += 1
                if t > max_znacznik:
                    max_znacznik = t
                if nid > n_wezlow:
                    poza += 1
                    continue
                maska = 1 << (nid & 7)
                bm_wsz[nid >> 3] |= maska
                bm_run[nid >> 3] |= maska
                if t <= okno_ms:
                    bm_okno[nid >> 3] |= maska

    zamknij_wpis()

    pokrycia, pokrycia_konc = [], []
    for klucz, bm in wszystkie.items():
        pokrycia.append(int.from_bytes(w_oknie[klucz], "little").bit_count() / n_wezlow)
        pokrycia_konc.append(int.from_bytes(bm, "little").bit_count() / n_wezlow)

    p = np.asarray(pokrycia, dtype=np.float64)
    pk = np.asarray(pokrycia_konc, dtype=np.float64)

    # Kontrola, czy -Dnodes faktycznie dotarlo do symulacji. Bez niej blednie
    # przekazany parametr dalby po cichu zle pokrycie, bo mianownik bierze sie
    # z nazwy pliku, a nie z logu.
    calosc = int.from_bytes(bm_run, "little")
    wezlow_w_logu = calosc.bit_count()
    max_id = calosc.bit_length() - 1 if calosc else 0

    wynik = {
        "blokow": int(p.size),
        "orphan_blokow": naglowkow_bez_odbioru,
        "orphan_rate": round(naglowkow_bez_odbioru / p.size, 6) if p.size else 0.0,
        "orphan_unikalnych": len(klucze_osierocone),
        "blokow_bez_odbioru": int((pk == 0).sum()),
        "wezlow_w_logu": wezlow_w_logu,
        "max_id_wezla": max_id,
        "N_zgodne": 1 if max_id == n_wezlow else 0,
        "pokrycie_okno_srednie": float(p.mean()) if p.size else 0.0,
        "pokrycie_okno_mediana": float(np.median(p)) if p.size else 0.0,
        "pokrycie_okno_q25": float(np.quantile(p, 0.25)) if p.size else 0.0,
        "pokrycie_okno_q75": float(np.quantile(p, 0.75)) if p.size else 0.0,
        "pokrycie_koncowe_srednie": float(pk.mean()) if pk.size else 0.0,
        "wpisow_naglowkow": wpisow,
        "fragmentow_na_blok": round(wpisow / p.size, 3) if p.size else 0.0,
        "max_propagacja_ms": max_znacznik,
        "wezly_poza_zakresem": poza,
        "czas_wykonania_ms": ogon[-1] if len(ogon) > 1 else "",
    }
    for prog in PROGI:
        wynik[f"udzial_blokow_{int(prog * 100)}proc_w_oknie"] = (
            float((p >= prog).mean()) if p.size else 0.0)
    return wynik


KOL = ["run_id", "algorithm", "tx_count", "nodes", "interval_s", "cbr_usage_rate",
       "seed", "okno_s", "blokow", "orphan_blokow", "orphan_rate",
       "orphan_unikalnych", "blokow_bez_odbioru",
       "pokrycie_okno_srednie", "pokrycie_okno_mediana",
       "pokrycie_okno_q25", "pokrycie_okno_q75",
       "udzial_blokow_90proc_w_oknie", "udzial_blokow_50proc_w_oknie",
       "pokrycie_koncowe_srednie",
       "wpisow_naglowkow", "fragmentow_na_blok", "max_propagacja_ms",
       "wezlow_w_logu", "max_id_wezla", "N_zgodne",
       "wezly_poza_zakresem", "czas_wykonania_ms"]

METRYKI = ["pokrycie_okno_srednie", "pokrycie_okno_mediana",
           "udzial_blokow_90proc_w_oknie", "udzial_blokow_50proc_w_oknie",
           "pokrycie_koncowe_srednie"]


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    okno_arg = None
    for i, a in enumerate(sys.argv):
        if a == "--okno" and i + 1 < len(sys.argv):
            okno_arg = int(sys.argv[i + 1])
    if not args:
        sys.exit("Uzycie: python3 analiza_okno.py <katalog_z_logami> [--okno <sekundy>]")

    katalog = Path(args[0])
    if not katalog.is_dir():
        sys.exit(f"BLAD: nie ma katalogu {katalog}\n(jestem w {Path.cwd()})")

    out = Path(str(katalog) + "_analiza")
    out.mkdir(exist_ok=True)
    plik = out / "run_coverage.csv"

    zrobione = set()
    if plik.exists():
        with open(plik, newline="") as f:
            zrobione = {w["run_id"] for w in csv.DictReader(f) if w.get("run_id")}
        print(f"Wznawiam: {len(zrobione)} juz policzonych.")

    pliki, pominiete = {}, []
    for p in sorted(katalog.rglob("*.txt")):
        o = opis_pliku(p)
        if o is None:
            pominiete.append(p.name)
            continue
        pliki[o["run_id"]] = (p, o)
    print(f"Znaleziono {len(pliki)} plikow pasujacych do wzorca.")
    if pominiete:
        print(f"Pominieto {len(pominiete)}, np.: {pominiete[:5]}")
    if not pliki:
        sys.exit("Brak plikow do analizy - sprawdz nazwy (wzorzec: alg_tx_N<n>[_cbr<x>]_int<s>_seed<s>.txt)")

    nowy = not plik.exists()
    f_out = open(plik, "a", newline="")
    w_out = csv.DictWriter(f_out, fieldnames=KOL)
    if nowy:
        w_out.writeheader()

    do_zrobienia = [k for k in sorted(pliki) if k not in zrobione]
    print(f"Do policzenia: {len(do_zrobienia)}\n", flush=True)

    for i, run_id in enumerate(do_zrobienia, 1):
        sciezka, o = pliki[run_id]
        okno_s = okno_arg if okno_arg is not None else o["interval_s"]
        m = przetworz_log(sciezka, o["nodes"], okno_s * 1000)
        wiersz = dict(o)
        wiersz["okno_s"] = okno_s
        wiersz.update({k: m[k] for k in KOL if k in m})
        w_out.writerow(wiersz)
        f_out.flush()
        print(f"[{i}/{len(do_zrobienia)}] {run_id}: okno {okno_s}s, "
              f"blokow {m['blokow']}, fragm/blok {m['fragmentow_na_blok']}, "
              f"pokrycie {m['pokrycie_okno_srednie']:.4f}, "
              f">=90% {m['udzial_blokow_90proc_w_oknie']:.4f}", flush=True)

    f_out.close()

    import pandas as pd
    df = pd.read_csv(plik)
    klucz = ["algorithm", "tx_count", "nodes", "interval_s", "cbr_usage_rate", "okno_s"]
    klucz = [k for k in klucz if df[k].notna().any()]
    agg = df.groupby(klucz, dropna=False)[METRYKI].agg(["mean", "median", "std", "count"])
    agg.columns = [f"{a}_{'sd' if b == 'std' else ('n' if b == 'count' else b)}"
                   for a, b in agg.columns]
    dod = df.groupby(klucz, dropna=False).agg(
        blokow_mean=("blokow", "mean"),
        orphan_blokow_mean=("orphan_blokow", "mean"),
        orphan_rate_mean=("orphan_rate", "mean"),
        blokow_bez_odbioru_mean=("blokow_bez_odbioru", "mean"),
        fragmentow_na_blok_mean=("fragmentow_na_blok", "mean"))
    sce = agg.join(dod).reset_index()
    sce.to_csv(out / "scenario_coverage.csv", index=False)

    print(f"\nGotowe. {len(df)} przebiegow, {len(sce)} scenariuszy.")
    print(f"  {plik}\n  {out/'scenario_coverage.csv'}")
    print(f"\nBlokow bez ani jednej linii odbioru: {int(df.blokow_bez_odbioru.sum())}")
    print(f"Linii z id wezla spoza 1..N (powinno byc 0): {int(df.wezly_poza_zakresem.sum())}")
    zgodne = int(df.N_zgodne.sum())
    print(f"Kontrola -Dnodes (max id wezla == N): {zgodne} / {len(df)}")
    if zgodne < len(df):
        zle = df[df.N_zgodne == 0][["run_id", "nodes", "wezlow_w_logu", "max_id_wezla"]]
        print("  >>> UWAGA: w tych przebiegach liczba wezlow w logu nie zgadza sie")
        print("  >>> z N z nazwy pliku. Mianownik pokrycia moze byc zly - sprawdz,")
        print("  >>> czy -Dnodes dotarlo do symulacji, zanim uzyjesz tych wynikow.")
        print(zle.head(10).to_string(index=False))
    roznica = int((df.orphan_blokow != df.orphan_unikalnych).sum())
    print(f"Wpisy osierocone powtorzone (powinno byc 0 przebiegow): {roznica}")
    print("\n--- wyniki scenariuszowe ---")
    kol = [k for k in ["algorithm", "interval_s", "okno_s"] if k in sce.columns]
    print(sce[kol + ["pokrycie_okno_srednie_mean",
                     "pokrycie_koncowe_srednie_mean",
                     "udzial_blokow_90proc_w_oknie_mean",
                     "udzial_blokow_90proc_w_oknie_sd",
                     "blokow_mean", "orphan_blokow_mean",
                     "orphan_rate_mean"]].round(4).to_string(index=False))
    print("\nMapowanie na nazwy z polecenia promotorki:")
    print("  coverage@okno             -> pokrycie_okno_srednie")
    print("  final observed coverage   -> pokrycie_koncowe_srednie")
    print("  % blokow do >=90% wezlow  -> udzial_blokow_90proc_w_oknie")
    print("  unique blocks             -> blokow")
    print("  orphan blocks             -> orphan_blokow (orphan_rate = udzial)")


if __name__ == "__main__":
    main()
