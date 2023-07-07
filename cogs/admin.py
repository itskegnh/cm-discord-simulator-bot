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
        # Get the list of stocks
        stocks = Stock.all()


        # Calculate the market share for each stock and sort them in descending order
        shares = [(stock.id, stock.total_value() / Stock.all_stocks_value()) for stock in stocks]
        shares.sort(key=lambda x: x[1], reverse=True)

        # Prepare data for the progress bar-style chart
        labels = [share[0] for share in shares]
        sizes = [share[1] for share in shares]

        # Create the progress bar-style chart
        fig, ax = plt.subplots()
        ax.barh(range(len(labels)), sizes)

        # Customize the appearance of the chart
        ax.set_yticks(range(len(labels)))
        ax.set_yticklabels(labels)
        ax.set_xlabel('Market Share')
        ax.set_title('Market Share by Stock')

        # Export the plot as an image
        image_stream = BytesIO()
        plt.savefig(image_stream, format='png')
        image_stream.seek(0)

        # Clear the plot for reuse
        plt.clf()

        await ctx.reply(file=disnake.File(image_stream, 'graph.png'))




def setup(bot):
    bot.add_cog(AdminCog(bot))