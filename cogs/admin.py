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
            offer = stock.OfferOrder(amount, quantity, MARKET)
            stock.sell_offers.append(offer)
            stock.update()

        await ctx.reply(f'Issued stocks.')



def setup(bot):
    bot.add_cog(AdminCog(bot))