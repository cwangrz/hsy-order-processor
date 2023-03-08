class Order:
	def __init__(self,wechat_id,raw_addr,raw_items):
		self.wechat_id = wechat_id
		self.addr = Address(raw_addr)
		self.items = Items(raw_items)

class Address:
	def __init__(self,raw_addr):
		self.raw_addr = raw_addr
		self.raw_min_len = 5
		self.compound = None
		self.meta = None
		#long forms must come before short hand: [北京市, 北京]
		self.general_filters = ('北京市','北京','顺义区','顺义','后沙峪镇','后沙峪','空港街道','安庆大街','小区','(',')','（','）','[',']','【','】')
		self.punctuation_filters = ('.','。',',','，','-')
		#{delimiter:output_len_upperbound}
		self.suffix_delimiters = {'区':3,'家园':2,'国门一号':2}
		self.prefix_delimiters = ('菜鸟驿站',)
		self.process_addr()

	def process_addr(self):
		import re
		self.error_check()

		#1.【general filters】- state, city, town, street names and symbols
		temp = self.raw_addr.strip()
		for f in self.general_filters:
			temp = temp.replace(f, '')
		
		#2.【punctionation filters】
		for p in self.punctuation_filters:
			temp = temp.replace(p, ' ')

		#3.【extra whitespace removal】
		temp = re.sub(' +',' ',temp)
		
		#4.【suffix delimiters】- for compound names including numerals or 南区/北区
		compound = None
		meta = temp
		for (suffix_delimiter,bound) in self.suffix_delimiters.items():
			tokens = meta.split(suffix_delimiter)
			assert len(tokens) <= bound
			if len(tokens) > 1:
				compound = suffix_delimiter.join(tokens[0:-1])+suffix_delimiter
			meta = tokens[-1]
		#print('SUFFIX ROUND:',(compound,meta))

		#5.【prefix delimiters】- for meta without building/unit/room info such as '菜鸟驿站'
		for prefix_delimiter in self.prefix_delimiters:
			if meta == prefix_delimiter: #if meta is only left with delimiter itself, then skip
				break
			tokens = meta.split(prefix_delimiter)
			assert len(tokens) <= 2
			if len(tokens) > 1:
				compound = tokens[0] #might overwrite result from previous attempt. but should be ok..?
				meta = prefix_delimiter+" "+tokens[-1]
				break
		#print('PREFIX ROUND:',(compound,meta))

		#6.【chinese to arabic numeral】
		chinese_nums = ["二十","十九","十八","十七","十六","十五","十四","十三","十二","十一","十","九","八","七","六","五","四","三","二","一"]
		for cn in chinese_nums:
			meta = meta.replace(cn,str(20-chinese_nums.index(cn)))

		#7.【last resort】uses first numeric char as delimiter 
		if not compound:
			for i in range(len(meta)):
				if meta[i].isnumeric():
					compound = meta[0:i]
					meta = meta[i:]
					break
			#print('FINAL ROUND:',(compound,meta))

		#8. clean up meta so that we only keep essential info
		assert meta
		exclude_str = '^0123456789'
		#Have to keep all prefix delimiters
		for pf in self.prefix_delimiters:
			exclude_str += pf
		exclude_str = '['+exclude_str+']'
		clean_meta = re.sub(exclude_str, ' ', meta) #remove irrelevant chars
		clean_meta = re.sub(' +', ' ',clean_meta).strip() #remove extra white spaces
		if clean_meta != '': #if clean_meta is empty then we should probably keep the original shit that was in there.
			meta = clean_meta

		#9.fill in legacy 公园十七区 orders. '北7 1 1' -> '公园十七区北区 7 1 1'
		if len(compound) == 0: #**********************************temporary fix**********************************
			compound = '公园十七区北区'
		elif len(compound) == 1:
			compound = '公园十七区'+compound+'区'
		elif len(compound) == 2:
			compound = '公园十七区'+compound

		#10.normalize all 公园十七区 namings
		if compound[0:2] == '17':
			compound = compound.replace('17区','公园十七区')
		if compound[0:2] == '十七':
			compound = compound.replace('十七区','公园十七区')
		compound = compound.replace('公元十七区','公园十七区').replace('公元17区','公园十七区').replace('17','十七').replace('1区','北区').replace('一区','北区').replace('2区','南区').replace('二区','南区')

		#11.output
		assert compound
		self.compound = compound.strip()
		self.meta = meta.strip()

	def error_check(self):
		assert self.raw_addr
		if len(self.raw_addr) < self.raw_min_len:
			print('请检查以下地址:')
			print(self.raw_addr)
			choice = input('1.无误  2.手动输入   ')
			if choice == '2':
				self.raw_addr = input('收货地址: ')

	def __str__(self):
		if self.compound and self.meta:
			return self.compound + ' ' + self.meta
		return 'None'

