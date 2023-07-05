import disnake
from disnake.ext import commands

from datetime import datetime

from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

import matplotlib.pyplot as plt
from matplotlib import dates as mdates
import numpy as np
import math
import statistics

from io import BytesIO

from collections import defaultdict

import time
import os


# Create a new client and connect to the server
client = MongoClient(os.getenv('URI'), server_api=ServerApi('1'))

db = client['market']

col_stocks = db['stocks']
col_users  = db['users']

STOCKS = [stock['_id'] for stock in col_stocks.find()]

MARKET = "1125298940200366080"
BOOST_REWARD = 500
GUILD_ID = 791818283867045941
BOOST_CHANNEL = 983204285712064593

# col_stocks.update_one({ '_id': 'MOV' }, { '$unset': { 'buy_orders': '' } })
# col_stocks.update_one({ '_id': 'MOV' }, { '$unset': { 'sell_offers': '' } })
# col_stocks.update_many({}, { '$set': { 'owners': [], 'buy_orders': [], 'sell_offers': [] } })
# col_stocks.update_one({ '_id': 'MOV' }, { '$set': { 'buy_orders': [] } })
# col_stocks.update_one({ '_id': 'MOV' }, { '$set': { 'sell_offers': [{ 'amount': 100, 'quantity': 10, 'user': MARKET }, { 'amount': 1000, 'quantity': 1, 'user': MARKET }] } })

# col_stocks.update_many({}, { '$unset': { 'sell_orders': '' } })
# col_stocks.update_many({}, { '$set': { 'transactions': [] } })
# col_stocks.update_one({ '_id': 'MOV' }, { '$push': { 'transactions': { 'buyer': '529785952982532117', 'seller': 'market', 'amount': 105, 'quantity': 2, 'timestamp': int(time.time()) } } })

# import random
# last_price = 100

# col_stocks.update_one({'_id': 'MOV'}, {'$set': {'transactions': []}})
# for i in range(10):
#     last_price += random.randint(-5, 20)
#     timestamp = int(time.time()) + i*random.randint(50, 200)
#     transaction = {
#         'buyer': '529785952982532117',
#         'seller': 'market',
#         'amount': last_price,
#         'quantity': random.randint(1, 5),
#         'timestamp': timestamp
#     }
#     col_stocks.update_one(
#         {'_id': 'MOV'},
#         {'$push': {'transactions': transaction}}
#     )
#     print(f"Inserted fake data for iteration {i+1}")


millnames = ['','k','m','b','t']

def millify(n):
    data = "QT,18|Q,15|T,12|B,9|M,6|k,3"
    for item in data.split("|"):
        s = item.split(",")
        if n >= 10 ** int(s[1]):
            return f"{round(n / (10 ** int(s[1])), 2)}{s[0]}"
    n = round(n, 2)
    if n == int(n):
        return str(int(n))
    else:
        return str(n)

# def millify(n):
#     n = float(n)
#     millidx = max(0,min(len(millnames)-1,
#                         int(math.floor(0 if n == 0 else math.log10(abs(n))/3))))

#     return '{:.0f}{}'.format(n / 10**(3 * millidx), millnames[millidx])

