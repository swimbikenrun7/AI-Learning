import os
import json
from tempfile import TemporaryDirectory
from roasting_logger.calculations import get_roast_records, save_roast_records

def test_persistence_load_records():
    with TemporaryDirectory() as tmp_dir:
        file_path = os.path.join(tmp_dir, "roast_records.json")
        
        # Initialize an empty dictionary in the temporary file
        with open(file_path, 'w') as file:
            json.dump({}, file)
        
        records = get_roast_records(file_path)
        assert isinstance(records, dict)

def test_persistence_empty_file():
    with TemporaryDirectory() as tmp_dir:
        file_path = os.path.join(tmp_dir, "test_records.json")
        
        # Create an empty file in the temporary directory
        open(file_path, 'a').close()
    
        records = get_roast_records(file_path)
        assert isinstance(records, dict)

def test_persistence_non_empty_file():
    with TemporaryDirectory() as tmp_dir:
        file_path = os.path.join(tmp_dir, "non_empty_records.json")
        
        # Save some data in the temporary file
        save_roast_records({'roast1': {'weight_loss': 5.0}}, file_path)
        
        records = get_roast_records(file_path)
        assert isinstance(records, dict)
        assert records == {'roast1': {'weight_loss': 5.0}}