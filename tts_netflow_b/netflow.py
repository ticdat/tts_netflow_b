#
# Core engine file for tts_netflow_b
#
try:
    import gurobipy as gp
except:
    gp = None
from ticdat import PanDatFactory, Slicer
import pandas as pd

from tts_netflow_b.tooltips import input_schema_tooltips, solution_schema_tooltips
# ------------------------ define the input schema --------------------------------
input_schema = PanDatFactory (
    commodities=[["Name"], ["Volume"]],
    nodes=[["Name"], []],
    arcs=[["Source", "Destination"], ["Capacity"]],
    cost=[["Commodity", "Source", "Destination"], ["Cost"]],
    supply=[["Commodity", "Node"], ["Quantity"]],
    demand=[["Commodity", "Node"], ["Quantity"]]
)
for (tbl, fld), tip in input_schema_tooltips.items():
    input_schema.set_tooltip(tbl, fld, tip)

# Define the foreign key relationships
input_schema.add_foreign_key("arcs", "nodes", ['Source', 'Name'])
input_schema.add_foreign_key("arcs", "nodes", ['Destination', 'Name'])
input_schema.add_foreign_key("cost", "arcs", [['Source', 'Source'],
                                              ['Destination', 'Destination']])
input_schema.add_foreign_key("cost", "commodities", ['Commodity', 'Name'])
input_schema.add_foreign_key("demand", "commodities", ['Commodity', 'Name'])
input_schema.add_foreign_key("demand", "nodes", ['Node', 'Name'])
input_schema.add_foreign_key("supply", "commodities", ['Commodity', 'Name'])
input_schema.add_foreign_key("supply", "nodes", ['Node', 'Name'])

# Define the data types
input_schema.set_data_type("commodities", "Volume", min=0, max=float("inf"),
                           inclusive_min=False, inclusive_max=False)
input_schema.set_data_type("arcs", "Capacity", min=0, max=float("inf"),
                           inclusive_min=True, inclusive_max=True)
input_schema.set_data_type("cost", "Cost", min=0, max=float("inf"),
                           inclusive_min=True, inclusive_max=False)
input_schema.set_data_type("demand", "Quantity", min=0, max=float("inf"), inclusive_min=True,
                                       inclusive_max=False)
input_schema.set_data_type("supply", "Quantity", min=0, max=float("inf"), inclusive_min=True,
                                       inclusive_max=False)

# The default-default of zero makes sense everywhere except for Capacity
input_schema.set_default_value("arcs", "Capacity", float("inf"))
# since infinity is natural for this model, lets handle infinity gracefully with a cloud GUI like Roundoff
input_schema.set_infinity_io_flag(999999999)

# we check that the same commodity node pairs don't appear both in supply and demand
def _supply_pairs(dat):
    return {"supply_pairs": {row[:2] for row in dat.supply.itertuples(index=False)}}
def _demand_pairs(dat):
    return {"demand_pairs": {row[:2] for row in dat.demand.itertuples(index=False)}}

input_schema.add_data_row_predicate("demand", predicate_name="Check Demand Against Supply",
    predicate=lambda row, supply_pairs: (row["Commodity"], row["Node"]) not in supply_pairs,
    predicate_kwargs_maker=_supply_pairs)
input_schema.add_data_row_predicate("supply", predicate_name="Check Supply Against Demand",
    predicate=lambda row, demand_pairs: (row["Commodity"], row["Node"]) not in demand_pairs,
    predicate_kwargs_maker=_demand_pairs)
# ---------------------------------------------------------------------------------



# ------------------------ define the output schema -------------------------------
solution_schema = PanDatFactory(
        flow=[["Commodity", "Source", "Destination"], ["Quantity"]],
        parameters=[["Parameter"], ["Value"]])
for (tbl, fld), tip in solution_schema_tooltips.items():
    solution_schema.set_tooltip(tbl, fld, tip)
# ---------------------------------------------------------------------------------

# ------------------------ solving section-----------------------------------------
# Since the modeling_schema is so similar to the input_schema, we'll create it using clone
# If you find this too fancy, you could also write out a full description of modeling_schema
# as you do with input_schema
modeling_schema = input_schema.clone(
    # we're going to remove the supply and demand tables before passing along to clone_factory
    table_restrictions=set(input_schema.all_tables).difference({"supply", "demand"})).\
    clone_add_a_table("inflow", ["Commodity", "Node"], ["Quantity"])


