# When run from the command line, will read/write json/xls/csv/db/sql/mdb files
# For example
#   python -m tts_netflow_b -i input.xlsx -o solution.xlsx
# will read from a model stored in input.xlsx and write solution.xlsx.
from ticdat import standard_main
from tts_netflow_b import input_schema, solution_schema, solve
if __name__ == "__main__":
    standard_main(input_schema, solution_schema, solve)
