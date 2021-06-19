#
# Core engine file for tts_netflow_b
#

from ticdat import PanDatFactory

# ------------------------ define the input schema --------------------------------
input_schema = PanDatFactory (
    commodities=[["Name"], ["Volume"]],
    nodes=[["Name"], []],
    arcs=[["Source", "Destination"], ["Capacity"]],
    cost=[["Commodity", "Source", "Destination"], ["Cost"]],
    supply=[["Commodity", "Node"], ["Quantity"]],
    demand=[["Commodity", "Node"], ["Quantity"]]
)

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
# ---------------------------------------------------------------------------------

# ------------------------ solving section-----------------------------------------
# Since the modeling_schema is so similar to the input_schema, we'll create it using clone
# If you find this too fancy, you could also write out a full description of modeling_schema
# as you do with input_schema

def _add_inflow_table(full_schema_dict):
    # as per the clone docstring, this function will take a full_schema_dict as argument and
    # return the  PanDatFactory we want to make.. in this case, all we need to do is add inflow.
    full_schema_dict["tables_fields"]["inflow"] = [["Commodity", "Node"], ["Quantity"]]
    rtn = PanDatFactory.create_from_full_schema(full_schema_dict)
    return rtn

modeling_schema = input_schema.clone(
    # we're going to remove the supply and demand tables before passing along to clone_factory
    table_restrictions=set(input_schema.all_tables).difference({"supply", "demand"}),
    clone_factory=_add_inflow_table)

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
    rtn.inflow = rtn.inflow.append(df, sort=False)
    return rtn

def solve(dat):
    """
    core solving routine
    :param dat: a good pan_dat for the input_schema
    :return: a good pan_dat for the solution_schema, or None
    """
    return solve_from_modeling_dat(create_modeling_dat_from_input_dat(dat))

def solve_from_modeling_dat(dat):
    assert modeling_schema.good_pan_dat_object(dat), "bad dat check"
    assert not modeling_schema.find_duplicates(dat), "duplicate record check"
    assert not modeling_schema.find_foreign_key_failures(dat), "foreign key check"
    # still need math functionality

# ---------------------------------------------------------------------------------
