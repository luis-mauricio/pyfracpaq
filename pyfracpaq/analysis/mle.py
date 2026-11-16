"""Length tail fitting and the original 2500 two-sample K-S comparisons.

Q-15 coherence contract: one percentage-selected sample for search and final
parameters; candidate-specific lognormal tails; complementary curves on both
sides of the fitting distance. No generic distribution .fit() is used.
"""

from collections.abc import Callable
from dataclasses import dataclass
import logging
from math import ceil

import numpy as np
from numpy.typing import ArrayLike, NDArray
from scipy.special import ndtr

from pyfracpaq.analysis.compatibility import readonly
from pyfracpaq.analysis.ks import ks_distance_sorted, ks_probability
from pyfracpaq.geometry.primitives import DEFAULT_MEMORY_LIMIT

MODELS = ('power_law', 'exponential', 'lognormal')
REPETITIONS = 2500
LOG = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class CutSample:
    original: NDArray[np.float64]
    retained: NDArray[np.float64]
    lower_count: int
    upper_count: int


def cut_sample(values: ArrayLike, lower: float = 0, upper: float = 0) -> CutSample:
    x = np.asarray(values, dtype=np.float64)
    if x.ndim != 1 or len(x) < 2 or not np.isfinite(x).all() or np.any(x <= 0):
        raise ValueError('MLE requires at least two finite positive lengths.')
    if not (np.isfinite(lower) and np.isfinite(upper) and lower >= 0 and upper >= 0
            and lower + upper < 100):
        raise ValueError('MLE cut-offs must be nonnegative and sum to less than 100%.')
    if len(x) * 256 > DEFAULT_MEMORY_LIMIT:
        raise MemoryError('MLE sample exceeds the 256 MiB working memory budget.')
    x = np.sort(x, kind='stable')
    low, high = ceil(len(x) * lower / 100), ceil(len(x) * upper / 100)
    kept = x[low:len(x) - high]
    if len(kept) < 2 or kept[0] == kept[-1]:
        raise ValueError('MLE needs at least two distinct retained lengths after cut-offs.')
    return CutSample(readonly(x), readonly(kept), low, high)


def _parameters(z: NDArray, kind: str, xmin: float, finite: bool = False) -> tuple:
    if kind == 'power_law':
        denominator = np.sum(np.log(z) - np.log(xmin))
        value = 1 + len(z) / denominator if denominator > 0 else float('inf')
        if finite:
            value = value * (len(z) - 1) / len(z) + 1 / len(z)
        parameters = (('alpha', float(value)),)
    elif kind == 'exponential':
        maximum = float(z[-1] - xmin)
        denominator = np.mean((z - xmin) / maximum) * maximum if maximum > 0 else 0.
        value = 1 / denominator if denominator > 0 else float('inf')
        parameters = (('lambda', float(value)),)
    else:
        logs = np.log(z)
        mu = float(np.mean(logs))
        sigma = float(np.sqrt(np.mean((logs - mu) ** 2)))
        parameters = (('mu', mu), ('sigma', sigma))
    if not all(np.isfinite(value) for _, value in parameters):
        raise ValueError('MLE parameters cannot be represented at this length scale.')
    if kind == 'lognormal' and parameters[1][1] <= 0:
        raise ValueError('Lognormal fitting requires positive log-length variance.')
    return parameters


def survival(values: ArrayLike, kind: str, xmin: float, parameters: tuple) -> NDArray:
    x = np.asarray(values, dtype=np.float64)
    p = dict(parameters)
    if kind == 'power_law':
        return np.exp((1 - p['alpha']) * (np.log(x) - np.log(xmin)))
    if kind == 'exponential':
        return np.exp(-p['lambda'] * (x - xmin))
    return ndtr(-(np.log(x) - p['mu']) / p['sigma'])


