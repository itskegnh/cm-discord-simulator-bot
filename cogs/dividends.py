from mongo import *

class DividendCog(commands.Cog):
    def __init__(self, bot : commands.Bot):
        self.bot = bot
        self.dividend_loop.start()
    
    @tasks.loop(minutes=60.0)
    async def dividend_loop(self):
        pool = col_market.find_one({ '_id': 'DIVIDEND_POOL' })
        if pool['payout']+(60*60*24) > time.time(): return
        for user in User.all():
            # if user.id != "529785952982532117": continue
            embeds = user.pay_dividends()

            if not user.dms: continue
            if len(embeds) <= 0: continue
            
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

def setup(bot):
    bot.add_cog(DividendCog(bot))