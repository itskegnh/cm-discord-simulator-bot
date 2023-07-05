from mongo import *

# sort methods:
#  • net worth
#  • pixels
#  • cells owned
#  • 

class LeaderboardCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.slash_command(name='leaderboard', description='See who has the most cells!')
    async def leaderboard(self, inter : disnake.interactions.AppCmdInter):
        await inter.response.defer(with_message=True)

        users = list(User.all())
        users = sorted(users, key=lambda u: u.pixels + u.spent_pixels(), reverse=True)
        
        embed = disnake.Embed(
            title = f'Leaderboard',
            description = '',
            color = 0x2b2d31
        )
        
        pos = -1
        for i, user in enumerate(users):
            if i < 10:
                embed.description += f'\n**{i+1}.** <@{user.id}> `${millify(user.pixels)}`' + (f' (`+${millify(user._spent_pixels)}`)' if user._spent_pixels > 0 else '')

            if user.id == str(inter.user.id):
                pos = i

        embed.set_thumbnail(url=self.bot.user.avatar.url)

        embed.set_footer(text=f'You are at position #{pos+1}.', icon_url=inter.user.avatar.url)

        await inter.followup.send(embed=embed)
            

def setup(bot):
    bot.add_cog(LeaderboardCog(bot))