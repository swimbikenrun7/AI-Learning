Explain each Ruff finding below. For each one, tell me:

What does the warning mean?
Why does Ruff consider it undesirable?
Is this definitely a problem or potentially just a style preference?
What would a reasonable fix look like?

Do not modify my code.

I001 [*] Import block is un-sorted or un-formatted
 --> Projects\coffeeroaster03\data_persistence.py:1:1
  |
1 | / import json
2 | | import os
3 | | from pathlib import Path
4 | | from datetime import datetime
  | |_____________________________^
5 |
6 |   DATA_DIR = Path(__file__).resolve().parent / "data"
  |
help: Organize imports
  |
2 | import os
3 + from datetime import datetime
4 | from pathlib import Path
  - from datetime import datetime
5 |
  |

DTZ007 Naive datetime constructed using `datetime.datetime.strptime()` without %z
  --> Projects\coffeeroaster03\data_persistence.py:15:45
   |
13 |                   records = json.load(file)
14 |                   for date in records:
15 |                       records[date]['date'] = datetime.strptime(records[date]['date'], 
   |  _____________________________________________^
16 | | "%m/%d/%Y").strftime("%m/%d/%Y")
   | |___________^
17 |                   return records
18 |               except json.JSONDecodeError:
   |
help: Call `.replace(tzinfo=<timezone>)` or `.astimezone()` to convert to an aware datetime

PLR1722 Use `sys.exit()` instead of `exit`
  --> Projects\coffeeroaster03\data_persistence.py:36:12
   |
34 |        except json.JSONDecodeError:
35 |            print("Error: The data file is corrupted. Exiting the program.")
36 |            exit(1)
   |            ^^^^
help: Replace `exit` with `sys.exit()`

I001 [*] Import block is un-sorted or un-formatted
 --> Projects\coffeeroaster03\test_integration.py:1:1
  |
1 | / import unittest
2 | | import sys
3 | | from io import StringIO
4 | | from ui import main
  | |___________________^
5 |
6 |   class TestIntegration(unittest.TestCase):
  |
help: Organize imports
  |
1 + import sys
2 | import unittest
  - import sys
3 | from io import StringIO
4 +
5 | from ui import main
6 |
7 +
8 | class TestIntegration(unittest.TestCase):
  |

I001 [*] Import block is un-sorted or un-formatted
 --> Projects\coffeeroaster03\test_units.py:1:1
  |
1 | / import unittest
2 | | from data_persistence import load_roast_records, save_roast_records
3 | | from user_input import get_date, get_bean_name, get_green_weight, get_finished_weight, get_roast_time, get_time_of_first_crack
4 | | from calculations import calculate_weight_loss, calculate_development_time, classify_roast
5 | | import unittest.mock as mock
  | |____________________________^
6 |
7 |   class TestDataPersistence(unittest.TestCase):
  |
help: Organize imports
   |
1  | import unittest
2  + import unittest.mock as mock
3  +
4  + from calculations import (
5  +     calculate_development_time,
6  +     calculate_weight_loss,
7  +     classify_roast,
8  + )
9  | from data_persistence import load_roast_records, save_roast_records
   - from user_input import get_date, get_bean_name, get_green_weight, get_finished_weight, get_roast_time, get_time_of_first_crack
   - from calculations import calculate_weight_loss, calculate_development_time, classify_roast
   - import unittest.mock as mock
10 + from user_input import (
11 +     get_bean_name,
12 +     get_date,
13 +     get_finished_weight,
14 +     get_green_weight,
15 +     get_roast_time,
16 +     get_time_of_first_crack,
17 + )
18 +
19 |
   |

PLR0402 [*] Use `from unittest import mock` in lieu of alias
 --> Projects\coffeeroaster03\test_units.py:5:8
  |
3 | from user_input import get_date, get_bean_name, get_green_weight, get_finished_weight, get_roast_time, get_time_of_first_crack
4 | from calculations import calculate_weight_loss, calculate_development_time, classify_roast
5 | import unittest.mock as mock
  |        ^^^^^^^^^^^^^^^^^^^^^
6 |
7 | class TestDataPersistence(unittest.TestCase):
  |
help: Replace with `from unittest import mock`
  |
4 | from calculations import calculate_weight_loss, calculate_development_time, classify_roast
  - import unittest.mock as mock
5 + from unittest import mock
6 |
  |

I001 [*] Import block is un-sorted or un-formatted
 --> Projects\coffeeroaster03\ui.py:1:1
  |
1 | / import calculations as calc
2 | | from data_persistence import load_roast_records, save_roast_records, count_roasts
3 | | from user_input import get_date, get_bean_name, get_green_weight, get_finished_weight, get_roast_time, get_time_of_first_crack
  | |______________________________________________________________________________________________________________________________^
4 |
5 |   ROAST_RECORDS = load_roast_records()
  |
help: Organize imports
   |
1  | import calculations as calc
   - from data_persistence import load_roast_records, save_roast_records, count_roasts
   - from user_input import get_date, get_bean_name, get_green_weight, get_finished_weight, get_roast_time, get_time_of_first_crack
2  + from data_persistence import count_roasts, load_roast_records, save_roast_records
3  + from user_input import (
4  +     get_bean_name,
5  +     get_date,
6  +     get_finished_weight,
7  +     get_green_weight,
8  +     get_roast_time,
9  +     get_time_of_first_crack,
10 + )
11 |
   |

PERF102 When using only the values of a dict use the `values()` method
  --> Projects\coffeeroaster03\ui.py:42:25
   |
41 | def view_roasts():
42 |     for date, record in ROAST_RECORDS.items():
   |                         ^^^^^^^^^^^^^^^^^^^
43 |         print(f"Date: {record['date']}")
44 |         print(f"Bean Name: {record['bean_name']}")
   |
help: Replace `.items()` with `.values()`

I001 [*] Import block is un-sorted or un-formatted
 --> Projects\coffeeroaster03\user_input.py:1:1
  |
1 | from datetime import datetime
  | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2 |
3 | def get_date():
  |
help: Organize imports
  |
2 |
3 +
4 | def get_date():
  |

DTZ007 Naive datetime constructed using `datetime.datetime.strptime()` without %z
 --> Projects\coffeeroaster03\user_input.py:7:24
  |
5 |         date_str = input("Enter the date (MM/DD/YYYY): ")
6 |         try:
7 |             date_obj = datetime.strptime(date_str, "%m/%d/%Y")
  |                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
8 |             if date_obj > datetime.now():
9 |                 raise ValueError("Date cannot be in the future.")
  |
help: Call `.replace(tzinfo=<timezone>)` or `.astimezone()` to convert to an aware datetime

DTZ005 `datetime.datetime.now()` called without a `tz` argument
  --> Projects\coffeeroaster03\user_input.py:8:27
   |
 6 |         try:
 7 |             date_obj = datetime.strptime(date_str, "%m/%d/%Y")
 8 |             if date_obj > datetime.now():
   |                           ^^^^^^^^^^^^^^
 9 |                 raise ValueError("Date cannot be in the future.")
10 |             return date_obj.strftime("%m/%d/%Y")
   |
help: Pass a `datetime.timezone` object to the `tz` parameter