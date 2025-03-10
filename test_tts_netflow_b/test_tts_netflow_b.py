import os
import inspect
import tts_netflow_b
import unittest
import math
import pandas as pd

def _this_directory() :
    return os.path.dirname(os.path.realpath(os.path.abspath(inspect.getsourcefile(_this_directory))))

def get_test_data(data_set_name):
    path = os.path.join(_this_directory(), "data", data_set_name)
    assert os.path.exists(path), f"bad path {path}"
    # right now assumes data is archived as a single json file for each data set
    if os.path.isfile(path):
        return tts_netflow_b.input_schema.json.create_pan_dat(path)

class TestNetflow(unittest.TestCase):
    def test_standard_data_set(self):
        dat = get_test_data("sample_data.json")
        sln = tts_netflow_b.solve(dat)
        self.assertTrue(math.isclose(list(sln.parameters[sln.parameters["Parameter"] == "Total Cost"]["Value"])[0],
                                     5500.0, rel_tol=1e-4))
        # simple demo of editing the dat object to validate a related solve
        dat.cost.loc[(dat.cost["Commodity"] == "Pencils") & (dat.cost["Source"] == "Denver") &
                     (dat.cost["Destination"] == "Seattle"), "Cost"] = 300
        sln = tts_netflow_b.solve(dat)
        self.assertTrue(math.isclose(list(sln.parameters[sln.parameters["Parameter"] == "Total Cost"]["Value"])[0],
                                     6100.0, rel_tol=1e-4))
    def test_sloan_data_set(self):
        # This data set was pulled from this MIT Sloan School of Management example problem here https://bit.ly/3254VpT
        dat = get_test_data("sloan_data_set.json")
        sln = tts_netflow_b.solve(dat)
        self.assertTrue({row[:3]:row[-1] for row in sln.flow.itertuples(index=False)} ==
            {(2, 3, 2): 2.0,
             (2, 2, 5): 2.0,
             (2, 5, 6): 2.0,
             (1, 1, 2): 3.0,
             (1, 2, 5): 3.0,
             (1, 5, 4): 3.0,
             (1, 1, 4): 2.0})

    def test_supply_demand_integrity(self):
        dat = get_test_data("sample_data.json")
        dat.supply = pd.concat([dat.supply, dat.demand[-2:-1]], ignore_index=True)
        ex = []
        try:
            tts_netflow_b.solve(dat)
        except AssertionError as e: # safe to assume unit tests aren't run with asserts disabled
            ex.append(e)
        self.assertTrue(ex and 'data row check' == str(ex[0]))
        # both supply and demand should have a data row problem
        self.assertTrue(set(map(tuple, tts_netflow_b.input_schema.find_data_row_failures(dat))) ==
                        {('demand', 'Check Demand Against Supply'), ('supply', 'Check Supply Against Demand')})

# Run the tests via the command line
if __name__ == "__main__":
    unittest.main()