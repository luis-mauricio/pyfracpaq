"""Analytic MLE parameters, source K-S constants and reproducible assessments."""

import json
from math import log,sqrt

import numpy as np
import pytest
from scipy.io import loadmat
from scipy.special import ndtri
from scipy.stats import ks_2samp

from pyfracpaq.analysis.ks import ks_two_sample,ks_probability
from pyfracpaq.analysis.mle import (
    MODELS,cut_sample,fit_tail,evaluate_fit,fit_populations,_standardized,
)
from reference_common import ROOT

NATIVE=ROOT/'tests/reference/sprint8/native_ks_hist.json'
SHARED=ROOT/'tests/reference/sprint8/shared_ks_inputs.mat'
OUTPUTS=ROOT/'tests/reference/sprint8/shared_ks_outputs.mat'


def test_cutoffs_have_field_direction_exact_counts_and_one_retained_sample():
    sample=cut_sample(np.arange(10,0,-1),20,10)
    assert sample.retained.tolist()==[3,4,5,6,7,8,9]
    assert (sample.lower_count,sample.upper_count)==(2,1)
    assert sample.original.tolist()==list(range(1,11))
    for model in MODELS:
        result=fit_tail(np.arange(1,11),model,lower=20,upper=10)
        assert result.sample.retained.tolist()==sample.retained.tolist()
        assert result.tail.min()>=3 and result.tail.max()<=9


@pytest.mark.parametrize('values,lower,upper',[
    ([0,1,2],0,0),([-1,1,2],0,0),([np.nan,1,2],0,0),([1],0,0),
    ([1,1,1],0,0),([1,2,3],40,40),([1,2,3],-1,0),([1,2,3],0,100),
])
def test_invalid_or_exhausted_samples_are_rejected(values,lower,upper):
    with pytest.raises(ValueError):cut_sample(values,lower,upper)


@pytest.mark.parametrize('kind',MODELS)
def test_four_geometric_lengths_have_known_mle_parameters(kind):
    fit=fit_tail([1,2,4,8],kind)
    assert fit.xmin==1
    p=dict(fit.parameters)
    expected={'power_law':{'alpha':1+4/(6*log(2))},
              'exponential':{'lambda':4/11},
              'lognormal':{'mu':1.5*log(2),'sigma':sqrt(1.25)*log(2)}}[kind]
    for name,value in expected.items():assert p[name]==pytest.approx(value,rel=1e-8,abs=1e-12)
    assert fit.distance==pytest.approx(fit.distances.min())
    assert all(not a.flags.writeable for a in (fit.tail,fit.candidates,fit.distances,fit.sample.retained))


def test_finite_power_law_correction_is_optional_and_keeps_threshold_search():
    regular=fit_tail([1,2,4,8],'power_law')
    finite=fit_tail([1,2,4,8],'power_law',finite=True)
    assert finite.xmin==regular.xmin
    assert dict(finite.parameters)['alpha']==pytest.approx(1+3/(6*log(2)))
    np.testing.assert_array_equal(finite.distances,regular.distances)


def test_repeated_lengths_are_retained_by_fitting_and_assessment():
    fit=fit_tail([1,1,2,2,4,8],'power_law')
    assert fit.tail.tolist()==[1,1,2,2,4,8]
    assert dict(fit.parameters)['alpha']==pytest.approx(1+6/(7*log(2)))


@pytest.mark.parametrize('kind',MODELS)
def test_scaling_changes_dimensional_parameters_only(kind):
    first=fit_tail([1,2,4,8],kind);second=fit_tail(np.array([1,2,4,8])/2,kind)
    assert second.xmin==first.xmin/2
    p,q=dict(first.parameters),dict(second.parameters)
    if kind=='power_law':assert q['alpha']==pytest.approx(p['alpha'])
    elif kind=='exponential':assert q['lambda']==pytest.approx(p['lambda']*2)
    else:
        assert q['mu']==pytest.approx(p['mu']-log(2))
        assert q['sigma']==pytest.approx(p['sigma'])
    assert second.distance==pytest.approx(first.distance,abs=1e-12)


def test_ks_distance_with_ties_and_native_asymptotic_probability():
    native=json.loads(NATIVE.read_text())
    got=ks_two_sample(native['first'],native['second'])
    assert got.distance==pytest.approx(native['distance'],abs=1e-12)
    assert got.pvalue==pytest.approx(native['p'],rel=1e-8,abs=1e-12)
    assert got.reject==native['h05']
    assert ks_two_sample([1,1,2],[1,1,2]).pvalue==1
    for a,b in [([1,1,2,3],[0,1,4,5]),([1,2],[5,6]),([1,2,3],[2,3,4])]:
        assert ks_two_sample(a,b).distance==pytest.approx(ks_2samp(a,b,method='asymp').statistic)


