from processors.addr import Address
from processors.items import Items

class Order:
	def __init__(self,wechat_id,raw_addr,raw_items):
		self.wechat_id = wechat_id
		self.addr = Address(raw_addr)
		self.items = Items(raw_items)