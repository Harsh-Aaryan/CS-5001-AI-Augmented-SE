import pytest
from src.app import is_prime, main
from unittest.mock import patch
import streamlit as st

def test_is_prime_negative():
    assert not is_prime(-1)

def test_is_prime_zero():
    assert not is_prime(0)

def test_is_prime_one():
    assert not is_prime(1)

def test_is_prime_two():
    assert is_prime(2)

def test_is_prime_three():
    assert is_prime(3)

def test_is_prime_four():
    assert not is_prime(4)

def test_is_prime_five():
    assert is_prime(5)

def test_is_prime_six():
    assert not is_prime(6)

def test_is_prime_seven():
    assert is_prime(7)

def test_is_prime_eight():
    assert not is_prime(8)

def test_is_prime_nine():
    assert not is_prime(9)

def test_is_prime_ten():
    assert not is_prime(10)

def test_is_prime_large_prime():
    assert is_prime(7919)

def test_is_prime_large_non_prime():
    assert not is_prime(7920)

def test_is_prime_large_even():
    assert not is_prime(1000000000000000000)

def test_is_prime_large_odd():
    assert not is_prime(1000000000000000001)

def test_is_prime_perfect_square():
    assert not is_prime(25)

def test_is_prime_perfect_square_prime():
    assert not is_prime(49)

def test_is_prime_negative_even():
    assert not is_prime(-4)

def test_is_prime_negative_odd():
    assert not is_prime(-3)

def test_main_prime():
    with patch('streamlit.number_input', return_value=7):
        with patch('streamlit.button', return_value=True):
            with patch('streamlit.success') as mock_success:
                with patch('streamlit.error') as mock_error:
                    main()
                    mock_success.assert_called_once_with("7 is a prime number!")
                    mock_error.assert_not_called()

def test_main_non_prime():
    with patch('streamlit.number_input', return_value=8):
        with patch('streamlit.button', return_value=True):
            with patch('streamlit.success') as mock_success:
                with patch('streamlit.error') as mock_error:
                    main()
                    mock_success.assert_not_called()
                    mock_error.assert_called_once_with("8 is not a prime number.")

def test_main_no_button_click():
    with patch('streamlit.number_input', return_value=5):
        with patch('streamlit.button', return_value=False):
            with patch('streamlit.success') as mock_success:
                with patch('streamlit.error') as mock_error:
                    main()
                    mock_success.assert_not_called()
                    mock_error.assert_not_called()

def test_main_zero():
    with patch('streamlit.number_input', return_value=0):
        with patch('streamlit.button', return_value=True):
            with patch('streamlit.success') as mock_success:
                with patch('streamlit.error') as mock_error:
                    main()
                    mock_success.assert_not_called()
                    mock_error.assert_called_once_with("0 is not a prime number.")

def test_main_one():
    with patch('streamlit.number_input', return_value=1):
        with patch('streamlit.button', return_value=True):
            with patch('streamlit.success') as mock_success:
                with patch('streamlit.error') as mock_error:
                    main()
                    mock_success.assert_not_called()
                    mock_error.assert_called_once_with("1 is not a prime number.")

def test_main_large_prime():
    with patch('streamlit.number_input', return_value=7919):
        with patch('streamlit.button', return_value=True):
            with patch('streamlit.success') as mock_success:
                with patch('streamlit.error') as mock_error:
                    main()
                    mock_success.assert_called_once_with("7919 is a prime number!")
                    mock_error.assert_not_called()

def test_main_large_non_prime():
    with patch('streamlit.number_input', return_value=7920):
        with patch('streamlit.button', return_value=True):
            with patch('streamlit.success') as mock_success:
                with patch('streamlit.error') as mock_error:
                    main()
                    mock_success.assert_not_called()
                    mock_error.assert_called_once_with("7920 is not a prime number.")
