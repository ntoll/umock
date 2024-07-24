"""
Tests for the patch_target function used to replace a target object with a
replacement based on the target path. The target path is of the form (note the
use of a colon ":" to separate the module path from the object path):

"module.submodule:object_name.method_name".
"""

import sys
import upytest
from umock import patch_target, Mock
from tests.a_package.a_module import another_function


def test_patch_target_module():
    """
    The target path is a dotted string without a colon pointing to a specific
    object in the module. Therefore the target is the module itself. Ensure
    this is patched with the expected replacement.
    """
    target = "tests.a_package.another_module"
    mock_module = Mock()
    old_module = patch_target(target, mock_module)
    # The module is replaced with the mock module.
    assert sys.modules[target] is mock_module
    # The imported module is also the mock module.
    from tests.a_package import another_module

    assert another_module is mock_module
    # The original module is returned from the patch.
    assert old_module.__name__ == target.replace(".", "/")
    # Restore the old module.
    patch_target(target, old_module)


def test_patch_target_sub_module():
    """
    The target path is a dotted string with a colon, pointing to a module
    imported in the referenced module (on the left side of the colon). Ensure
    this is patched with the expected replacement.
    """
    target = "tests.a_package.a_module:random"
    mock_random = Mock(return_value=42)
    old_random = patch_target(target, mock_random)
    # The module is replaced with the mock module.
    assert sys.modules["tests.a_package.a_module"].random is mock_random
    # The imported module is also the mock module.
    from tests.a_package.a_module import random

    assert random is mock_random
    # The original module is returned from the patch.
    assert old_random.__name__ == "random"
    # Restore the old module.
    patch_target(target, old_random)


def test_patch_target_class():
    """
    The target path is a dotted string with a colon, pointing to a class in the
    module. Ensure this is patched with the expected replacement.
    """
    target = "tests.a_package.a_module:AClass"
    mock_class = Mock()
    old_class = patch_target(target, mock_class)
    # The class is replaced
    from tests.a_package.a_module import AClass

    assert AClass is mock_class
    # The old class is the expected one.
    assert old_class.__name__ == "AClass"
    # Restore the old class.
    patch_target(target, old_class)


def test_patch_target_function():
    """
    The target path is a dotted string with a colon, pointing to a function in
    the module. Ensure this is patched with the expected replacement.
    """
    target = "tests.a_package.a_module:a_function"
    mock_function = Mock(return_value=42)
    old_function = patch_target(target, mock_function)
    # The function is replaced, so the return value is 42.
    from tests.a_package.a_module import a_function

    assert a_function(1, 2) == 42
    # An already imported function that calls the patched function, returns
    # the expected value.
    assert another_function(1, 2) == 42
    # The old function is the expected one.
    assert old_function.__name__ == "a_function"
    # Restore the old function.
    patch_target(target, old_function)


@upytest.skip("This doesn't seem to work. Check with Damien.")
def test_patch_target_class_method():
    """
    The target path is a dotted string with a colon, pointing to a method in a
    class in the module. Ensure this is patched with the expected replacement.
    """
    target = "tests.a_package.a_module:AClass.a_method"
    mock_method = Mock(return_value=42)
    old_method = patch_target(target, mock_method)
    # The method is replaced, so the return value is 42.
    from tests.a_package.a_module import AClass

    my_object = AClass(1)
    # Other aspects of the class are not changed.
    assert my_object.a == 1
    # The method is still there.
    assert hasattr(my_object, "a_method")
    # But returns the expected value.
    assert my_object.a_method(2) == 42
    # The old method is the expected one.
    assert old_method.__name__ == "a_method"
    # Restore the old method.
    patch_target(target, old_method)


def test_patch_target_class_instance():
    """
    The target path is a dotted string with a colon, pointing to an instance of
    a class in the module. Ensure this is patched with the expected
    replacement.
    """
    target = "tests.a_package.a_module:an_object.a_method"
    mock_instance = Mock(return_value=42)
    old_method = patch_target(target, mock_instance)
    # The method is replaced, so the return value is 42.
    from tests.a_package.a_module import an_object

    # The method is still there.
    assert hasattr(an_object, "a_method")
    # But returns the expected value.
    assert an_object.a_method(2) == 42
    # The old method is the expected one.
    assert old_method.__name__ == "a_method"
    # Restore the old method.
    patch_target(target, old_method)
