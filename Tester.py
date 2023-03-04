class Order:
	def __init__(self,wechat_id,raw_addr,raw_items):
		self.wechat_id = wechat_id
		self.addr = Address(raw_addr)
		self.items = Items(raw_items)

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
		#print('SUFFIX ROUND:',(compound,meta))

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
		#print('PREFIX ROUND:',(compound,meta))

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
			#print('FINAL ROUND:',(compound,meta))

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

		#9.normalize all 公园十七区 namings
		compound = compound.replace('17','十七').replace('1区','北区').replace('一区','北区').replace('2区','南区').replace('二区','南区')

		#8.output
		assert compound
		self.compound = compound
		self.meta = meta

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
		self.process()

	def process(self):
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
			assert quantity and quantity > 0
			self.summary[item] = self.summary.get(item,0)+quantity

	def __str__(self):
		return str(self.summary)

class Stats:
	def __init__(self):
		self.by_compound = {}
		self.by_customer = {}
		self.by_item = {}

	def process(self,order):
		compound = order.addr.compound
		meta = order.addr.meta
		wechat_id = order.wechat_id
		items = order.items

		self.by_compound.setdefault(compound,{}).setdefault(meta,{}).update(items.summary)

	def __str__(self):
		o = ''
		for compound in self.by_compound.keys():
			o += compound + '\n'
			o += '----------------\n'
			for meta in self.by_compound[compound]:
				o += meta+':'+str(self.by_compound[compound][meta])+'\n'
				#self.by_compound[compound][meta] = str(self.by_compound[compound][meta])
			o += '\n'
		return o

'''
while True:
	raw_items = input("Items:")
	if raw_items == 'end':
		break
	items_obj = Items(raw_items)
	print(items_obj)
'''
'''
while True:
	addr = input("Addr:")
	print()
	if addr == "end":
		break
	print('Raw Addr:',addr)
	addr_obj = Address(addr)
	print('Clean Addr:',addr_obj)
	print()'''

order1 = Order('小宇💕[社会社会]','顺义区金地悦景台7号楼1单元806','葡萄柚(一箱)*1\n即食猕猴桃(一箱)*1\n')
order2 = Order('🍭Ms.S🍭','北京市顺义区后沙峪镇公园十七区南区一号楼三单元1202室','树熟贵妃芒🥭(500g)*1\n猫山王D197榴莲果肉无核(2盒)*1\n挖土豆🥔(210g)*2\n')
order3 = Order('August·崔','公园十七区南区6-1-702','挖土豆🥔(210g)*2\n')
order4 = Order('🍭Ms.S🍭','后沙峪国门智慧城8号楼518','葡萄柚(一箱)*1\n即食猕猴桃(一箱)*1\n')
order5 = Order('August·崔','公园十七区南区6-1-702','二次下单*1\n')
stats = Stats()
stats.process(order1)
stats.process(order2)
stats.process(order3)
stats.process(order4)
stats.process(order5)
print(stats)