def test_native_significance_thresholds_distinguish_power_law_and_other_models():
    native = json.loads((ROOT / 'tests/reference/sprint8/native/ks_threshold.json').read_text())
    for alpha, key in ((.05, 'h05'), (.1, 'h10')):
        result = ks_two_sample(native['first'], native['second'], alpha=alpha)
        assert result.distance == pytest.approx(native['D'], abs=1e-12)
        assert result.pvalue == pytest.approx(native['p'], abs=1e-12)
        assert result.reject == native[key]
    assert native['h05'] != native['h10']


@pytest.mark.parametrize('kind', MODELS)
def test_native_uncut_reference_has_same_fitted_parameters(kind):
    native = json.loads((ROOT / 'tests/reference/sprint8/native/native_fits.json').read_text())
    result = fit_tail(native['input'], kind)
    expected = native['cuts0'][kind]
    assert result.xmin == pytest.approx(expected['xmin'], rel=1e-8, abs=1e-12)
    for name, value in result.parameters:
        assert value == pytest.approx(expected[name], rel=1e-8, abs=1e-12)


@pytest.mark.parametrize('kind',MODELS)
def test_all_2500_ks_results_match_matlab_on_identical_shared_vectors(kind):
    inputs=loadmat(SHARED,simplify_cells=True)
    outputs=loadmat(OUTPUTS,simplify_cells=True)['ks'][kind]
    fit=fit_tail(inputs['sample'],kind)
    result=evaluate_fit(fit,draws=inputs[kind+'_draws'])
    np.testing.assert_allclose(result.distances,outputs['D'],rtol=1e-8,atol=1e-12)
    np.testing.assert_allclose(result.pvalues,outputs['p'],rtol=1e-8,atol=1e-12)
    np.testing.assert_array_equal(result.rejected,np.asarray(outputs['h'],dtype=bool))
    assert result.alpha==outputs['alpha']


@pytest.mark.parametrize('kind', MODELS)
def test_known_synthetic_distribution_quantiles_recover_parameters(kind):
    # Midpoint quantiles give deterministic populations without sampling noise.
    probabilities = (np.arange(512) + .5) / 512
    values = {
        'power_law': 2 * (1 - probabilities) ** (-1 / 1.5),
        'exponential': 2 - np.log1p(-probabilities) / .4,
        'lognormal': np.exp(1.2 + .7 * ndtri(probabilities)),
    }[kind]
    fit = fit_tail(values, kind)
    expected = {'power_law': {'alpha': 2.5}, 'exponential': {'lambda': .4},
                'lognormal': {'mu': 1.2, 'sigma': .7}}[kind]
    assert len(fit.tail) == 512
    for name, value in expected.items():
        assert dict(fit.parameters)[name] == pytest.approx(value, rel=.003)
    assert fit.distance < .002


def test_rng_is_local_reproducible_and_2500_comparisons_are_preserved():
    np.random.seed(93);before=np.random.get_state()
    x=[1,2,3,4,6,10,18,40]
    a=fit_populations(x,x,seed=71);b=fit_populations(x,x,seed=71)
    after=np.random.get_state()
    np.testing.assert_array_equal(before[1],after[1])
    assert before[2:]==after[2:]
    for one,two in zip(a.trace+a.segment,b.trace+b.segment):
        assert len(one.goodness.pvalues)==2500
        np.testing.assert_array_equal(one.goodness.pvalues,two.goodness.pvalues)
        assert one.goodness.non_rejection_percent==pytest.approx(np.mean(~one.goodness.rejected)*100)
        expected=.1 if one.fit.kind=='power_law' else .05
        assert one.goodness.alpha==expected
    assert a.seed==b.seed==71
    assert not a.trace[0].goodness.pvalues.flags.writeable


def test_ks_search_and_monte_carlo_are_cooperatively_interruptible():
    with pytest.raises(InterruptedError):fit_tail([1,2,4],'power_law',interrupted=lambda:True)
    fit=fit_tail([1,2,4],'power_law')
    with pytest.raises(InterruptedError):evaluate_fit(fit,interrupted=lambda:True)


def test_independent_monte_carlo_streams_have_documented_sampling_variation():
    fit=fit_tail(np.exp(np.linspace(0,3,30)),'lognormal')
    rates=[]
    for seed in range(20):
        result=evaluate_fit(fit,rng=np.random.default_rng(seed),repetitions=2500)
        rates.append(result.non_rejection_percent)
    assert len(set(rates))>1
    # Distribution-free concentration check around their pooled binomial rate.
    mean=np.mean(rates)/100
    error=6*sqrt(max(mean*(1-mean),1/2500)/2500)*100
    assert max(abs(np.asarray(rates)-np.mean(rates)))<error
