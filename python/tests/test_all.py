import pytest
import liquid2


def test_sum_as_string():
    assert liquid2.sum_as_string(1, 1) == "2"
