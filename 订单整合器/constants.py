#constats.py

'''This module defines some global constants mainly column headers'''

'''Excel Column Headers'''
WECHAT_HEADER = '微信昵称'
ITEMS_HEADER = '商品合计'
RAW_ADDR_HEADER = '收货地址'
BACKUP_ADDR_HEADER = '备用地址'
META_HEADER = '收货地址'

'''Excel Cell Formats'''
TEXT_WRAP = True
ALIGN = 'center'
VALIGN = 'vcenter'
FONT_NAME = 'Microsoft YaHei'
FONT_SIZE = '20'


'''IO'''
WORKBOOK_FOLDER = '输入表格'
OUTPUT_FOLDER = '输出表格'
COL_HEADERS = [META_HEADER,ITEMS_HEADER,BACKUP_ADDR_HEADER,WECHAT_HEADER]
TOTAL_COLS = len(COL_HEADERS)