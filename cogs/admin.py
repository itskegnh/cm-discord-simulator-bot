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
        if ctx.author.id != 529785952982532117: return
        col_stocks.update_many({}, { '$set': { 'owners': [], 'sell_offers': [{ 'amount': amount, 'quantity': quantity, 'user': MARKET }], 'buy_orders': [] } })
        col_stocks.update_many({}, { '$set': { 'transactions': [] }})
        col_users.delete_many({})
    
    @commands.Cog.listener(name='on_ready')
    async def on_ready(self):
        await (await self.bot.fetch_user(529785952982532117)).send('BOT IS ONLINE!')
    
    @commands.command(name='market_pie')
    async def market_pie(self, ctx : commands.Context):
        if ctx.author.id != 529785952982532117: return
        stocks = Stock.all()

        # Calculate the total value of all stocks
        total_all_stocks_value = sum(stock.total_value() for stock in stocks)

        # Prepare data for the pie chart
        labels = []
        sizes = []
        for stock in stocks:
            stock_value = stock.total_value()
            market_share = stock_value / total_all_stocks_value
            labels.append(stock.id)  # Assuming stock has an 'id' attribute
            sizes.append(market_share)

        # Create the pie chart
        plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
        plt.axis('equal')  # Equal aspect ratio ensures a circular pie chart
        plt.title('Market Share by Stock')

        # Export the plot as an image
        image_stream = BytesIO()
        plt.savefig(image_stream, format='png')
        image_stream.seek(0)

        # Clear the plot for reuse
        plt.clf()

        await ctx.reply(file=disnake.File(image_stream))




def setup(bot):
    bot.add_cog(AdminCog(bot))