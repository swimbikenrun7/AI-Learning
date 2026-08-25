from calculations import calculate_weight_loss, calculate_development_time, get_roast_classification

def test_calculate_weight_loss():
    assert calculate_weight_loss(250, 200) == 20.00
    assert round(calculate_weight_loss(300, 250),2) == 16.67
    assert calculate_weight_loss(200, 150) == 25.00

def test_calculate_development_time():
    assert calculate_development_time("03:00", "01:00") == 120
    assert calculate_development_time("04:30", "02:15") == 135
    assert calculate_development_time("19:00", "17:30") == 90

def test_get_roast_classification():
    assert get_roast_classification(12.00) == "City Roast"
    assert get_roast_classification(15.00) == "Full City"
    assert get_roast_classification(18.00) == "Vienna Roast"
    assert get_roast_classification(20.00) == "Italian Roast"