"""Guards on the model / scaler contract the backend relies on.

If a retrained model or scaler is dropped in with the wrong shape, these fail
fast instead of the app returning silently wrong numbers.
"""


def test_model_input_shape(module):
    assert module.model.input_shape == (None, 30, 5)


def test_model_output_width(module):
    # temp_f, humidity, wind, rain
    assert module.model.output_shape == (None, 4)


def test_input_scaler_feature_count(module):
    assert module.scaler_X.n_features_in_ == 5


def test_target_scaler_feature_count(module):
    assert module.scaler_y.n_features_in_ == 4


def test_output_width_matches_target_scaler(module):
    assert module.model.output_shape[-1] == module.scaler_y.n_features_in_


def test_expected_window_shape_constant(module):
    assert module.EXPECTED_WINDOW_SHAPE == (30, 5)
