"""Paired inference from actual MuJoCo trials; no participant/workload inference."""
from pathlib import Path
import argparse,json
import numpy as np,pandas as pd
from scipy import stats
HERE=Path(__file__).resolve().parent

def bootstrap_mean_ci(delta,seed=2026):
    rng=np.random.default_rng(seed);a=np.asarray(delta,dtype=float)
    means=a[rng.integers(0,len(a),size=(20000,len(a)))].mean(axis=1)
    return np.quantile(means,[.025,.975]).tolist()

def analyze(folder):
    folder=Path(folder);df=pd.read_csv(folder/'results.csv')
    baseline=df[df.policy=='baseline'].set_index('seed').sort_index();shared=df[df.policy=='shared'].set_index('seed').sort_index()
    if not baseline.index.equals(shared.index):raise ValueError('Unmatched seeds')
    if len(df)!=2*len(shared):raise ValueError('Duplicate policy/seed')
    delta=shared.goal_error_m.values-baseline.goal_error_m.values
    n=len(delta);mean=float(np.mean(delta));sd=float(np.std(delta,ddof=1));se=sd/np.sqrt(n)
    t=stats.ttest_rel(shared.goal_error_m,baseline.goal_error_m)
    shapiro=stats.shapiro(delta)
    wilcoxon=stats.wilcoxon(delta,zero_method='pratt',alternative='two-sided',method='auto')
    b=int(((shared.accepted==True)&(baseline.accepted==False)).sum())
    c=int(((shared.accepted==False)&(baseline.accepted==True)).sum())
    primary=stats.binomtest(b,b+c,.5).pvalue if b+c else 1.
    summary={'N_pairs':n,'N_simulations':len(df),'primary_hypothesis':'Paired probability of accepted mission differs between policies',
        'primary_test':'Two-sided exact McNemar via discordant-pair binomial test',
        'shared_only_accepted':b,'baseline_only_accepted':c,'exact_McNemar_p':float(primary),
        'acceptance_difference_shared_minus_baseline':float(shared.accepted.mean()-baseline.accepted.mean()),
        'acceptance_difference_bootstrap_CI95':bootstrap_mean_ci(shared.accepted.astype(int).values-baseline.accepted.astype(int).values),
        'goal_error_difference_m':mean,'goal_error_difference_sd_m':sd,'goal_error_difference_bootstrap_CI95_m':bootstrap_mean_ci(delta),
        'exploratory_paired_t':{'df':n-1,'statistic':float(t.statistic),'p_value':float(t.pvalue),
            'cohen_dz':mean/sd if sd else None,'CI95_m':[mean-stats.t.ppf(.975,n-1)*se,mean+stats.t.ppf(.975,n-1)*se],
            'shapiro_W':float(shapiro.statistic),'shapiro_p':float(shapiro.pvalue),
            'interpretation':'Exploratory sensitivity analysis; mixed-scenario difference distribution may be non-normal. Primary inference is exact paired binary test.'},
        'exploratory_Wilcoxon':{'statistic':float(wilcoxon.statistic),'p_value':float(wilcoxon.pvalue),'method':'SciPy auto; two-sided Pratt zero handling'},
        'policies':{},'scenarios':{},'limitations':['Same deterministic ideal sensors and torque-limited M20 in both arms',
            'Baseline is a software driver, not human teleoperation; no NASA-TLX or SUS measured',
            'Latency buffer delays baseline remote velocity; local planner retains authority in shared arm',
            'Scenario mixture and seeded small fixtures do not represent real disaster fields',
            'No independent sensor-noise/localization-error or hardware validation']}
    for policy,g in df.groupby('policy'):
        metrics=['goal_error_m','path_length_m','simulated_s','max_abs_roll_deg','max_abs_pitch_deg','mean_slip_proxy','harmful_contact_steps','map_coverage','interventions']
        summary['policies'][policy]={'N':len(g),'accepted':int(g.accepted.sum()),'acceptance_rate':float(g.accepted.mean()),
            'rollovers':int(g.rollover.sum()),'harmful_contact_trials':int((g.harmful_contact_steps>0).sum()),
            **{k:{'mean':float(g[k].mean()),'sd':float(g[k].std(ddof=1))} for k in metrics}}
    for mode,g in df.groupby('mode'):
        summary['scenarios'][mode]={p:{'N':len(a),'accepted':int(a.accepted.sum()),'climb_verified':int(a.climb_verified.sum()),'statuses':a.status.value_counts().to_dict()} for p,a in g.groupby('policy')}
    (folder/'statistics.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    failures=df[~df.accepted][['trial_id','policy','mode','status','harmful_contact_steps','goal_error_m','rollover']]
    failures.to_csv(folder/'failure_cases.csv',index=False)
    lines=['# Measured paired M20 results','',f'{n} matched environments; {len(df)} actual MuJoCo simulations.','',
       '| Policy | Accepted | Harmful-contact trials | Rollovers |','|---|---:|---:|---:|']
    for p,r in summary['policies'].items():lines.append(f'| {p} | {r["accepted"]}/{r["N"]} | {r["harmful_contact_trials"]} | {r["rollovers"]} |')
    lines+=['',f'Exact paired McNemar p = {primary:.12g}; discordant counts shared-only {b}, baseline-only {c}.',
        f'Acceptance difference = {summary["acceptance_difference_shared_minus_baseline"]:.3f}; paired bootstrap 95% CI {summary["acceptance_difference_bootstrap_CI95"]}.',
        f'Goal-error difference (shared minus baseline) = {mean:.6f} ± {sd:.6f} m (SD); bootstrap 95% CI {summary["goal_error_difference_bootstrap_CI95_m"]}.',
        f'Exploratory paired t({n-1}) = {t.statistic:.6f}, p={t.pvalue:.12g}, Cohen d_z={mean/sd:.6f}. Shapiro p={shapiro.pvalue:.12g}; Wilcoxon p={wilcoxon.pvalue:.12g}.',
        '',*summary['limitations']]
    (folder/'RESULTS.md').write_text('\n'.join(lines),encoding='utf-8');print(json.dumps(summary,indent=2));return summary

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--folder',type=Path,default=HERE/'benchmark');a=p.parse_args();analyze(a.folder)
