import pandas as pd
import time
from os import listdir
from constants import *

class IO:
	def __init__(self):
		self.workbooks = None
		self.orders_df = None
		self.writer = pd.ExcelWriter('{output_folder}/{t}.xlsx'.format(output_folder = OUTPUT_FOLDER, t=time.strftime("%Y%m%d-%H%M%S")),engine='xlsxwriter')
		self.formats = {'text_wrap':TEXT_WRAP,'align':ALIGN,'valign':VALIGN,'font_name':FONT_NAME,'font_size':FONT_SIZE}
		self.hasoutput = False

	def process_inputs(self):
		assert (len(listdir(WORKBOOK_FOLDER))) > 0
		self.workbooks = listdir(WORKBOOK_FOLDER)
		self.orders_df = pd.DataFrame()
		for workbook in self.workbooks:
			df = pd.read_excel(f'{WORKBOOK_FOLDER}/{workbook}',usecols = [RAW_ADDR_HEADER,WECHAT_HEADER,ITEMS_HEADER])
			df.dropna(inplace=True)
			self.orders_df = pd.concat([self.orders_df,df],ignore_index=True)

	def process_output(self,sheet,cols):
		assert len(cols) == TOTAL_COLS
		df = pd.DataFrame(list(zip(*cols)),columns=COL_HEADERS)
		df.to_excel(self.writer, sheet_name = sheet,index=False)

	def output_process_complete(self):
		self.hasoutput = True

	def process_formats(self):
		assert self.hasoutput
		outfile = self.writer.book
		formats = outfile.add_format(self.formats)
		for sheet in self.writer.sheets:
			self.writer.sheets[sheet].set_column('A:D',50,formats)
		self.writer.close()