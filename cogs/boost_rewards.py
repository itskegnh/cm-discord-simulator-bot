from mongo import *

# sort methods:
#  • net worth
#  • pixels
#  • cells owned
#  • 

class BoostCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener(name='on_message')
    async def on_boost(self, message : disnake.Message):
        if message.channel.id != BOOST_CHANNEL: return
        # if not (message.type in [
        #     disnake.MessageType.premium_guild_subscription,
        #     disnake.MessageType.premium_guild_tier_1,
        #     disnake.MessageType.premium_guild_tier_2,
        #     disnake.MessageType.premium_guild_tier_3,
        # ]): return

        user = User.load(message.author.id)
        user.pixels += BOOST_REWARD

        user.recieved_reward = True

        user.update()

        try:
            await message.author.send(f'Thank you for boosting {message.author.mention}! I have given you an extra `${BOOST_REWARD}` as a thank you :smiling_face_with_3_hearts:')
        except Exception: ...
    
    @commands.command(name='claimreward')
    async def claimreward(self, ctx : commands.Context):
        if ctx.author.premium_since is None: return

        user = User.load(ctx.author.id)

        if user.recieved_reward: return

        user.pixels += BOOST_REWARD
        user.recieved_reward = True
        user.update()

        await ctx.reply(f'Thank you for boosting {ctx.author.mention}! I have given you an extra `${BOOST_REWARD}` as a thank you :smiling_face_with_3_hearts:')



def setup(bot):
    bot.add_cog(BoostCog(bot))