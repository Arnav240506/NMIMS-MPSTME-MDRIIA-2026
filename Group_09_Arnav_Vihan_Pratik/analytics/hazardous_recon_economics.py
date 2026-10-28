"""Illustrative dimensionless economics; no field-calibrated savings claims."""
import json
import math
from pathlib import Path

def economics(operating_parity=.22,reclaimed_value_parity=1.,capex_parity=.30,reclaimed_hours=312.,lifetime_years=5.,annual_work_hours=2080.):
    values=[operating_parity,reclaimed_value_parity,capex_parity,reclaimed_hours,lifetime_years,annual_work_hours]
    if not all(math.isfinite(x) for x in values):raise ValueError('Inputs must be finite')
    if operating_parity<0 or reclaimed_value_parity<=0 or capex_parity<0 or reclaimed_hours<0 or lifetime_years<=0 or annual_work_hours<=0:
        raise ValueError('Invalid nonnegative parity or nonpositive denominator')
    kappa=operating_parity/reclaimed_value_parity
    net=reclaimed_value_parity-operating_parity
    years=capex_parity/net if net>0 else None
    return dict(kappa=kappa,NCRI=1-kappa,capex_parity=capex_parity,
                net_annual_savings_parity=net,lifetime_years=lifetime_years,
                payback_months=12*years if years is not None else None,
                P_payback=years/lifetime_years if years is not None else None,
                pays_back_within_life=years is not None and years<lifetime_years,
                H_reclaimed_hours_per_year=reclaimed_hours,annual_work_hours=annual_work_hours,
                delta_FTE=reclaimed_hours/annual_work_hours,
                assumption_status='Illustrative uncalibrated assumptions; not observed savings')

def queue_model(arrival_per_week=8.,service_per_server_week=12.,servers=1,working_hours_per_week=40.):
    """Erlang C M/M/c; rates share a week unit, delays are in weeks and work hours.

    Poisson arrivals, exponential service, independent parallel servers, FCFS,
    infinite buffer and steady state are scenario assumptions, not observations.
    """
    if isinstance(servers,bool) or not isinstance(servers,int) or servers<1 or servers>100:raise ValueError('servers must be an integer in 1..100')
    if not all(math.isfinite(x) for x in [arrival_per_week,service_per_server_week,working_hours_per_week]):raise ValueError('Rates must be finite')
    if arrival_per_week<0 or service_per_server_week<=0 or working_hours_per_week<=0:raise ValueError('Invalid queue rate or work week')
    load=arrival_per_week/service_per_server_week;rho=load/servers
    base=dict(model=f'M/M/{servers}',arrival_per_week=arrival_per_week,service_per_server_week=service_per_server_week,
              servers=servers,rho=rho,stable=rho<1,working_hours_per_week=working_hours_per_week,
              assumption_status='Assumed request rates and exponential service; no measured arrival/service dataset')
    if rho>=1:return dict(base,probability_wait=None,Wq_weeks=None,W_weeks=None,Wq_work_hours=None,Lq=None,L=None)
    # Recurrence avoids large factorials; c=1 reduces to lambda/(mu*(mu-lambda)).
    term=1.;partial=1.
    for k in range(1,servers):term*=load/k;partial+=term
    tail=term*load/servers/(1-rho)
    wait_probability=tail/(partial+tail)
    wq=wait_probability/(servers*service_per_server_week-arrival_per_week)
    w=wq+1/service_per_server_week
    return dict(base,probability_wait=wait_probability,Wq_weeks=wq,W_weeks=w,
                Wq_work_hours=wq*working_hours_per_week,Lq=arrival_per_week*wq,L=arrival_per_week*w)

def main():
    result={'base_case':economics(),'queue_base_case':queue_model(),
            'input_provenance':'All business rates, capital/operating parities, lifetime and labor hours are explicit planning assumptions; actual MuJoCo results do not establish observed business savings.',
            'sensitivity':[economics(k) for k in [.12,.22,.45,.8,1.,1.2]],
            'queue_sensitivity':[queue_model(lam) for lam in [0.,3.,6.,8.,9.,10.8,11.4,12.,13.]],
            'labor_sensitivity':[economics(reclaimed_hours=h) for h in [218.4,312.,405.6]]}
    out=Path(__file__).resolve().parent/'economics_results.json'
    out.write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
