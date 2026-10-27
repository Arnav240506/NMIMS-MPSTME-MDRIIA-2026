"""Scenario capacity driven by real trial time/acceptance; no field savings claim."""
from pathlib import Path
import json
import pandas as pd
from hazardous_recon_economics import queue_model
HERE=Path(__file__).resolve().parent

def capacity(mean_attempt_seconds,acceptance_fraction,overhead_hours=3.,work_hours_week=40.):
    if mean_attempt_seconds<=0 or not 0<=acceptance_fraction<=1 or overhead_hours<0 or work_hours_week<=0:
        raise ValueError('Invalid capacity inputs')
    return work_hours_week*acceptance_fraction/(overhead_hours+mean_attempt_seconds/3600)

def main():
    df=pd.read_csv(HERE/'capstone_500hz/capstone_real_trials.csv')
    result={'interpretation':'Sensitivity scenario only: each job attempt includes measured simulated route time plus assumed inspection/reset overhead. Acceptance fraction is empirical simulation frequency, not field reliability. Constant independent repeated-attempt assumption; M/M/1 arrival/service distribution is an approximation.',
        'assumptions':{'overhead_hours_per_attempt':[1.5,3.,4.5],'work_hours_per_week':40.,'arrival_requests_per_week':8.},'policies':{}}
    for policy,g in df.groupby('policy'):
        rate=float(g.accepted.mean());seconds=float(g.simulated_s.mean());cases=[]
        for h in [1.5,3.,4.5]:
            mu=capacity(seconds,rate,h)
            cases.append({'overhead_hours':h,'effective_success_capacity_per_week':mu,'queue':queue_model(8.,mu) if mu>0 else {'stable':False,'Wq_work_hours':None,'reason':'No accepted service in this sample'}})
        result['policies'][policy]={'actual_trials':len(g),'measured_mean_attempt_seconds':seconds,'measured_acceptance_fraction':rate,'scenarios':cases}
    (HERE/'telemetry_business_bridge.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()
