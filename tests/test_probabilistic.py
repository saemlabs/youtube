import math

import pytest

from saemphysics.probabilistic import (
    boltzmann_distribution,
    sample_boltzmann_state,
    update_belief,
)


def test_boltzmann_distribution_normalizes_and_favors_lower_energy():
    distribution = boltzmann_distribution(
        {"low": 0.0, "high": 2.0},
        temperature=1.0,
    )

    assert math.fsum(
        probability for _, probability in distribution.probabilities
    ) == pytest.approx(1)
    assert distribution.probability_of("low") == pytest.approx(
        1 / (1 + math.exp(-2))
    )
    assert distribution.entropy_nats > 0


def test_boltzmann_distribution_uses_stable_energy_shifting():
    distribution = boltzmann_distribution(
        {"state-a": 1e300, "state-b": 1e300 + 1e290},
        temperature=1e290,
    )

    assert all(math.isfinite(value) for _, value in distribution.probabilities)
    assert sum(value for _, value in distribution.probabilities) == pytest.approx(1)


def test_bayesian_update_applies_likelihood_and_normalizes():
    prior = boltzmann_distribution({"left": 0.0, "right": 0.0}, temperature=1.0)

    posterior = update_belief(prior, {"left": 0.9, "right": 0.1})

    assert posterior.probability_of("left") == pytest.approx(0.9)
    assert posterior.probability_of("right") == pytest.approx(0.1)


def test_zero_likelihood_observation_for_all_states_is_rejected():
    prior = boltzmann_distribution({"left": 0.0, "right": 1.0}, temperature=1.0)

    with pytest.raises(ValueError, match="at least one weight"):
        update_belief(prior, {"left": 0.0, "right": 0.0})


def test_bayesian_update_rejects_invalid_likelihood_values():
    prior = boltzmann_distribution({"left": 0.0, "right": 1.0}, temperature=1.0)

    with pytest.raises(ValueError, match="finite non-negative"):
        update_belief(prior, {"left": 1.0, "right": float("nan")})


def test_normalization_handles_large_finite_weights():
    prior = boltzmann_distribution({"left": 0.0, "right": 0.0}, temperature=1.0)

    posterior = update_belief(
        prior,
        {"left": 1e308, "right": 1e308},
    )

    assert posterior.probability_of("left") == pytest.approx(0.5)
    assert posterior.probability_of("right") == pytest.approx(0.5)


def test_sampling_is_reproducible_and_favors_lower_energy():
    energies = {"preferred": 0.0, "unlikely": 12.0}

    assert sample_boltzmann_state(energies, temperature=0.5, seed=47) == (
        sample_boltzmann_state(energies, temperature=0.5, seed=47)
    )
    draws = [
        sample_boltzmann_state(energies, temperature=1.0, seed=seed)
        for seed in range(100)
    ]
    assert draws.count("preferred") > 95


@pytest.mark.parametrize(
    ("energies", "temperature"),
    [
        ({}, 1.0),
        ({"state": float("nan")}, 1.0),
        ({"state": 10**1000}, 1.0),
        ({"state": 0.0}, 0.0),
        ({"state": 0.0}, float("inf")),
    ],
)
def test_boltzmann_distribution_rejects_invalid_parameters(energies, temperature):
    with pytest.raises(ValueError):
        boltzmann_distribution(energies, temperature)


def test_bayesian_update_rejects_incomplete_likelihoods():
    prior = boltzmann_distribution({"left": 0.0, "right": 1.0}, temperature=1.0)

    with pytest.raises(ValueError, match="exactly the states"):
        update_belief(prior, {"left": 1.0})
