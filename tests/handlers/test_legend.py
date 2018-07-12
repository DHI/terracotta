
def test_legend_handler():
    from terracotta.handlers import legend
    leg = legend.legend(colormap='jet', stretch_range=[0., 1.], num_values=50)
    assert leg
    assert len(leg) == 50
    assert len(leg[0]['rgba']) == 4
    assert leg[0]['value'] == 0. and leg[-1]['value'] == 1.
