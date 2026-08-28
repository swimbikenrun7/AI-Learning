import unittest
from data_persistence import load_roast_records, save_roast_records
from user_input import get_date, get_bean_name, get_green_weight, get_finished_weight, get_roast_time, get_time_of_first_crack
from calculations import calculate_weight_loss, calculate_development_time, classify_roast
import unittest.mock as mock

class TestDataPersistence(unittest.TestCase):
    def test_load_roast_records(self):
        records = load_roast_records()
        self.assertIsInstance(records, dict)

    def test_save_roast_records(self):
        records = {'04/15/2023': {'date': '04/15/2023', 'bean_name': 'Arabica', 'green_weight': 250, 'finished_weight': 180}}
        save_roast_records(records)
        loaded_records = load_roast_records()
        self.assertIn('04/15/2023', loaded_records)

class TestUserInput(unittest.TestCase):
    @mock.patch('builtins.input')
    def test_get_date(self, mock_input):
        mock_input.return_value = '04/15/2023'
        date = get_date()
        self.assertEqual(date, '04/15/2023')

    @mock.patch('builtins.input')
    def test_get_bean_name(self, mock_input):
        mock_input.return_value = 'Arabica'
        bean_name = get_bean_name()
        self.assertEqual(bean_name, 'Arabica')

    @mock.patch('builtins.input')
    def test_get_green_weight(self, mock_input):
        mock_input.return_value = '250'
        green_weight = get_green_weight()
        self.assertEqual(green_weight, 250)

    @mock.patch('builtins.input')
    def test_get_finished_weight(self, mock_input):
        mock_input.return_value = '180'
        finished_weight = get_finished_weight(250)
        self.assertEqual(finished_weight, 180)

    @mock.patch('builtins.input')
    def test_get_roast_time(self, mock_input):
        mock_input.return_value = '08:30'
        total_roast_time = get_roast_time()
        self.assertEqual(total_roast_time, 510)

    @mock.patch('builtins.input')
    def test_get_time_of_first_crack(self, mock_input):
        mock_input.return_value = '06:45'
        time_of_first_crack = get_time_of_first_crack(510)
        self.assertEqual(time_of_first_crack, 405)

class TestCalculations(unittest.TestCase):
    def test_calculate_weight_loss(self):
        green_weight = 250
        finished_weight = 180
        expected_loss = ((green_weight - finished_weight) / green_weight) * 100
        self.assertEqual(calculate_weight_loss(green_weight, finished_weight), expected_loss)

    def test_calculate_development_time(self):
        total_roast_time = 900
        time_of_first_crack = 800
        development_time = total_roast_time - time_of_first_crack
        self.assertEqual(calculate_development_time(total_roast_time, time_of_first_crack), development_time)

    def test_classify_roast(self):
        weight_loss = 14.0
        classification = classify_roast(weight_loss)
        self.assertEqual(classification, 'City Plus')

if __name__ == '__main__':
    unittest.main()