@dataclass(frozen=True, slots=True)
class TailFit:
    kind: str
    sample: CutSample
    xmin: float
    tail: NDArray[np.float64]
    parameters: tuple[tuple[str, float], ...]
    candidates: NDArray[np.float64]
    distances: NDArray[np.float64]
    search_distance: float
    distance: float
    finite_correction: bool


def fit_tail(values: ArrayLike, kind: str, *, lower: float = 0, upper: float = 0,
             finite: bool = False, progress: Callable[[int, str], None] = lambda *_: None,
             interrupted: Callable[[], bool] = lambda: False) -> TailFit:
    if kind not in MODELS:
        raise ValueError(f'Unknown MLE model: {kind}.')
    sample = cut_sample(values, lower, upper)
    x = sample.retained
    candidates, distances = [], []
    unique, starts = np.unique(x, return_index=True)
    for index, (xmin, start) in enumerate(zip(unique, starts)):
        if interrupted():
            raise InterruptedError('MLE cancelled.')
        z = x[start:]
        if len(z) < 2 or z[0] == z[-1]:
            continue
        try:
            parameters = _parameters(z, kind, float(xmin))
        except ValueError:
            continue
        empirical = np.arange(len(z), 0, -1, dtype=float) / len(z)
        distance = float(np.max(np.abs(survival(z, kind, xmin, parameters) - empirical)))
        if np.isfinite(distance):
            candidates.append(xmin)
            distances.append(distance)
        if index % max(1, len(unique) // 100) == 0:
            progress(round(100 * (index + 1) / len(unique)), f'MLE {kind}: searching xmin...')
    if not candidates:
        raise ValueError(f'No finite nondegenerate {kind} tail can be fitted.')
    best = int(np.argmin(distances))  # Stable: smallest xmin wins equal distances.
    xmin = float(candidates[best])
    z = readonly(x[x >= xmin])
    parameters = _parameters(z, kind, xmin, finite=finite and kind == 'power_law')
    distance = float(np.max(np.abs(survival(z, kind, xmin, parameters)
                                   - np.arange(len(z), 0, -1) / len(z))))
    return TailFit(kind, sample, xmin, z, parameters, readonly(candidates), readonly(distances),
                   distances[best], distance, bool(finite and kind == 'power_law'))


@dataclass(frozen=True, slots=True)
class GoodnessOfFit:
    distances: NDArray[np.float64]
    pvalues: NDArray[np.float64]
    rejected: NDArray[np.bool_]
    alpha: float
    non_rejection_percent: float
    above_005_percent: float
    method: str = 'two-sample, two-sided, MATLAB asymptotic (101 terms)'


def _standardized(fit: TailFit) -> NDArray:
    p = dict(fit.parameters)
    if fit.kind == 'power_law':
        return (np.log(fit.tail) - np.log(fit.xmin)) * (p['alpha'] - 1)
    if fit.kind == 'exponential':
        return (fit.tail - fit.xmin) * p['lambda']
    return (np.log(fit.tail) - p['mu']) / p['sigma']


def evaluate_fit(fit: TailFit, *, rng: np.random.Generator | None = None,
                 repetitions: int = REPETITIONS, draws: ArrayLike | None = None,
                 progress: Callable[[int, str], None] = lambda *_: None,
                 interrupted: Callable[[], bool] = lambda: False) -> GoodnessOfFit:
    """Synthetic draws are in standardized units: Exp(1) for PL/exp, N(0,1) for LN.

    Monotonic transforms preserve two-sample K-S while avoiding overflow of
    Pareto/lognormal lengths. Supplied shared draws bypass RNG for native checks.
    """
    if isinstance(repetitions, bool) or not isinstance(repetitions, int) or repetitions < 1:
        raise ValueError('Choose a positive integer number of K-S comparisons.')
    if repetitions * 64 > DEFAULT_MEMORY_LIMIT:
        raise MemoryError('K-S result vectors exceed the 256 MiB memory budget.')
    rng = np.random.default_rng() if rng is None else rng
    observed = np.sort(_standardized(fit))
    if not np.isfinite(observed).all():
        raise ValueError('Standardized MLE observations exceed float64 range.')
    shared = None if draws is None else np.asarray(draws, dtype=np.float64)
    if shared is not None and (shared.shape != (repetitions, len(observed))
                               or not np.isfinite(shared).all()):
        raise ValueError('Shared synthetic draws must match repetitions × tail size and be finite.')
    if shared is not None and fit.kind != 'lognormal' and np.any(shared < 0):
        raise ValueError('Standardized power-law/exponential draws must be nonnegative.')
    distances = np.empty(repetitions)
    for i in range(repetitions):
        if interrupted():
            raise InterruptedError('MLE K-S comparisons cancelled.')
        generated = (shared[i] if shared is not None else rng.standard_normal(len(observed))
                     if fit.kind == 'lognormal' else rng.exponential(size=len(observed)))
        distances[i] = ks_distance_sorted(observed, np.sort(generated))
        if (i + 1) % max(1, repetitions // 100) == 0 or i + 1 == repetitions:
            progress(round(100 * (i + 1) / repetitions),
                     f'MLE {fit.kind}: K-S comparison {i + 1}/{repetitions}')
    pvalues = ks_probability(distances, len(observed), len(observed))
    alpha = .1 if fit.kind == 'power_law' else .05
    rejected = np.array(pvalues <= alpha, dtype=bool)
    rejected.setflags(write=False)
    return GoodnessOfFit(readonly(distances), readonly(pvalues), rejected, alpha,
                          float(np.mean(~rejected) * 100), float(np.mean(pvalues > .05) * 100))


@dataclass(frozen=True, slots=True)
class ModelResult:
    fit: TailFit
    goodness: GoodnessOfFit


@dataclass(frozen=True, slots=True)
class MleResult:
    trace: tuple[ModelResult, ...]
    segment: tuple[ModelResult, ...]
    seed: int
    unit: str
    colour: tuple[float, float, float]


def fit_populations(traces: ArrayLike, segments: ArrayLike, *, lower: float = 0,
                     upper: float = 0, seed: int | None = None, unit: str = 'pixels',
                     colour: tuple = (0., 0., 1.),
                     progress: Callable[[int, str], None] = lambda *_: None,
                     interrupted: Callable[[], bool] = lambda: False) -> MleResult:
    # Validate both populations before expensive work or any family export.
    for values in (traces, segments):
        cut_sample(values, lower, upper)
    sequence = np.random.SeedSequence(seed)
    seed = int(sequence.entropy)
    streams = sequence.spawn(6)
    LOG.info('MLE RNG: PCG64; root seed=%s; 2500 comparisons per model.', seed)
    records = []
    for i, (population, values, kind) in enumerate(
            (p, x, k) for p, x in (('trace', traces), ('segment', segments)) for k in MODELS):
        fit = fit_tail(values, kind, lower=lower, upper=upper, interrupted=interrupted,
                       progress=lambda percent, message: progress(round((i * 100 + percent * .2) / 6), message))
        goodness = evaluate_fit(fit, rng=np.random.Generator(np.random.PCG64(streams[i])),
                                interrupted=interrupted,
                                progress=lambda percent, message: progress(round((i * 100 + 20 + percent * .8) / 6), message))
        LOG.info('MLE %s lengths, %s: xmin=%g; %s; n=%d; D=%g', population, kind,
                 fit.xmin, dict(fit.parameters), len(fit.tail), fit.distance)
        LOG.info('Two-sample K-S non-rejection rate (alpha=%g): %.2f%%; p>0.05 rate: %.2f%%.',
                 goodness.alpha, goodness.non_rejection_percent, goodness.above_005_percent)
        if len(fit.tail) < 8:
            LOG.warning('Small MLE tail (n=%d): asymptotic K-S percentages require caution.', len(fit.tail))
        records.append(ModelResult(fit, goodness))
    return MleResult(tuple(records[:3]), tuple(records[3:]), seed, unit, colour)
