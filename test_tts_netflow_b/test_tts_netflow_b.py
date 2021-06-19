import os
import inspect
import tts_netflow_b
import unittest
import collections

def _this_directory() :
    return os.path.dirname(os.path.realpath(os.path.abspath(inspect.getsourcefile(_this_directory))))

def get_test_data(data_set_name):
    path = os.path.join(_this_directory(), "data", data_set_name)
    assert os.path.exists(path), f"bad path {path}"
    # right now assumes data is archived as a single json file for each data set
    if os.path.isfile(path):
        return tts_netflow_b.input_schema.json.create_pan_dat(path)

def _nearly_same(x, y, epsilon=1e-5):
    if x == y or max(abs(x), abs(y)) < epsilon:
        return True
    if min(abs(x), abs(y)) > epsilon:
        return abs(x-y) /  min(abs(x), abs(y)) < epsilon

class TestNetflow(unittest.TestCase):
    def test_standard_data_set(self):
        dat = get_test_data("sample_data.json")
        tts_netflow_b.solve(dat) # just checking that no data integrity exceptions are thrown


# Run the tests via the command line
if __name__ == "__main__":
    unittest.main()