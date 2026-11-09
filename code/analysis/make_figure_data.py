#!/usr/bin/env python3
"""Create compact numerical inputs for manuscript network figures/tables."""
from pathlib import Path
import pandas as pd

def main():
    root=Path(__file__).resolve().parents[2]
    p=pd.read_csv(root/'data/simblock_primary/run_coverage6s.csv')
    # Fig. 3: mean across five network sizes and ten seeds, by scheme/load/mode.
    fig3=(p.groupby(['algorithm','tx_count','mode'],as_index=False)
          .agg(coverage_within_6s=('pokrycie6s_srednie','mean'),
               final_observed_coverage=('pokrycie_koncowe_srednie','mean')))
    for col in ['coverage_within_6s','final_observed_coverage']:
        fig3[col]=100*fig3[col]
    fig3.to_csv(root/'derived/figure_data/fig3_primary_propagation.csv',index=False)

    stable=pd.read_csv(root/'data/simblock_stable_full/scenario_coverage.csv')
    cbr=pd.read_csv(root/'data/simblock_cbr/scenario_coverage.csv')
    # Primary CBR=0 matching rows, aggregated over seeds for N=2000, tx=2000.
    base=(p[(p['mode']=='full')&(p.nodes==2000)&(p.tx_count==2000)]
          .groupby('algorithm',as_index=False)
          .agg(cbr0_coverage=('pokrycie6s_srednie','mean')))
    base['cbr0_coverage']*=100
    # scenario files already contain one row per algorithm for these experiments.
    # Keep original columns plus a compact harmonized table.
    s=stable.copy(); c=cbr.copy()
    # Identify canonical columns robustly.
    stab=s[['algorithm','pokrycie_okno_srednie_mean','pokrycie_koncowe_srednie_mean','udzial_blokow_90proc_w_oknie_mean','orphan_rate_mean']].copy()
    stab.columns=['algorithm','stable120_coverage','stable120_final_observed','stable120_blocks_ge90','stable120_orphan_rate']
    for col in stab.columns[1:]: stab[col]*=100
    cb=c[['algorithm','pokrycie_okno_srednie_mean','pokrycie_koncowe_srednie_mean','udzial_blokow_90proc_w_oknie_mean']].copy()
    cb.columns=['algorithm','cbr1_coverage','cbr1_final_observed','cbr1_blocks_ge90']
    for col in cb.columns[1:]: cb[col]*=100
    sens=stab.merge(base,on='algorithm').merge(cb,on='algorithm')
    sens.to_csv(root/'derived/figure_data/network_sensitivity_summary.csv',index=False)
    print('Wrote figure_data CSV files.')

if __name__=='__main__': main()