class Stock:
    class OfferOrder:
        def __init__(self, amount, quantity, user):
            self.amount = amount
            self.quantity = quantity
            self.user = user
        
        @classmethod
        def load(cls, offer_order):
            return cls(offer_order['amount'], offer_order['quantity'], offer_order['user'])
        
        def to_dict(self):
            if self.quantity <= 0:
                return None
            return {
                "amount": self.amount,
                "quantity": self.quantity,
                "user": self.user,
            }
    
    class Transaction:
        def __init__(self, buyer, seller, amount, quantity, timestamp = None):
            self.buyer = buyer
            self.seller = seller
            self.amount = amount
            self.quantity = quantity
            self.timestamp = timestamp if timestamp else int(time.time())
        
        @classmethod
        def load(cls, transaction):
            return cls(transaction["buyer"], transaction["seller"], transaction["amount"], transaction["quantity"], transaction["timestamp"])
        
        def to_dict(self):
            return {
                "buyer": self.buyer,
                "seller": self.seller,
                "amount": self.amount,
                "quantity": self.quantity,
                "timestamp": self.timestamp
            }

    def __init__(self, _id, name, emoji, owners, buy_orders, sell_offers, transactions):
        self.id = _id
        self.name = name
        self.emoji = emoji
        self.owners = defaultdict(int, owners)
        self.buy_orders = [self.OfferOrder.load(order) for order in buy_orders]
        self.sell_offers = [self.OfferOrder.load(offer) for offer in sell_offers]
        self.transactions = sorted([self.Transaction.load(transaction) for transaction in transactions], key=lambda t: t.timestamp, reverse=True)

        self.image = disnake.File(f'cells/{_id}.png')
    
    @classmethod
    def load(cls, _id):
        stock = col_stocks.find_one({ '_id': _id.upper() })
        if not stock:
            return None
        return cls(stock["_id"], stock["name"], stock["emoji"], stock["owners"], stock["buy_orders"], stock["sell_offers"], stock["transactions"])
    
    @classmethod
    def all(cls):
        stocks = col_stocks.find()
        for stock in stocks:
            yield cls(stock["_id"], stock["name"], stock["emoji"], stock["owners"], stock["buy_orders"], stock["sell_offers"], stock["transactions"])


    def to_dict(self):
        return {
            "_id": self.id,
            "name": self.name,
            "emoji": self.emoji,
            "owners": self.owners,
            "buy_orders": [o for o in [o.to_dict() for o in self.buy_orders] if o is not None],
            "sell_offers": [o for o in [o.to_dict() for o in self.sell_offers] if o is not None],
            "transactions": [t for t in [t.to_dict() for t in self.transactions] if t is not None]
        }
    
    def update(self):
        col_stocks.update_one({ '_id': self.id }, { '$set': self.to_dict() }, upsert=True)

    def get_value(self, timeframe=60*60*7):
        return statistics.median([transaction.amount for transaction in self.transactions_after(time.time() - timeframe)])

    def get_lastsale(self):
        if len(self.transactions) >= 1:
            return self.transactions[0].amount
        return -1
    
    def sorted_sell_offers(self):
        offers = defaultdict(int)

        for offer in self.sell_offers:
            offers[offer.amount] += offer.quantity
        
        offers = sorted([self.OfferOrder(k, v, None) for k, v in offers.items()], key=lambda o: o.amount)

        return offers
    
    def sorted_buy_orders(self):
        offers = defaultdict(int)

        for offer in self.buy_orders:
            offers[offer.amount] += offer.quantity
        
        offers = sorted([self.OfferOrder(k, v, None) for k, v in offers.items()], key=lambda o: o.amount, reverse=True)

        return offers
    
    def transactions_after(self, timespan):
        current_time = int(time.time())
        start_time = current_time - timespan

        transactions_after_timespan = []
        for transaction in self.transactions:
            if transaction.timestamp >= start_time:
                transactions_after_timespan.append(transaction)

        return sorted(transactions_after_timespan, key=lambda t: t.timestamp, reverse=True)

    def plot_sales_after(self, timestamp):
        timestamps = [transaction.timestamp for transaction in self.transactions]
        amounts = [transaction.amount for transaction in self.transactions]
        
        # Filter transactions after the given timestamp
        filtered_timestamps = []
        filtered_amounts = []
        for t, amount in zip(timestamps, amounts):
            if t >= timestamp:
                filtered_timestamps.append(t)
                filtered_amounts.append(amount)
        
        # Sort transactions by timestamp in ascending order
        sorted_indices = np.argsort(filtered_timestamps)
        sorted_timestamps = np.array(filtered_timestamps)[sorted_indices]
        sorted_amounts = np.array(filtered_amounts)[sorted_indices]
        
        # Convert timestamps to datetime objects
        datetimes = [datetime.utcfromtimestamp(t) for t in sorted_timestamps]

        # Create the line graph with scatter markers
        fig, ax = plt.subplots()
        ax.plot(datetimes, sorted_amounts)
        ax.set_xlabel("Time")
        ax.set_ylabel("Price")
        ax.set_title("Sales")

        ax.axhline(self.get_value(), color='gray', linestyle='--')

        # Set line colors based on direction
        for i in range(1, len(sorted_amounts)):
            if sorted_amounts[i] < sorted_amounts[i-1]:
                ax.plot([datetimes[i-1], datetimes[i]], [sorted_amounts[i-1], sorted_amounts[i]], color='red')
            else:
                ax.plot([datetimes[i-1], datetimes[i]], [sorted_amounts[i-1], sorted_amounts[i]], color='green')

        # Plot the scatter dots on top
        ax.scatter(datetimes, sorted_amounts, color='black', s=10, zorder=10)

        # Format x-axis as human-friendly timestamps
        date_fmt = mdates.DateFormatter('%b %d, %I%p')
        ax.xaxis.set_major_formatter(date_fmt)
        fig.autofmt_xdate()
        
        # Export the plot as an image
        image_stream = BytesIO()
        plt.savefig(image_stream, format='png')
        image_stream.seek(0)

        # Clear the plot for reuse
        plt.clf()

        return image_stream

