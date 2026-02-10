import pytest
from src.calculator import add, subtract, multiply, divide

def test_add_positive_numbers():
    assert add(2, 3) == 5

def test_add_negative_numbers():
    assert add(-1, -1) == -2

def test_add_mixed_numbers():
    assert add(-1, 1) == 0

def test_add_floats():
    assert add(0.1, 0.2) == pytest.approx(0.3)

def test_add_zero():
    assert add(0, 0) == 0
    assert add(5, 0) == 5
    assert add(0, 5) == 5

def test_subtract_positive_numbers():
    assert subtract(5, 3) == 2

def test_subtract_negative_numbers():
    assert subtract(-1, -1) == 0

def test_subtract_mixed_numbers():
    assert subtract(1, -1) == 2

def test_subtract_floats():
    assert subtract(0.3, 0.1) == pytest.approx(0.2)

def test_subtract_zero():
    assert subtract(0, 0) == 0
    assert subtract(5, 0) == 5
    assert subtract(0, 5) == -5

def test_multiply_positive_numbers():
    assert multiply(2, 3) == 6

def test_multiply_negative_numbers():
    assert multiply(-2, -3) == 6

def test_multiply_mixed_numbers():
    assert multiply(-2, 3) == -6

def test_multiply_floats():
    assert multiply(0.5, 0.5) == pytest.approx(0.25)

def test_multiply_zero():
    assert multiply(0, 5) == 0
    assert multiply(5, 0) == 0
    assert multiply(0, 0) == 0

def test_divide_positive_numbers():
    assert divide(6, 3) == 2

def test_divide_negative_numbers():
    assert divide(-6, -3) == 2

def test_divide_mixed_numbers():
    assert divide(-6, 3) == -2

def test_divide_floats():
    assert divide(0.6, 0.3) == pytest.approx(2.0)

def test_divide_by_zero():
    with pytest.raises(ZeroDivisionError):
        divide(1, 0)

def test_divide_by_zero_negative():
    with pytest.raises(ZeroDivisionError):
        divide(-1, 0)

def test_divide_by_zero_float():
    with pytest.raises(ZeroDivisionError):
        divide(1.0, 0.0)

def test_divide_by_zero_zero():
    with pytest.raises(ZeroDivisionError):
        divide(0, 0)

def test_divide_large_numbers():
    assert divide(1000000, 2) == 500000

def test_divide_small_numbers():
    assert divide(0.0001, 0.0002) == pytest.approx(0.5)

def test_add_large_numbers():
    assert add(1000000, 2000000) == 3000000

def test_add_small_numbers():
    assert add(0.0001, 0.0002) == pytest.approx(0.0003)

def test_subtract_large_numbers():
    assert subtract(2000000, 1000000) == 1000000

def test_subtract_small_numbers():
    assert subtract(0.0002, 0.0001) == pytest.approx(0.0001)

def test_multiply_large_numbers():
    assert multiply(1000, 2000) == 2000000

def test_multiply_small_numbers():
    assert multiply(0.001, 0.002) == pytest.approx(0.000002)

def test_add_very_large_numbers():
    assert add(1e10, 2e10) == 3e10

def test_add_very_small_numbers():
    assert add(1e-10, 2e-10) == pytest.approx(3e-10)

def test_subtract_very_large_numbers():
    assert subtract(2e10, 1e10) == 1e10

def test_subtract_very_small_numbers():
    assert subtract(2e-10, 1e-10) == pytest.approx(1e-10)

def test_multiply_very_large_numbers():
    assert multiply(1e5, 2e5) == 2e10

def test_multiply_very_small_numbers():
    assert multiply(1e-5, 2e-5) == pytest.approx(2e-10)

def test_divide_very_large_numbers():
    assert divide(2e10, 1e10) == 2.0

def test_divide_very_small_numbers():
    assert divide(2e-10, 1e-10) == pytest.approx(2.0)

def test_add_negative_and_positive():
    assert add(-5, 5) == 0
    assert add(-0.5, 0.5) == pytest.approx(0.0)

def test_subtract_negative_and_positive():
    assert subtract(-5, 5) == -10
    assert subtract(5, -5) == 10
    assert subtract(-0.5, 0.5) == pytest.approx(-1.0)
    assert subtract(0.5, -0.5) == pytest.approx(1.0)

def test_multiply_negative_and_positive():
    assert multiply(-5, 5) == -25
    assert multiply(5, -5) == -25
    assert multiply(-0.5, 0.5) == pytest.approx(-0.25)
    assert multiply(0.5, -0.5) == pytest.approx(-0.25)

def test_divide_negative_and_positive():
    assert divide(-5, 5) == -1
    assert divide(5, -5) == -1
    assert divide(-0.5, 0.5) == pytest.approx(-1.0)
    assert divide(0.5, -0.5) == pytest.approx(-1.0)

def test_add_infinity():
    assert add(float('inf'), 1) == float('inf')
    assert add(float('-inf'), 1) == float('-inf')
    assert add(float('inf'), float('-inf')) == float('nan')

def test_subtract_infinity():
    assert subtract(float('inf'), 1) == float('inf')
    assert subtract(float('-inf'), 1) == float('-inf')
    assert subtract(float('inf'), float('-inf')) == float('inf')
    assert subtract(float('-inf'), float('inf')) == float('-inf')

def test_multiply_infinity():
    assert multiply(float('inf'), 2) == float('inf')
    assert multiply(float('-inf'), 2) == float('-inf')
    assert multiply(float('inf'), float('-inf')) == float('-inf')
    assert multiply(float('-inf'), float('-inf')) == float('inf')

def test_divide_infinity():
    assert divide(float('inf'), 2) == float('inf')
    assert divide(float('-inf'), 2) == float('-inf')
    with pytest.raises(ZeroDivisionError):
        divide(1, float('inf'))
    with pytest.raises(ZeroDivisionError):
        divide(1, float('-inf'))

def test_add_nan():
    assert add(float('nan'), 1) == float('nan')
    assert add(float('nan'), float('nan')) == float('nan')

def test_subtract_nan():
    assert subtract(float('nan'), 1) == float('nan')
    assert subtract(1, float('nan')) == float('nan')

def test_multiply_nan():
    assert multiply(float('nan'), 1) == float('nan')
    assert multiply(1, float('nan')) == float('nan')

def test_divide_nan():
    assert divide(float('nan'), 1) == float('nan')
    assert divide(1, float('nan')) == float('nan')
    with pytest.raises(ZeroDivisionError):
        divide(1, float('nan'))

def test_add_type_error():
    with pytest.raises(TypeError):
        add("1", 2)
    with pytest.raises(TypeError):
        add(1, "2")

def test_subtract_type_error():
    with pytest.raises(TypeError):
        subtract("1", 2)
    with pytest.raises(TypeError):
        subtract(1, "2")

def test_multiply_type_error():
    with pytest.raises(TypeError):
        multiply("1", 2)
    with pytest.raises(TypeError):
        multiply(1, "2")

def test_divide_type_error():
    with pytest.raises(TypeError):
        divide("1", 2)
    with pytest.raises(TypeError):
        divide(1, "2")
