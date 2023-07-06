from mongo import *

class AdminCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    # !issue mov 1 150
    @commands.command(name='issue')
    async def issue(self, ctx : commands.Context, stock, quantity, amount):
        if ctx.author.id != 529785952982532117: return

        stocks = [Stock.load(stock)] if stock != 'ALL' else Stock.all()

        for stock in stocks:
            offer = stock.OfferOrder(float(amount), int(quantity), MARKET)
            stock.sell_offers.append(offer)
            stock.update()

        await ctx.reply(f'Issued stocks.')
    
    @commands.command(name='resetmarket')
    async def resetalluserdata(self, ctx : commands.Context, quantity = 10, amount = 150):
        col_stocks.update_many({}, { '$set': { 'owners': [], 'sell_offers': [{ 'amount': amount, 'quantity': quantity, 'user': MARKET }], 'buy_orders': [] } })
        col_stocks.update_many({}, { '$set': { 'transactions': [] }})
        col_users.delete_many({})
    
    @commands.Cog.listener(name='on_ready')
    async def on_ready(self):
        await (await self.bot.fetch_user(529785952982532117)).send('BOT IS ONLINE!')




def setup(bot):
    bot.add_cog(AdminCog(bot))