class User:
    def __init__(self, _id, pixels, recieved_reward):
        self.id = _id
        self.pixels = pixels
        self.recieved_reward = recieved_reward
    
    @classmethod
    def load(cls, _id):
        _id = str(_id)
        user = col_users.find_one({ '_id': _id })
        if not user:
            pixels = 500
            user = { '_id': _id, 'pixels': pixels, 'recieved_reward': False }
            col_users.insert_one(user)
        return cls(user["_id"], user["pixels"], user["recieved_reward"])
    
    @classmethod
    def all(cls):
        users = col_users.find()
        for user in users:
            if user["_id"] == MARKET: continue
            yield cls(user["_id"], user["pixels"], user["recieved_reward"])

    def to_dict(self):
        return {
            "_id": self.id,
            "pixels": self.pixels,
            "recieved_reward": self.recieved_reward
        }
    
    def update(self):
        col_users.update_one({ '_id': self.id }, { '$set': self.to_dict() }, upsert=True)
    
    def gst(self, amount):
        return amount / 10
    
    def add_gst(self, amount):
        return amount + amount / 10

    def buy(self, stock, quantity, amount):
        if type(stock) == str: stock = Stock.load(stock)
        if self.add_gst(amount*quantity) > self.pixels: return

        sell_offers = sorted(stock.sell_offers, key=lambda o: o.amount)

        embeds = []

        while quantity > 0:
            if len(sell_offers) <= 0: break
            if sell_offers[0].amount > amount: break

            offer = sell_offers[0]
            offerer = User.load(offer.user)

            if offerer.id == self.id: 
                sell_offers.pop(0)
                continue

            transaction = None

            if offer.quantity <= quantity:
                stock.owners[self.id] += offer.quantity
                stock.sell_offers.remove(offer)
                sell_offers.pop(0)
                transaction = stock.Transaction(self.id, offerer.id, offer.amount, offer.quantity)
                self.pixels -= offer.amount * offer.quantity
                self.pixels -= self.gst(offer.amount * offer.quantity)
                offerer.pixels += offer.amount * offer.quantity
                quantity -= offer.quantity

            elif offer.quantity > quantity:
                stock.owners[self.id] += quantity
                offer.quantity -= quantity
                transaction = stock.Transaction(self.id, offerer.id, offer.amount, quantity)
                self.pixels -= offer.amount * quantity
                self.pixels -= self.gst(offer.amount * quantity)
                offerer.pixels += offer.amount * quantity
                quantity -= quantity
            
            stock.transactions.append(transaction)
            embeds.append((disnake.Embed(
                title = 'Transaction Complete',
                description = f'You bought **{millify(transaction.quantity)}x** {stock.emoji} from <@{transaction.seller}> @ `${millify(transaction.amount)}/unit`',
                color = 0x2b2d31
            ), offerer.id))
            
            offerer.update()

        if quantity > 0:
            # Place Buy Order
            order = stock.OfferOrder(amount, quantity, self.id)
            self.pixels -= amount * quantity
            self.pixels -= self.gst(amount * quantity)
            stock.buy_orders.append(order)

            embeds.append((disnake.Embed(
                title = 'Created Buy Order',
                description = f'You are now buying **{millify(quantity)}x** {stock.emoji} @ `${millify(amount)}/unit`',
                color = 0x2b2d31
            ), self.id))
        
        stock.update()
        self.update()

        return embeds
    
    def sell(self, stock, quantity, amount):
        if type(stock) == str: stock = Stock.load(stock)
        if stock.owners[self.id] < quantity: return

        buy_orders = sorted(stock.buy_orders, key=lambda o: o.amount)

        embeds = []

        while quantity > 0:
            if len(buy_orders) <= 0: break
            if buy_orders[0].amount < amount: break

            offer = buy_orders[0]
            offerer = User.load(offer.user)

            if offerer.id == self.id: 
                buy_orders.pop(0)
                continue

            transaction = None

            if offer.quantity <= quantity:
                stock.owners[self.id] -= offer.quantity # remove units from us
                self.pixels += offer.amount * offer.quantity # give us pixels

                stock.owners[offerer.id] += offer.quantity # give units to offerer

                stock.buy_orders.remove(offer) # delete order
                buy_orders.pop(0)

                transaction = stock.Transaction(offerer.id, self.id, offer.amount, offer.quantity) # create transaction

                quantity -= offer.quantity # change quantity

            elif offer.quantity > quantity:
                stock.owners[self.id] -= quantity # remove units from us
                self.pixels += offer.amount * quantity # give us pixels

                stock.owners[offerer.id] += quantity # give units to offerer

                stock.buy_orders.remove(offer) # delete order
                buy_orders.pop(0)
                
                transaction = stock.Transaction(offerer.id, self.id, offer.amount, quantity) # create transaction
                
                quantity -= quantity # change quantity
            
            stock.transactions.append(transaction)
            embeds.append((disnake.Embed(
                title = 'Transaction Complete',
                description = f'You sold **{millify(transaction.quantity)}x** {stock.emoji} to <@{transaction.buyer}> @ `${millify(transaction.amount)}/unit`',
                color = 0x2b2d31
            ), offerer.id))
            
            offerer.update()

        if quantity > 0:
            # Place Sell Offer
            order = stock.OfferOrder(amount, quantity, self.id)
            stock.owners[self.id] -= quantity
            stock.sell_offers.append(order)

            embeds.append((disnake.Embed(
                title = 'Created Sell Offer',
                description = f'You are now selling **{millify(quantity)}x** {stock.emoji} @ `${millify(amount)}/unit`',
                color = 0x2b2d31
            ), self.id))
        
        stock.update()
        self.update()

        return embeds
    
    def portfolio(self):
        for stock in Stock.all():
            units_owned = stock.owners[self.id]
            units_for_sale = 0
            for sell_offer in stock.sell_offers:
                if sell_offer.user == self.id:
                    units_for_sale += sell_offer.quantity

            if units_owned + units_for_sale > 0:
                yield stock, (units_owned, units_for_sale)
    
    def spent_pixels(self):
        pixels_spent = 0
        for stock in Stock.all():
            for buy_order in stock.buy_orders:
                if buy_order.user == self.id:
                    pixels_spent += buy_order.amount * buy_order.quantity
        self._spent_pixels = pixels_spent
        return pixels_spent
    
    def cancel_all(self):
        for stock in Stock.all():
            for buy_order in stock.buy_orders:
                if buy_order.user == self.id:
                    stock.buy_orders.remove(buy_order)
                    self.pixels += buy_order.amount * buy_order.quantity
                    self.pixels += self.gst(buy_order.amount * buy_order.quantity)
            for sell_offer in stock.sell_offers:
                if sell_offer.user == self.id:
                    stock.sell_offers.remove(sell_offer)
                    stock.owners[self.id] += sell_offer.quantity
            stock.update()
        self.update()