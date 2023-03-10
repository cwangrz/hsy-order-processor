from processors.stats import Stats
from processors.io import IO
from order import Order
from constants import *

#Instantiate
stats = Stats()
io = IO()

#read excel forms into dataframe
#fail if empty workbook folder
io.process_inputs()

#convert data in dataframe into list of order objects
orders_df = io.orders_df
orders = tuple(Order(orders_df[WECHAT_HEADER][r],orders_df[RAW_ADDR_HEADER][r],orders_df[ITEMS_HEADER][r]) for r in range(len(orders_df)))

#pass order objects to stats for processing
#currently only processes basic info based on compound 
stats.process_stats(orders)

#get compounds list from stats and associated colum data for output processing
compounds = stats.get_compounds()
for compound in compounds:
	cols = stats.get_cols_by_compound(compound)
	io.process_output(compound,cols)
io.output_process_complete() #must be called before adding format
io.process_formats() #will close writer

#print some stats
stats.print_stats()
