"""Verify 500 Hz evidence and analyze the predeclared independent experiment."""
from pathlib import Path
import argparse,json,hashlib
import numpy as np,pandas as pd
from scipy import stats

def comparison(proposed,baseline):
    a=np.asarray(proposed,float);b=np.asarray(baseline,float)
    if not np.isfinite(a).all() or not np.isfinite(b).all():raise ValueError('Missing metric; do not drop failed trials')
    na,nb=len(a),len(b);va,vb=a.var(ddof=1),b.var(ddof=1)
    result=stats.ttest_ind(a,b,equal_var=False)
    difference=float(a.mean()-b.mean());se=np.sqrt(va/na+vb/nb)
    df=(va/na+vb/nb)**2/((va/na)**2/(na-1)+(vb/nb)**2/(nb-1))
    pooled=np.sqrt(((na-1)*va+(nb-1)*vb)/(na+nb-2))
    half=stats.t.ppf(.975,df)*se
    return {'N_proposed':na,'N_baseline':nb,'difference_proposed_minus_baseline':difference,
            't':float(result.statistic),'df':float(df),'p_two_sided':float(result.pvalue),
            'cohen_d_pooled':float(difference/pooled),'pooled_SD':float(pooled),
            'CI95':[float(difference-half),float(difference+half)],
            'baseline_mean':float(b.mean()),'baseline_SD':float(b.std(ddof=1)),
            'proposed_mean':float(a.mean()),'proposed_SD':float(a.std(ddof=1)),
            'mann_whitney_p_sensitivity':float(stats.mannwhitneyu(a,b,alternative='two-sided',method='asymptotic').pvalue)}