# clone copied over all the integrity rules other than those associated with supply, demand
# so all thats left is to add the inflow integrity rules
modeling_schema.add_foreign_key("inflow", "commodities", ['Commodity', 'Name'])
modeling_schema.add_foreign_key("inflow", "nodes", ['Node', 'Name'])
modeling_schema.set_data_type("inflow", "Quantity", min=-float("inf"), max=float("inf"),
                               inclusive_min=False, inclusive_max=False)

def create_modeling_dat_from_input_dat(dat):
    """
    :param dat: a good pan_dat for the input schema
    :return: a good pan_dat for the modeling schema
    """
    assert input_schema.good_pan_dat_object(dat), "bad dat check"
    assert not input_schema.find_duplicates(dat), "duplicate record check"
    assert not input_schema.find_foreign_key_failures(dat), "foreign key check"
    assert not input_schema.find_data_type_failures(dat), "data type value check"
    assert not input_schema.find_data_row_failures(dat), "data row check"

    rtn = modeling_schema.PanDat(commodities=dat.commodities, nodes=dat.nodes, arcs=dat.arcs, cost=dat.cost,
                                 inflow=dat.supply)
    df = dat.demand.copy()
    df["Quantity"] = -df["Quantity"]
    rtn.inflow = pd.concat([rtn.inflow, df], ignore_index=True)
    return rtn

def solve(dat):
    """
    core solving routine
    :param dat: a good pan_dat for the input_schema
    :return: a good pan_dat for the solution_schema, or None
    """
    return solve_from_modeling_dat(create_modeling_dat_from_input_dat(dat))

def solve_from_modeling_dat(dat):
    """
    auxiliary solving routine
    :param dat: a good pan_dat for the modeling_schema
    :return: a good pan_dat for the solution_schema, or None
    """
    assert modeling_schema.good_pan_dat_object(dat), "bad dat check"
    assert not modeling_schema.find_duplicates(dat), "duplicate record check"
    assert not modeling_schema.find_foreign_key_failures(dat), "foreign key check"
    assert not modeling_schema.find_data_type_failures(dat), "data type value check"

    # Create optimization model
    mdl = gp.Model('netflow')

    # itertuples is the most performant way to iterate over the rows of a DataFrame
    flow = {(h, i, j): mdl.addVar(name=f'flow_{h}_{i}_{j}', obj=cost)
            for h, i, j, cost in dat.cost.itertuples(index=False)}

    flowslice = Slicer(flow)
    volume = {k: volume for k, volume in dat.commodities.itertuples(index=False)}

    # Arc Capacity constraints
    for i, j, capacity in dat.arcs.itertuples(index=False):
        mdl.addConstr(gp.quicksum(flow[_h, _i, _j] * volume[_h]
                                  for _h, _i, _j in flowslice.slice('*', i, j))
                      <= capacity, name=f'cap_{i}_{j}')

    inflow = {(h, j): qty for h, j, qty in dat.inflow.itertuples(index=False) if abs(qty) > 0}
    # Flow conservation constraints. Constraints are generated only for relevant pairs.
    # So we generate a conservation of flow constraint if there is negative or positive inflow
    # quantity, or at least one inbound flow variable, or at least one outbound flow variable.
    for h, j in set(inflow).union({(h, i) for h, i, j in flow}, {(h, j) for h, i, j in flow}):
        mdl.addConstr(
            gp.quicksum(flow[h_i_j] for h_i_j in flowslice.slice(h, '*', j)) +
            inflow.get((h, j), 0) ==
            gp.quicksum(flow[h_j_i] for h_j_i in flowslice.slice(h, j, '*')),
            name=f'node_{h}_{j}')

    # Compute optimal solution
    mdl.optimize()

    if mdl.status == gp.GRB.status.OPTIMAL:
        # PanDatFactory also makes it easy to create DataFrame objects from rows of data
        rtn = solution_schema.PanDat(flow=[[h, i, j, var.x] for (h, i, j), var in flow.items() if var.x > 0],
                                     parameters=[["Total Cost",  mdl.objVal]])
        return rtn
# ---------------------------------------------------------------------------------