class Items:
	def __init__(self,raw_items):
		self.raw_items = raw_items
		#{item:quantity}
		self.summary = {}
		self.entry_delimiter = '\n'
		self.quant_delimiter = '*'
		self.process_items()

	def process_items(self):
		assert self.raw_items
		#raw format: '鸡蛋(30个)*1\n🇨🇱智利空运3J西梅👑(500g)*3\nxxxxxx*n\n'
		#1. split entries by entry_delimiter -> ['鸡蛋(30个)*1','🇨🇱智利空运3J西梅👑(500g)*3','xxxxxx*n']
		entries = self.raw_items.strip().split(self.entry_delimiter)
		assert entries
		#2. split items and quantities by quant_delimiter -> {'鸡蛋(30个)':1,'🇨🇱智利空运3J西梅👑(500g)':3,'xxxxxx':n}
		#   NOTE: item might contain delimiter.   'xxxxxx(500g*5)*3'  so here is only using last occurence
		for entry in entries:
			tokens = entry.split(self.quant_delimiter)
			item = self.quant_delimiter.join(tokens[0:-1]) #glue back item names that contain delimiters
			assert item
			quantity = int(tokens[-1])
			assert quantity > 0
			self.summary[item] = self.summary.get(item,0)+quantity

	def __str__(self):
		return str(self.summary)

class Stats:
	def __init__(self):
		self.by_compound = {}
		self.by_customer = {}
		self.by_item = {}
		self.items_header = '商品合计'
		self.raw_addr_header = '备用地址'
		self.wechat_header = '微信昵称'

	def process_stats(self,order):
		raw_addr = order.addr.raw_addr
		compound = order.addr.compound
		meta = order.addr.meta
		wechat_id = order.wechat_id
		items = order.items
		self.by_compound.setdefault(compound,{}).setdefault(meta,{}).setdefault(self.items_header,{}).update(items.summary) #update items
		self.by_compound[compound][meta][self.raw_addr_header] = raw_addr #update raw address
		self.by_compound[compound][meta][self.wechat_header] = wechat_id

	def get_compounds(self):
		compounds =  tuple(self.by_compound.keys())
		return compounds

	def get_columns(self,compound):
		rows = self.by_compound[compound]
		metas = tuple(' - '.join(meta.split(' ')) for meta in rows.keys())
		items = tuple(self.serialize_items(conglom[self.items_header]) for conglom in rows.values())
		raw_addrs = tuple(conglom[self.raw_addr_header] for conglom in rows.values())
		wechat_ids = tuple(conglom[self.wechat_header] for conglom in rows.values())
		return metas,items,raw_addrs,wechat_ids

	def serialize_items(self,item_dict):
		item_strs = ''
		for item,quantity in item_dict.items():
			item_strs += item + ' x ' + str(quantity) + '\n'
		return item_strs.strip()

	def __str__(self):
		o = ''
		for compound in self.by_compound.keys():
			o += compound + '\n'
			o += '----------------\n'
			for meta in self.by_compound[compound]:
				o += meta.ljust(20)+':'+str(self.by_compound[compound][meta]['商品合计'])+', '+str(self.by_compound[compound][meta]['备用地址'])+'\n'
			o += '\n'
		return o

import pandas as pd
from os import listdir

stats = Stats()
sheets = listdir('sheets')
for sheet in sheets:
	orders = pd.read_excel('sheets/'+sheet)
	orders.dropna(inplace=True)
	for r in range(len(orders)):
		order = Order(str(orders['微信昵称'][r]),str(orders['收货地址'][r]),str(orders['商品合计'][r]))
		stats.process_stats(order)

with pd.ExcelWriter('output.xlsx') as writer:
	for compound in stats.get_compounds():
		metas,items,raw_addrs,wechat_ids = stats.get_columns(compound)
		df = pd.DataFrame(list(zip(metas,items,raw_addrs,wechat_ids)),columns=['收货地址','商品合计','备用地址','微信昵称'])
		df.to_excel(writer, sheet_name = compound,index=False)

	workbook = writer.book
	formats = workbook.add_format({'text_wrap':True,'align':'center','valign':'vcenter'})
	for worksheet in writer.sheets:
		writer.sheets[worksheet].set_column('A:D', 50, formats)
writer.close()