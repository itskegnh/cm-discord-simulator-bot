from mongo import *

class StockCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.slash_command(name='stock', description='Inspect a stock, or the whole market.', options=[
        disnake.Option(name='stock', description='The stock to inspect - Leave blank to view all.', type=disnake.OptionType.string, required=False, autocomplete=True, )
    ])
    async def stock(self, inter : disnake.interactions.AppCmdInter, stock = None):
        if stock is None:
            await inter.response.defer(with_message=True)

            embed = disnake.Embed(
                title = 'CellMarket',
                description = '',
                color = 0x2b2d31
            )

            for stock in Stock.all():
                offers = stock.sorted_sell_offers()
                if len(offers) >= 1:
                    value = f'`${millify(offers[0].amount)}`'
                else:
                    value = '`-`'
                embed.add_field(
                    name = f'{stock.emoji} `{stock.id}`',
                    value = f'> **BIN:** {value}',
                    inline = True
                )

            embed.set_thumbnail(url=self.bot.user.avatar.url)
            
            return await inter.followup.send(embed=embed)
        
        stock = Stock.load(stock)
        if stock is None:
            return await inter.response.send_message('That is not a valid stock!', ephemeral=True)
        
        await inter.response.defer(with_message=True)

        embed = disnake.Embed(
            title = f'({stock.id}) {stock.name}',
            description = '',
            color = 0x2b2d31
        )

        embed.description += f'Value: `${millify(stock.get_value())}`\nLast Sale: `${millify(stock.get_lastsale())}`'

        embed.set_thumbnail(file=stock.image)

        value = ''

        for offer in stock.sorted_sell_offers():
            value += f'• `${millify(offer.amount)}` **x{millify(offer.quantity)}**\n'
        
        if value == '':
            value = ':spider_web: No Offers.'

        embed.add_field(
            name = 'Sell Offers',
            value = value,
            inline = True
        )

        value = ''

        for i, offer in enumerate(stock.sorted_buy_orders()):
            if i >= 3:
                value += '...'
                break
            value += f'• `${millify(offer.amount)}` **x{millify(offer.quantity)}**\n'
        
        if value == '':
            value = ':spider_web: No Orders.'

        embed.add_field(
            name = 'Buy Orders',
            value = value,
            inline = True
        )

        embed.set_image(file=disnake.File(stock.plot_sales_after(time.time() - 60*60*24*7), 'graph.png'))

        await inter.followup.send(embed=embed)
            

def setup(bot):
    bot.add_cog(StockCog(bot))