def verify(folder):
    design=json.loads((folder/'design.json').read_text());summaries=json.loads((folder/'summaries.json').read_text())
    assert len(summaries)==60 and design['N_per_policy']==30
    rows=[];total_samples=0;csv_count=0
    for summary in summaries:
        trial=folder/summary['trial_id'];schema=json.loads((trial/'telemetry_schema.json').read_text())
        assert summary['source_sha256']==design['source_sha256']
        previous=0.;n=valid=harm=0;effort=sq=0.;last=None
        for f in schema['files']:
            path=trial/f['path'];assert hashlib.sha256(path.read_bytes()).hexdigest()==f['sha256']
            data=pd.read_csv(path);csv_count+=1
            assert len(data)<=20000 and len(data)>0
            assert data.run_id.eq(summary['trial_id']).all() and data.seed.eq(summary['config']['seed']).all()
            times=data.time_s.to_numpy();assert np.allclose(np.diff(np.r_[previous,times]),.002,atol=1e-10,rtol=0)
            assert np.allclose(data.dt_s,.002,rtol=0,atol=1e-12);previous=float(times[-1])
            tau=data[[f'tau_{i:02d}_Nm' for i in range(16)]].to_numpy();assert np.isfinite(tau).all()
            effort+=float(np.sum(tau*tau)*.002)
            mask=data.tracking_valid.eq(1)
            assert np.isfinite(data[['reference_x_m','reference_y_m','error_x_m','error_y_m']]).all().all()
            assert np.allclose(data.x_m-data.reference_x_m,data.error_x_m,atol=2e-7)
            assert np.allclose(data.y_m-data.reference_y_m,data.error_y_m,atol=2e-7)
            sq+=float((data.loc[mask,'error_x_m']**2+data.loc[mask,'error_y_m']**2).sum());valid+=int(mask.sum())
            harm+=int(data.harmful_contact_step.sum());n+=len(data);last=data.iloc[-1]
        assert n==schema['samples']==summary['telemetry_samples'] and abs(previous-summary['simulated_s'])<1e-6
        assert np.isclose(effort,summary['control_effort_Nm2_s'],rtol=1e-8)
        assert np.isclose(np.sqrt(sq/valid),summary['tracking_rmse_m'],rtol=1e-7,atol=1e-9)
        assert harm==summary['harmful_contact_steps']
        assert np.isclose(np.linalg.norm(np.array([last.x_m,last.y_m])-summary['terrain']['goal']),summary['goal_error_m'],atol=1e-6)
        if summary['accepted']:
            assert harm==0 and summary['goal_reached'] and len(summary['climb_records'])==2
            assert all(c[k] for c in summary['climb_records'] for k in ['front_pair_air','rear_pair_air','front_resupport','rear_resupport'])
        total_samples+=n
        rows.append({'trial_id':summary['trial_id'],'samples':n,'CSV_parts':len(schema['files']),'recomputed_effort':effort,'recomputed_RMSE':float(np.sqrt(sq/valid))})
    receipt={'status':'PASS','actual_trials_checked':60,'sample_rate_hz':500,'total_actual_samples':total_samples,'CSV_parts':csv_count,
             'source_sha256':design['source_sha256'],'checks':['CSV SHA256','continuous 2 ms sampling','all 16 torque channels','effort recomputed','RMSE recomputed','contact counts','terminal goal error','both pair-lift ascent gates'],'trials':rows}
    (folder/'verification.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
    return receipt

def main():
    p=argparse.ArgumentParser();p.add_argument('--folder',type=Path,default=Path(__file__).resolve().parent/'capstone_500hz');a=p.parse_args()
    receipt=verify(a.folder);df=pd.read_csv(a.folder/'capstone_real_trials.csv')
    assert set(df.policy)=={'baseline','shared'} and (df.groupby('policy').size()==30).all()
    b=df[df.policy=='baseline'];s=df[df.policy=='shared'];assert set(b.seed).isdisjoint(set(s.seed))
    metrics=['goal_error_m','tracking_rmse_m','control_effort_Nm2_s','simulated_s','path_length_m','max_abs_roll_deg','max_abs_pitch_deg']
    result={'source_sha256':receipt['source_sha256'],'N_per_policy':30,'N_total':60,'design':'Independent seeds; ten runs in each of three roughness strata per policy',
        'primary_metric':'goal_error_m','primary_hypothesis':'The mean terminal XY goal error differs between the two policies',
        'primary_test':'Two-sided independent Welch t test at alpha 0.05',
        'comparisons':{m:comparison(s[m],b[m]) for m in metrics},'policies':{},'roughness_strata':{},
        'limitations':['Software-driver baseline, not a human operator','Integrated map-and-transfer policy; cannot attribute improvement to one feature','Fixed evaluator-only reference measures geometric cross-track error, not timed trajectory tracking','Unequal failure rates and durations affect RMSE and total effort; lower effort alone is not efficiency','Rigid idealized simulated yard, exact pose, ideal rays; no hardware or human workload validation','N=30 per policy and 10 per roughness stratum; extensions are not pooled with historical studies']}
    for name,g in df.groupby('policy'):
        result['policies'][name]={'N':len(g),'accepted':int(g.accepted.sum()),'harmful_contact_trials':int((g.harmful_contact_steps>0).sum()),'rollovers':int(g.rollover.sum()),'status_counts':g.status.value_counts().to_dict(),
            'mean_goal_error_m':float(g.goal_error_m.mean()),'mean_tracking_rmse_m':float(g.tracking_rmse_m.mean()),'mean_control_effort_Nm2_s':float(g.control_effort_Nm2_s.mean())}
    for rough,g in df.groupby('roughness_m'):result['roughness_strata'][str(rough)]={p:{'N':len(x),'accepted':int(x.accepted.sum())} for p,x in g.groupby('policy')}
    result['acceptance_Fisher_exact_p']=float(stats.fisher_exact([[int(s.accepted.sum()),30-int(s.accepted.sum())],[int(b.accepted.sum()),30-int(b.accepted.sum())]]).pvalue)
    (a.folder/'statistics.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    df[~df.accepted].to_csv(a.folder/'failure_cases.csv',index=False)
    print(json.dumps({'verification':{k:v for k,v in receipt.items() if k!='trials'},'primary':result['comparisons']['goal_error_m'],'policies':result['policies']},indent=2))

if __name__=='__main__':main()
