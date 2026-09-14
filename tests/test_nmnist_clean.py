import numpy as np
import torch

from experiments.nmnist.data import events_to_temporal_channels, make_development_indices
from models.nmnist_qsnn import NMNISTTemporalQSNN


def test_event_reduction_preserves_time_order_and_polarity():
    events = np.array([
        (1, 1, 0, 0), (1, 1, 10, 1), (33, 33, 20, 0), (33, 33, 30, 1),
    ], dtype=[("x", "i2"), ("y", "i2"), ("t", "i8"), ("p", "i1")])
    reduced = events_to_temporal_channels(events, temporal_bins=4)
    assert reduced.shape == (4, 8)
    assert np.count_nonzero(reduced) == 4
    assert reduced[0, 0] > 0 and reduced[1, 1] > 0
    assert reduced[2, 6] > 0 and reduced[3, 7] > 0


def test_development_indices_are_seeded_balanced_and_disjoint():
    targets = np.repeat(np.arange(10), 30)
    train, validation = make_development_indices(targets, 42, 20, 5)
    assert len(train) == 200 and len(validation) == 50
    assert not np.intersect1d(train, validation).size
    assert np.array_equal(np.bincount(targets[train]), np.full(10, 20))
    assert np.array_equal(np.bincount(targets[validation]), np.full(10, 5))


def test_temporal_qsnn_shape_and_capacity():
    model = NMNISTTemporalQSNN()
    assert model(torch.rand(2, 8, 8)).shape == (2, 10)
    assert model.trainable_parameter_count() == 298
    assert model.circuit_depth() == 88
