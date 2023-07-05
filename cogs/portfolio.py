from mongo import *

class PortfolioCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.slash_command(name='portfolio', description='View a user\'s stock portfolio.', options=[
        disnake.Option(name='user', description='Who\'s portfolio do you want to view?', type=disnake.OptionType.user)
    ])
    async def portfolio(self, inter : disnake.interactions.AppCmdInter, user = commands.Param(lambda inter: inter.user)):
        await inter.response.defer(with_message=True)

        embed = disnake.Embed(
            title = f'{user}\'s Portfolio',
            description = '',
            color = 0x2b2d31
        ).set_thumbnail(user.avatar.url)

        user = User.load(user.id)
        spent_pixels = user.spent_pixels()

        embed.description += f'Pixels: `${millify(user.pixels)}`' + (f' (`+${millify(spent_pixels)}`)' if spent_pixels > 0 else '')

        net_worth = user.pixels + spent_pixels

        for stock, (units_owned, units_for_sale) in user.portfolio():
            value = f'> **Units:** `{millify(units_owned)}`' + (f' (`+{millify(units_for_sale)}`)' if units_for_sale > 0 else '')
            value += f'\n> **Value:** `${millify(stock.get_value() * units_owned)}`'
            net_worth += stock.get_value() * units_owned

            embed.add_field(
                name = f'{stock.emoji} `{stock.id}`',
                value = value,
                inline = True,
            )

        embed.set_footer(text=f'Net Worth: ${millify(net_worth)}')
        # embed.set_image(file=disnake.File(stock.plot_sales_after(time.time() - 60*60*24*2), 'graph.png'))

        await inter.followup.send(embed=embed)
            

def setup(bot):
    bot.add_cog(PortfolioCog(bot))