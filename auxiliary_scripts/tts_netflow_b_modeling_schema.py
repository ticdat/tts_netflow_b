# When run from the command line, will read/write json/xls/csv/db/sql/mdb files
# For example
#   python tts_netflow_b_modeling_schema.py -i input.xlsx -o solution.xlsx
# will read from a model stored in input.xlsx and write solution.xlsx.
# Will use tts_netflow_b.modeling_schema as the input schema. E.g. the input.xlsx file
# should have an inflow tab, but neither a supply nor a demand tab.
from ticdat import standard_main
from tts_netflow_b import modeling_schema, solution_schema, solve_from_modeling_dat
if __name__ == "__main__":
    standard_main(modeling_schema, solution_schema, solve_from_modeling_dat)