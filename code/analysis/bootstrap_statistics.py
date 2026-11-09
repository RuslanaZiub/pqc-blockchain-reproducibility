#!/usr/bin/env python3
"""Reproduce paired SimBlock sensitivity statistics from run-level CSV files.

Primary FULL/ZERO: cluster bootstrap at the seed level, retaining all five N values.
CBR: paired by seed against the matching primary FULL run (N=2000, 2000 tx).

The RNG seed is fixed to make the Monte-Carlo interval exactly reproducible for this archive.
"""
from pathlib import Path
import argparse
import numpy as np
import pandas as pd

ALG_ORDER = ["ecdsa", "dilithium", "sphincs"]
TX_ORDER = [500,1000,1500,2000]

def percentile_ci(values, rng, reps=10000):
    values=np.asarray(values,float)
    idx=rng.integers(0,len(values),size=(reps,len(values)))
    b=values[idx].mean(axis=1)
    return np.quantile(b,[0.025,0.975])

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--root',default=str(Path(__file__).resolve().parents[2]))
    ap.add_argument('--seed',type=int,default=20261109)
    ap.add_argument('--reps',type=int,default=10000)
    args=ap.parse_args()
    root=Path(args.root)
    p=pd.read_csv(root/'data/simblock_primary/run_coverage6s.csv')
    c=pd.read_csv(root/'data/simblock_cbr/run_coverage.csv')
    rng=np.random.default_rng(args.seed)
    out=[]
    for alg in ALG_ORDER:
        for tx in TX_ORDER:
            x=p[(p.algorithm==alg)&(p.tx_count==tx)]
            f=x[x['mode']=='full']
            z=x[x['mode']=='zero_verify']
            m=f.merge(z,on=['algorithm','tx_count','nodes','seed'],suffixes=('_full','_zero'))
            m['diff_pp']=100*(m.pokrycie6s_srednie_zero-m.pokrycie6s_srednie_full)
            by_seed=m.groupby('seed',sort=True)['diff_pp'].mean().to_numpy()
            lo,hi=percentile_ci(by_seed,rng,args.reps)
            out.append(dict(comparison='ZERO-FULL',algorithm=alg,tx_count=tx,nodes='all_5',mean_diff_pp=by_seed.mean(),ci_low_pp=lo,ci_high_pp=hi,n_seeds=len(by_seed)))
    # CBR paired by seed to primary FULL at N=2000, tx=2000
    base=p[(p['mode']=='full')&(p.nodes==2000)&(p.tx_count==2000)]
    for alg in ALG_ORDER:
        b=base[base.algorithm==alg][['algorithm','seed','pokrycie6s_srednie']]
        cc=c[c.algorithm==alg][['algorithm','seed','pokrycie_okno_srednie']]
        m=b.merge(cc,on=['algorithm','seed'])
        vals=100*(m.pokrycie_okno_srednie-m.pokrycie6s_srednie)
        lo,hi=percentile_ci(vals.to_numpy(),rng,args.reps)
        out.append(dict(comparison='CBR1-CBR0',algorithm=alg,tx_count=2000,nodes=2000,mean_diff_pp=vals.mean(),ci_low_pp=lo,ci_high_pp=hi,n_seeds=len(vals)))
    out=pd.DataFrame(out)
    dst=root/'derived/tables/bootstrap_sensitivity_statistics.csv'
    dst.parent.mkdir(parents=True,exist_ok=True)
    out.to_csv(dst,index=False)
    print(out.to_string(index=False,float_format=lambda x:f'{x:.6f}'))
    print(f'\nWrote {dst}')

if __name__=='__main__': main()
