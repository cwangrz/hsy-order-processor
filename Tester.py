class Order:
	def __init__(self,wechat_id,raw_addr,raw_items):
		this.wechat_id = wechat_id
		this.addr = Address(raw_addr)
		this.items = Items(raw_items)

class Address:
	def __init__(self,raw_addr):
		self.raw_addr = raw_addr
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
		assert self.raw_addr
		#1.【general filters】- state, city, town, street names and 
		temp = self.raw_addr.strip()
		for f in self.general_filters:
			temp = temp.replace(f, '')
		
		#2.【punctionation filters】
		for p in self.punctuation_filters:
			temp = temp.replace(p, ' ')

		#3.【extra whitespace removal】
		temp = re.sub(' +',' ',temp)
		
		#4.【suffix delimiters】- for compound names including numerals or 南区/北区
		'''
			1.艾迪城菜鸟驿站 晨呐18511342908
				compound = ''
				meta = '艾迪城菜鸟驿站 晨呐18511342908'

			2.空港工业区B区三山新新家园菜鸟驿站
				compound = '空港工业区B区'
				meta = '三山新新家园菜鸟驿站'

			3.空港工业区B区三山新新家园十一号楼七单元501
				compound = '空港工业区B区'
				meta = '三山新新家园十一号楼七单元501'

			4.公园十七区北区1 1 401
				compound = '公园十七区北区'
				meta = '1 1 401'

			5.古城东大街12 2 电话:18311426087
				compound = ''
				meta = '古城东大街12 2 电话:18311426087'

			1.compound = ''   meta = '艾迪城菜鸟驿站 晨呐18511342908'
				compound = ''   meta = '艾迪城菜鸟驿站 晨呐18511342908'

			2.compound = '空港工业区B区'  meta = '三山新新家园菜鸟驿站'
				compound = '三山新新家园'   meta = '菜鸟驿站'

			3.compound = '空港工业区B区'  meta = '三山新新家园十一号楼七单元501'
				compound = '三山新新家园'  meta = '十一号楼七单元501'

			4.compound = '公园十七区北区'  meta = '1 1 401'
				compound = '公园十七区北区'  meta = '1 1 401'

			5.compound = ''   meta = '古城东大街12.2 电话:18311426087'
				compound = ''   meta = '古城东大街12 2 电话:18311426087'
		'''
		compound = None
		meta = temp
		for (suffix_delimiter,bound) in self.suffix_delimiters.items():
			tokens = meta.split(suffix_delimiter)
			assert len(tokens) <= bound
			if len(tokens) > 1:
				compound = suffix_delimiter.join(tokens[0:-1])+suffix_delimiter
			meta = tokens[-1]
		print('SUFFIX ROUND:',(compound,meta))

		#4.【prefix delimiters】- for meta without building/unit/room info such as '菜鸟驿站'
		'''
			1.compound = ''        meta = '艾迪城菜鸟驿站 晨呐18511342908'
				compound = '艾迪城'   meta = '菜鸟驿站 晨呐18511342908'

			2.compound = '空港工业区B区'  meta = '三山新新家园菜鸟驿站'
				compound = '三山新新家园'   meta = '菜鸟驿站'

			3.compound = '三山新新家园'  meta = '十一号楼七单元501'
				compound = '三山新新家园'  meta = '十一号楼七单元501'

			4.compound = '公园十七区北区'  meta = '1 1 401'
				compound = '公园十七区北区'  meta = '1 1 401'

			5.compound = ''   meta = '古城东大街12 2 电话:18311426087'
				compound = ''   meta = '古城东大街12 2 电话:18311426087'
		'''
		for prefix_delimiter in self.prefix_delimiters:
			if meta == prefix_delimiter: #if meta is only left with delimiter itself, then skip
				break
			tokens = meta.split(prefix_delimiter)
			assert len(tokens) <= 2
			if len(tokens) > 1:
				compound = tokens[0] #might overwrite result from previous attempt. but should be ok..?
				meta = prefix_delimiter+" "+tokens[-1]
				break
		print('PREFIX ROUND:',(compound,meta))

		#5.【chinese to arabic numeral】
		chinese_nums = ["二十","十九","十八","十七","十六","十五","十四","十三","十二","十一","十","九","八","七","六","五","四","三","二","一"]
		for cn in chinese_nums:
			meta = meta.replace(cn,str(20-chinese_nums.index(cn)))

		#6.【last resort】uses first numeric char as delimiter 
		'''
			1.compound = '艾迪城'   meta = '菜鸟驿站 晨呐18511342908'
				compound = '艾迪城'   meta = '菜鸟驿站 晨呐18511342908'
				
			2.compound = '三山新新家园'   meta = '菜鸟驿站'
				compound = '三山新新家园'   meta = '菜鸟驿站'

			3.compound = '三山新新家园'  meta = '十一号楼七单元501'
				compound = '三山新新家园'  meta = '十一号楼七单元501'

			4.compound = '公园十七区北区'  meta = '1 1 401'
				compound = '公园十七区北区'  meta = '1 1 401'

			5.compound = ''           meta = '古城东大街12 2 电话:18311426087'
				compound = '古城东大街'   meta = '12 2 电话:18311426087'
		'''
		if not compound:
			for i in range(len(meta)):
				if meta[i].isnumeric():
					compound = meta[0:i]
					meta = meta[i:]
					break
			print('FINAL ROUND:',(compound,meta))

		#7. clean up meta so that we only keep essential info
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

		#8.fill in legacy 公园十七区 orders. '北7 1 1' -> '公园十七区北区 7 1 1'
		if len(compound) == 1:
			compound = '公园十七区'+compound+'区'
		elif len(compound) == 2:
			compound = '公园十七区'+compound

		#8.output
		assert compound
		self.compound = compound
		self.meta = meta

