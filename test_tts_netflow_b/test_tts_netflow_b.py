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
    def _sln_validate(self, dat, sln):
        merged_flow = sln.flow.merge(dat.cost, on=["Commodity", "Source", "Destination"], how="left", indicator=True)
        self.assertFalse((merged_flow["_merge"] == "left_only").any(),
            "Solution has flows for invalid (Commodity, Source, Destination).")

        flow_vol = sln.flow.merge(dat.commodities.rename(columns={"Name": "Commodity"}), on="Commodity")
        flow_vol["FlowVolume"] = flow_vol["Quantity"] * flow_vol["Volume"]
        arc_flow = flow_vol.groupby(["Source", "Destination"], as_index=False)["FlowVolume"].sum()
        arc_check = arc_flow.merge(dat.arcs, on=["Source", "Destination"], how="left")
        self.assertFalse((arc_check["FlowVolume"] > arc_check["Capacity"] * (1 + 1e-5)).any(),
            "Capacity constraint violated on at least one arc.")

        inbound = sln.flow.groupby(["Commodity", "Destination"], as_index=False)["Quantity"].sum()
        inbound.rename(columns={"Destination": "Node", "Quantity": "FlowIn"}, inplace=True)

        outbound = sln.flow.groupby(["Commodity", "Source"], as_index=False)["Quantity"].sum()
        outbound.rename(columns={"Source": "Node", "Quantity": "FlowOut"}, inplace=True)

        supply = dat.supply.rename(columns={"Quantity": "Supply"})
        demand = dat.demand.rename(columns={"Quantity": "Demand"})

        flow_bal = pd.merge(inbound, outbound, on=["Commodity", "Node"], how="outer")
        flow_bal = pd.merge(flow_bal, supply, on=["Commodity", "Node"], how="outer")
        flow_bal = pd.merge(flow_bal, demand, on=["Commodity", "Node"], how="outer")
        flow_bal.fillna(0, inplace=True)

        for row in flow_bal.itertuples():
            lhs = row.FlowIn + row.Supply
            rhs = row.FlowOut + row.Demand
            self.assertTrue(math.isclose(lhs, rhs, rel_tol=1e-5),
                f"Flow conservation failed for Commodity={row.Commodity}, Node={row.Node}: "
                f"inbound + supply = {lhs}, outbound + demand = {rhs}")

        flow_cost = sln.flow.merge(dat.cost, on=["Commodity", "Source", "Destination"])
        computed_cost = (flow_cost["Quantity"] * flow_cost["Cost"]).sum()
        reported_cost = sln.parameters.loc[sln.parameters["Parameter"] == "Total Cost", "Value"].iloc[0]

        self.assertTrue( math.isclose(computed_cost, reported_cost, rel_tol=1e-5))

    def test_standard_data_set(self):
        dat = get_test_data("sample_data.json")
        sln = tts_netflow_b.solve(dat)
        self._sln_validate(dat, sln)
        self.assertTrue(math.isclose(list(sln.parameters[sln.parameters["Parameter"] == "Total Cost"]["Value"])[0],
                                     5500.0, rel_tol=1e-4))
        # simple demo of editing the dat object to validate a related solve
        dat.cost.loc[(dat.cost["Commodity"] == "Pencils") & (dat.cost["Source"] == "Denver") &
                     (dat.cost["Destination"] == "Seattle"), "Cost"] = 300
        sln = tts_netflow_b.solve(dat)
        self._sln_validate(dat, sln)
        self.assertTrue(math.isclose(list(sln.parameters[sln.parameters["Parameter"] == "Total Cost"]["Value"])[0],
                                     6100.0, rel_tol=1e-4))
    def test_sloan_data_set(self):
        # This data set was pulled from this MIT Sloan School of Management example problem here https://bit.ly/3254VpT
        dat = get_test_data("sloan_data_set.json")
        sln = tts_netflow_b.solve(dat)
        self._sln_validate(dat, sln)
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