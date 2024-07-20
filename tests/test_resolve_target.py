"""
Tests for the resolve_target function used to return a target Python object
from a target string.
"""

import upytest
from umock import resolve_target


def test_resolve_target_no_colon():
    """
    The target path is a dotted string without a colon pointing to a specific
    object in the module.
    """
    target = "tests.a_package.a_module.AClass"
    expected = "AClass"
    actual = resolve_target(target)
    assert actual.__name__ == expected


def test_resolve_target_with_colon():
    """
    The target path is a dotted string with a colon pointing to a specific
    object in the module.
    """
    target = "tests.a_package.a_module:AClass.a_method"
    expected = "a_method"
    actual = resolve_target(target)
    assert actual.__name__ == expected


def test_resolve_target_with_object():
    """
    If the target is already an object, return it as is.
    """
    target = "tests.a_package.a_module.AClass"
    expected = resolve_target(target)
    actual = resolve_target(expected)
    assert actual is expected


def test_resolve_target_invalid_target():
    """
    If the target path points to an invalid object, raise an AttributeError.
    """
    target = "tests.a_package.a_module:AClass.not_a_method"
    with upytest.raises(AttributeError):
        resolve_target(target)
