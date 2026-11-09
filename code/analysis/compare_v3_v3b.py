#!/usr/bin/env python3
from pathlib import Path
import pandas as pd
ROOT = Path(__file__).resolve().parents[2]
v3 = pd.read_csv(ROOT/'data/solochain_repeat_v3/suma_wyniki_v3.csv')
v3b = pd.read_csv(ROOT/'data/solochain_v3b/suma_wyniki_v3b.csv')
keys=['algo','users','runtime']
m=v3.merge(v3b,on=keys,suffixes=('_v3','_v3b'))
m['throughput_abs_rel_diff_pct']=(m['tps_post_warmup_mean_v3b']-m['tps_post_warmup_mean_v3']).abs()/m['tps_post_warmup_mean_v3b'].abs()*100
m['inclusion_abs_diff_pp']=(m['inclusion_ratio_mean_v3b']-m['inclusion_ratio_mean_v3']).abs()*100
out=m[keys+['tps_post_warmup_mean_v3','tps_post_warmup_mean_v3b','throughput_abs_rel_diff_pct','inclusion_ratio_mean_v3','inclusion_ratio_mean_v3b','inclusion_abs_diff_pp']]
out.to_csv(ROOT/'derived/tables/v3_vs_v3b_reproducibility.csv', index=False)
print(f"max throughput relative difference = {out.throughput_abs_rel_diff_pct.max():.6f}%")
print(f"max inclusion difference = {out.inclusion_abs_diff_pp.max():.6f} pp")
