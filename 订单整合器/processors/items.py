class Items:
	def __init__(self,raw_items):
		self.raw_items = raw_items
		self.summary = {} #{item:quantity}
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