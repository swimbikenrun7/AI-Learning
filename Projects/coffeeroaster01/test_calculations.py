# Import the function from main.py
from calculations import calculate_weight_loss_percentage

# Define the first test case
def test_weight_loss_100_to_90():
    # Call the function with the given inputs
    result = calculate_weight_loss_percentage(100, 90)
    # Assert that the result is as expected (10%)
    assert round(result, 2) == 10.00

# Define the second test case
def test_weight_loss_100_to_80():
    # Call the function with the given inputs
    result = calculate_weight_loss_percentage(100, 80)
    # Assert that the result is as expected (20%)
    assert round(result, 2) == 20.00

# Define the third test case
def test_weight_loss_225_to_191():
    # Call the function with the given inputs
    result = calculate_weight_loss_percentage(225, 191)
    # Assert that the result is as expected (approximately 15.11%)
    assert round(result, 2) == 15.11

# Define the fourth test case
def test_weight_loss_200_to_180():
    # Call the function with the given inputs
    result = calculate_weight_loss_percentage(200, 180)
    # Assert that the result is as expected (approximately 10.00%)
    assert round(result, 2) == 10.00