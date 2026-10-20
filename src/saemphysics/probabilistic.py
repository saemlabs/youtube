"""Explicit probability distributions for uncertain candidate states."""

from collections.abc import Mapping
from dataclasses import dataclass
import math
import random


def _is_finite_number(value: object) -> bool:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    try:
        return math.isfinite(value)
    except OverflowError:
        return False


@dataclass(frozen=True)
class ProbabilityDistribution:
    probabilities: tuple[tuple[str, float], ...]

    def __post_init__(self):
        if not self.probabilities:
            raise ValueError("at least one state is required")
        states = tuple(state for state, _ in self.probabilities)
        values = tuple(probability for _, probability in self.probabilities)
        if any(not isinstance(state, str) or not state for state in states):
            raise ValueError("state identifiers must be non-empty strings")
        if len(states) != len(set(states)):
            raise ValueError("state identifiers must be unique")
        if any(
            not _is_finite_number(probability)
            or probability < 0
            for probability in values
        ):
            raise ValueError("probabilities must be finite non-negative numbers")
        if not math.isclose(math.fsum(values), 1.0, rel_tol=1e-12, abs_tol=1e-12):
            raise ValueError("probabilities must sum to one")

    @property
    def entropy_nats(self) -> float:
        return -math.fsum(
            probability * math.log(probability)
            for _, probability in self.probabilities
            if probability > 0
        )

    def sample(self, seed: int) -> str:
        if isinstance(seed, bool) or not isinstance(seed, int):
            raise ValueError("seed must be an integer")
        states, weights = zip(*self.probabilities, strict=True)
        return random.Random(seed).choices(states, weights=weights, k=1)[0]

    def probability_of(self, state: str) -> float:
        for candidate, probability in self.probabilities:
            if candidate == state:
                return probability
        raise KeyError(state)


def _normalized_distribution(weights: Mapping[str, float]) -> ProbabilityDistribution:
    if not weights:
        raise ValueError("at least one state is required")
    states = tuple(weights)
    if any(not isinstance(state, str) or not state for state in states):
        raise ValueError("state identifiers must be non-empty strings")
    if len(states) != len(set(states)):
        raise ValueError("state identifiers must be unique")
    values = tuple(weights[state] for state in states)
    if any(
        not _is_finite_number(value)
        or value < 0
        for value in values
    ):
        raise ValueError("weights must be finite non-negative numbers")
    maximum = max(values)
    if maximum <= 0:
        raise ValueError("at least one weight must be positive")
    scaled_values = tuple(value / maximum for value in values)
    total = math.fsum(scaled_values)
    return ProbabilityDistribution(
        probabilities=tuple(
            (state, value / total)
            for state, value in zip(states, scaled_values, strict=True)
        )
    )


def boltzmann_distribution(
    energies: Mapping[str, float],
    temperature: float,
) -> ProbabilityDistribution:
    """Convert dimensionless energies to a stable Gibbs/Boltzmann distribution."""
    if (
        not _is_finite_number(temperature)
        or temperature <= 0
    ):
        raise ValueError("temperature must be a finite positive number")
    if not energies:
        raise ValueError("at least one state is required")
    values = tuple(energies.values())
    if any(
        not _is_finite_number(energy)
        for energy in values
    ):
        raise ValueError("energies must be finite numbers")

    minimum = min(values)
    weights = {
        state: math.exp(-(energy - minimum) / temperature)
        for state, energy in energies.items()
    }
    return _normalized_distribution(weights)


def update_belief(
    prior: ProbabilityDistribution,
    likelihoods: Mapping[str, float],
) -> ProbabilityDistribution:
    """Apply explicit likelihoods to a prior distribution using Bayes' rule."""
    states = tuple(state for state, _ in prior.probabilities)
    if set(likelihoods) != set(states):
        raise ValueError("likelihoods must name exactly the states in the prior")
    if any(
        not _is_finite_number(likelihood)
        or likelihood < 0
        for likelihood in likelihoods.values()
    ):
        raise ValueError("likelihoods must be finite non-negative numbers")
    prior_weights = dict(prior.probabilities)
    posterior_weights = {
        state: prior_weights[state] * likelihoods[state] for state in states
    }
    return _normalized_distribution(posterior_weights)


def sample_boltzmann_state(
    energies: Mapping[str, float],
    temperature: float,
    seed: int,
) -> str:
    """Draw one reproducible state from a Boltzmann-weighted ensemble."""
    return boltzmann_distribution(energies, temperature).sample(seed)
