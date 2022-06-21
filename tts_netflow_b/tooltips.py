# To minimize distraction from the logical code in netflow.py, I'm putting the tooltips in this file.
# The tooltips are completely optional but they make the schemas more comprehensible.
input_schema_tooltips = {
    ("commodities", ""): "Definte the commodities.",
    ("commodities", "Name"): "The name of the commodity.",
    ("commodities", "Volume"): "The volumne for one unit of this commodity.",
    ("nodes", ""): "Definte the nodes.",
    ("nodes", "Name"): "The name of the node.",
    ("arcs", ""): "Populate the arcs table as a pre-requisite to populating the cost table.",
    ("arcs", "Source"): "The source node for the arc.",
    ("arcs", "Destination"): "The destination node for the arc.",
    ("arcs", "Capacity"): "The total units, summed across all commodities, that can be shipped between the source " +
                          "destination.",
    ("cost", ""): "Populate the costs table to allow a commodity to be shipped between two nodes.",
    ("cost", "Source"): "The node to serve as the source for the shipment.",
    ("cost", "Destination"): "The node to serve as the destination for the shipment.",
    ("cost", "Commodity"): "The commodity that can be shipped.",
    ("cost", "Cost"): "The per-unit cost of shipping one unit of the commodity between the source and the destination.",
    ("supply", ""): "Populate the supply table to allow a commodity to be sourced by a node.",
    ("supply", "Node"): "The node to serve as a supplier.",
    ("supply", "Commodity"): "The commodity to be supplier.",
    ("supply", "Quantity"): "The number of units of this commodity to be supplied by this node.",
    ("demand", ""): "Populate the demand table to allow a commodity to be consumed by a node.",
    ("demand", "Node"): "The node to serve as a consumer.",
    ("demand", "Commodity"): "The commodity to be consumed.",
    ("demand", "Quantity"): "The number of units of this commodity to be consumed at this node."
}

solution_schema_tooltips = {
    ("flow", ""): "This report defines the specific shipments.",
    ("flow", "Source"): "The source for the shipment.",
    ("flow", "Destination"): "The destination for the shipment.",
    ("flow", "Commodity"): "The commodity being shipped.",
    ("flow", "Quantity"): "The number of units being shipped.",
    ("parameters", ""): "This report lists the Key Performance Indicators for the solution.",
    ("parameters", "Parameter"): "This name of the Key Performance Indicator.",
    ("parameters", "Value"): "The value of the Key Performance Indicator..",
}