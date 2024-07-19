"""
Tests the patch decorator/context manager.
"""

from umock import patch


def test_patch_decorator():
    """
    Tests the patch decorator.
    """

    @patch("tests.test_patch.some_function", lambda: 42)
    def test():
        from tests.test_patch import some_function

        assert some_function() == 42

    test()
