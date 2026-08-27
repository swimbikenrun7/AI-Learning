import roasting_logger.calculations as calc

def test_calculate_weight_loss():
    assert calc.calculate_weight_loss(200, 180) == 10.0
    assert calc.calculate_weight_loss(250, 240) == 4.0
    assert round(calc.calculate_weight_loss(300, 290), 2) == 3.33

def test_calculate_development_time():
    assert calc.calculate_development_time(600, 180) == 420
    assert calc.calculate_development_time(720, 300) == 420
    assert calc.calculate_development_time(840, 420) == 420

def test_classify_roast():
    assert calc.classify_roast(12.5) == 'City Roast'
    assert calc.classify_roast(14.0) == 'City Plus'
    assert calc.classify_roast(15.0) == 'Full City'
    assert calc.classify_roast(16.0) == 'Full City Plus'
    assert calc.classify_roast(18.0) == 'Vienna Roast'
    assert calc.classify_roast(20.0) == 'Italian Roast'