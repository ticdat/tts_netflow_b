## Write glue code responsibly

Python is a great language for writing "glue code". Tidy, Tested, Safe shouldn't be interpreted as 
"never write free standing .py files". Rather, free standing .py files should primarily be used for 
quick and dirty proof-of-concept work. When a .py file is used as industrial code, it should be very short, 
with all the heavy lifting being done by calling the public interface of a package. 

The `tts_netflow_b_modeling_schema.py` file is a good example of the latter. This is a reasonably clean way
to support more than one command line interface to a package.  Of course, one could also edit the 
`__main__.py` file to look for additional flagging to determine which functionality to use. I demonstrate
an auxiliary script instead because its easier to write. There is no need to be deontological about the 
"production code belongs in packages" rule.
