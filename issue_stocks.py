from mongo import *

# print(millify(103.00))

col_stocks.update_many({}, { '$set': { 'owners': [], 'sell_offers': [{ 'amount': 150, 'quantity': 10, 'user': MARKET }], 'buy_orders': [] } })
col_stocks.update_many({}, { '$set': { 'transactions': [] }})
col_users.delete_many({})