import numpy as np


def test_legend_handler():
    from terracotta.handlers import legend
    leg = legend.legend(colormap='jet', stretch_range=[0., 1.], num_values=50)
    assert leg
    assert len(leg) == 50
    assert len(leg[0]['rgb']) == 3
    assert leg[0]['value'] == 0. and leg[-1]['value'] == 1.


def test_nocmap():
    from terracotta.handlers import legend
    leg = legend.legend(stretch_range=[0., 1.], num_values=255)
    leg_array = np.array([row['rgb'] for row in leg])
    np.testing.assert_array_equal(leg_array, np.tile(np.arange(1, 256)[:, np.newaxis], (1, 3)))