class Items:
	def __init__(self,raw_items):
		self.raw_items = raw_items
		#{item name:quantity}
		self.quantities = {}
		self.entry_delimiter = '\n'
		self.quant_delimiter = '*'
		self.process()

	def process(self,raw_items = None):
		if not raw_items:
			assert self.raw_items
			raw_items = self.raw_items
		assert raw_items
		#raw format: '鸡蛋(30个)*1\n🇨🇱智利空运3J西梅👑(500g)*3\nxxxxxx*n\n'
		#1. split entries by entry_delimiter -> ['鸡蛋(30个)*1','🇨🇱智利空运3J西梅👑(500g)*3','xxxxxx*n']
		entries = raw_items.strip().split(self.entry_delimiter)
		assert entries
		#2. split item names and quantities by quant_delimiter -> {'鸡蛋(30个)':1,'🇨🇱智利空运3J西梅👑(500g)':3,'xxxxxx':n}
		#   NOTE: item name might contain delimiter.   'xxxxxx(500g*5)*3'  so here is only using last occurence
		for entry in entries:
			tokens = entry.split(self.quant_delimiter)
			item_name = self.quant_delimiter.join(tokens[0:-1]) #glue back item names that contain delimiters
			assert item_name
			item_quantity = int(tokens[-1])
			assert item_quantity and item_quantity > 0
			self.quantities[item_name] = self.quantities.get(item_name,0)+item_quantity

	def __str__(self):
		return str(self.quantities)

while True:
	raw_items = input("Items:")
	if raw_items == 'end':
		break
	items_obj = Items(raw_items)
	print(items_obj)

'''
#Tester
while True:
	addr = input("Addr:")
	print()
	if addr == "end":
		break
	addr_obj = Address(addr)
	print('Raw Addr:',addr_obj.raw_addr)
	addr_obj.process_addr()
	print('Clean Addr:',addr_obj.compound + " " + addr_obj.meta)
	print()
'''
