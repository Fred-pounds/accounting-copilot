#!/usr/bin/env python3
"""Test exception re-raising with pytest.raises"""

import pytest

class MyException(Exception):
    pass

def inner_function():
    raise MyException("Inner error")

def outer_function():
    try:
        inner_function()
    except MyException:
        # Re-raise the exception
        raise

def test_reraise():
    """Test that pytest.raises catches re-raised exceptions"""
    with pytest.raises(MyException):
        outer_function()
    print("Test passed!")

if __name__ == "__main__":
    test_reraise()
    print("All tests passed!")
