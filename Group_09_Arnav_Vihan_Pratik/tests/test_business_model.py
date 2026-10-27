import pytest
from hazardous_recon_economics import economics,queue_model

def test_normalized_payback_and_scale_invariance():
    e=economics();assert e['P_payback']==pytest.approx(.30/(5*.78))
    scaled=economics(.44,2.,.60)
    assert scaled['payback_months']==pytest.approx(e['payback_months'])
    assert scaled['NCRI']==e['NCRI'] and scaled['P_payback']==e['P_payback']
    assert economics(lifetime_years=10)['P_payback']==pytest.approx(e['P_payback']/2)

def test_nonpaying_case_and_zero_capital():
    assert economics(1.)['P_payback'] is None
    assert economics(1.2)['NCRI']<0
    assert economics(capex_parity=0.)['payback_months']==0.
    with pytest.raises(ValueError):economics(lifetime_years=0)

def test_mm1_closed_form_and_little_law():
    q=queue_model(8.,12.)
    assert q['Wq_weeks']==pytest.approx(8/(12*(12-8)))
    assert q['W_weeks']==pytest.approx(1/(12-8))
    assert q['Wq_work_hours']==pytest.approx(40/6)
    assert q['Lq']==pytest.approx(q['arrival_per_week']*q['Wq_weeks'])
    assert q['L']==pytest.approx(q['arrival_per_week']*q['W_weeks'])

def test_mmc_known_case_zero_arrivals_and_overload():
    # lambda=2, mu=2, c=2 => Erlang C=1/3, Wq=1/6 in the rate unit.
    q=queue_model(2,2,2)
    assert q['probability_wait']==pytest.approx(1/3) and q['Wq_weeks']==pytest.approx(1/6)
    assert queue_model(0)['Wq_weeks']==0
    assert queue_model(12)['Wq_weeks'] is None and not queue_model(12)['stable']
    assert queue_model(8,12,2)['Wq_weeks']<queue_model(8,12,1)['Wq_weeks']
    for kwargs in [{'servers':0},{'servers':1.5},{'arrival_per_week':-1},{'service_per_server_week':0}]:
        with pytest.raises(ValueError):queue_model(**kwargs)
from telemetry_business_bridge import capacity

def test_telemetry_capacity_units_and_failed_service():
    assert capacity(3600,1,3,40)==10
    assert capacity(3600,.5,3,40)==5
    assert capacity(3600,0,3,40)==0

