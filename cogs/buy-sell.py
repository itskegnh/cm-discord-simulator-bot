from mongo import *

class BuySellCog(commands.Cog):
    def __init__(self, bot : commands.Bot):
        self.bot = bot
    
    @commands.slash_command(name='buy', description='Buy a stock!', options=[
        disnake.Option(name='stock', description='The stock you want to purchase.', type=disnake.OptionType.string, required=True, choices=[
            disnake.OptionChoice(name=stock, value=stock) for stock in STOCKS
        ]),
        disnake.Option(name='quantity', description='Quantity of units to buy.', type=disnake.OptionType.integer, required=True, min_value=1),
        disnake.Option(name='amount', description='Maximum price per unit you are willing to spend. (tax is +10%)', type=disnake.OptionType.integer, required=True, min_value=1)
    ])
    async def buy(self, inter : disnake.interactions.AppCmdInter, stock, quantity, amount):
        if quantity <= 0:
            return await inter.response.send_message('You must buy atleast 1 unit!', ephemeral=True)
        
        if amount <= 0:
            return await inter.response.send_message('You must pay atleast `$1/unit`!', ephemeral=True)

        stock = Stock.load(stock)
        if stock is None:
            return await inter.response.send_message('That is not a valid stock!', ephemeral=True)
        
        user = User.load(str(inter.user.id))
        if user.pixels < quantity * amount:
            return await inter.response.send_message('You do not have enough pixels!', ephemeral=True)
        
        if user.pixels < user.add_gst(quantity * amount):
            return await inter.response.send_message('You do not have enough to afford GST (10%)!', ephemeral=True)

        await inter.response.defer(with_message=True)
        embeds = user.buy(stock, quantity, amount)
        
        for embed, user_id in embeds:
            embed.set_thumbnail(self.bot.get_user(int(user_id)).avatar.url)

        await send_embeds(inter, embeds)
    
    @commands.slash_command(name='sell', description='Sell a stock!', options=[
        disnake.Option(name='stock', description='The stock you want to offload.', type=disnake.OptionType.string, required=True, choices=[
            disnake.OptionChoice(name=stock, value=stock) for stock in STOCKS
        ]),
        disnake.Option(name='quantity', description='Quantity of units to sell.', type=disnake.OptionType.integer, required=True, min_value=1),
        disnake.Option(name='amount', description='Minimum price per unit you are willing to sell at.', type=disnake.OptionType.integer, required=True, min_value=1)
    ])
    async def sell(self, inter : disnake.interactions.AppCmdInter, stock, quantity, amount):
        if quantity <= 0:
            return await inter.response.send_message('You must sell atleast 1 unit!', ephemeral=True)
        
        if amount <= 0:
            return await inter.response.send_message('You must sell it at minimum `$1/unit`!', ephemeral=True)

        stock = Stock.load(stock)
        if stock is None:
            return await inter.response.send_message('That is not a valid stock!', ephemeral=True)
        
        user = User.load(str(inter.user.id))
        if stock.owners[user.id] < quantity:
            return await inter.response.send_message('You do not own enough of this stock!', ephemeral=True)

        await inter.response.defer(with_message=True)

        embeds = user.sell(stock, quantity, amount)
        
        for embed, user_id in embeds:
            embed.set_thumbnail(self.bot.get_user(int(user_id)).avatar.url)

        await send_embeds(inter, embeds)
        
    @commands.slash_command(name='cancel', description='Cancel all outgoing sell offers and buy orders.')
    async def cancel(self, inter : disnake.interactions.AppCmdInter):
        await inter.response.defer(with_message=True, ephemeral=True)
        
        user = User.load(inter.user.id)
        user.cancel_all()

        await inter.followup.send('You cancelled ALL outgoing sell offers and buy orders!')
    
    @tasks.loop(seconds=5.0)
    async def dividend_loop(self):
        pool = col_market.find_one({ '_id': 'DIVIDEND_POOL' })
        if pool['payout']+(60*60*24) > time.time(): return
        for user in User.all():
            if user.id != "529785952982532117": continue
            embeds = user.pay_dividends()

            if not user.dms: continue
            _user = await self.bot.fetch_user(int(user.id))
            await _user.send(embeds=embeds)
            await _user.send('If you would like to not recieve DMs, please use !dms-off')
        
        col_market.update_one({ '_id': 'DIVIDEND_POOL' }, { '$set': { 'amount': 0, 'payout': int(time.time()) } })
    
    @commands.command(name='dms-off')
    async def dms_off(self, ctx : commands.Context):
        user = User.load(ctx.author.id)
        user.dms = False
        user.update()

        await ctx.reply('I will stop sending you DMs!')

    @commands.command(name='dms-on')
    async def dms_on(self, ctx : commands.Context):
        user = User.load(ctx.author.id)
        user.dms = True
        user.update()

        await ctx.reply('I will send you DMs!')

            




    @commands.command(name='dividend')
    async def dividend(self, ctx : commands.Context):
        if ctx.author.id != 529785952982532117: return

        user = User.load(ctx.author.id)

        embeds = user.pay_dividends()

        await ctx.reply(embeds=embeds)

        # await send_embeds(inter, embeds)



def setup(bot):
    bot.add_cog(BuySellCog(bot))