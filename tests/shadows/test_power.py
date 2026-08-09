from src.core.power import discrete_log_shadow, iterate_transformer, nth_root_shadow, ratio_power
from src.core.ratio import ratio_from_ints, ratio_shadow
from src.core.transformer import affine_transformer, apply_transformer


def test_ratio_power_positive_zero_negative():
    assert ratio_shadow(ratio_power(ratio_from_ints(2), 3)) == 8
    assert ratio_shadow(ratio_power(ratio_from_ints(5), 0)) == 1
    assert ratio_shadow(ratio_power(ratio_from_ints(2), -1)) == ratio_shadow(ratio_from_ints(1, 2))


def test_exact_nth_root_shadow():
    root = nth_root_shadow(ratio_from_ints(8), 3)
    assert root.status == "unique"
    assert root.value is not None
    assert ratio_shadow(root.value) == 2
    blocked = nth_root_shadow(ratio_from_ints(2), 2)
    assert blocked.status == "none"
    assert blocked.obstruction == "irrational-shadow"


def test_discrete_log_shadow():
    result = discrete_log_shadow(ratio_from_ints(2), ratio_from_ints(32), 10)
    assert result.status == "unique"
    assert result.value == 5
    missing = discrete_log_shadow(ratio_from_ints(3), ratio_from_ints(10), 5)
    assert missing.obstruction == "outside-search-window"


def test_iterate_transformer_affine_translation():
    shift = affine_transformer(ratio_from_ints(1), ratio_from_ints(2), "shift")
    triple = iterate_transformer(shift, 3).transformer
    assert ratio_shadow(apply_transformer(triple, ratio_from_ints(1))) == 7
