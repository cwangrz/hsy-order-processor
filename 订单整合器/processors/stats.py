from constants import *

class Stats:
	def __init__(self):
		self.by_compound = {}
		self.order_raw_count = 0
		self.compound_count = 0
		self.order_combined_count = 0

	def process_stats(self,orders):
		for order in orders:
			raw_addr = order.addr.raw_addr
			compound = order.addr.compound
			meta = order.addr.meta
			wechat_id = order.wechat_id
			items = order.items
			if compound not in self.by_compound:
				self.compound_count += 1
			self.by_compound.setdefault(compound,{}).setdefault(meta,{}).setdefault(ITEMS_HEADER,{}).update(items.summary) #update items
			if RAW_ADDR_HEADER not in self.by_compound[compound][meta]:
				self.order_combined_count += 1
			self.by_compound[compound][meta][RAW_ADDR_HEADER] = raw_addr #update raw address
			self.by_compound[compound][meta][WECHAT_HEADER] = wechat_id
			self.order_raw_count += 1

	def get_compounds(self):
		assert len(self.by_compound) > 0
		return tuple(self.by_compound.keys())

	def get_cols_by_compound(self,compound):
		cols_dict = self.by_compound[compound]
		col_metas = tuple(' - '.join(meta.split(' ')) for meta in cols_dict.keys())
		col_items = []
		col_raw_addrs = []
		col_wechat_ids = []
		for conglom_dict in cols_dict.values():
			col_items.append(self.serialize_items(conglom_dict[ITEMS_HEADER]))
			col_raw_addrs.append(conglom_dict[RAW_ADDR_HEADER])
			col_wechat_ids.append(conglom_dict[WECHAT_HEADER])
		return [col_metas,tuple(col_items),tuple(col_raw_addrs),tuple(col_wechat_ids)]

	def serialize_items(self,item_dict):
		item_strs = ''
		for item,quantity in item_dict.items():
			item_strs += item + ' x ' + str(quantity) + '\n'
		return item_strs.strip()

	def print_stats(self):
		print(f'总订单数量:{self.order_raw_count}')
		print(f'配送数量:{self.order_combined_count}')
		print(f'小区数量:{self.compound_count}')