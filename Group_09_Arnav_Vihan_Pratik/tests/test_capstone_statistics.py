import numpy as np
from analyze_capstone import comparison

def test_welch_known_shift_equal_sample_variances():
    baseline=np.array([1.,2.,3.,4.,5.])
    proposed=baseline+2
    r=comparison(proposed,baseline)
    assert np.isclose(r['difference_proposed_minus_baseline'],2)
    assert np.isclose(r['t'],2)
    assert np.isclose(r['df'],8)
    assert np.isclose(r['cohen_d_pooled'],2/np.sqrt(2.5))
    assert np.allclose(r['CI95'],[-.3060041352,4.3060041352])
    reverse=comparison(baseline,proposed)
    assert np.isclose(reverse['p_two_sided'],r['p_two_sided'])
    assert np.allclose(reverse['CI95'],-np.array(r['CI95'])[::-1])
