import disnake
from disnake.ext import commands

from io import BytesIO

from PIL import Image, ImageDraw, ImageFont

import random

from mongo import *


class Stock:

    width, height = 1600, 200

    unit = height
    gap = unit/4

    title_font = ImageFont.truetype("fonts/poppins-bold.ttf", 1.2*gap)
    text_font  = ImageFont.truetype("fonts/poppins-light.ttf", 0.8*gap)

    def __init__(self, icon, title, price, diff):
        self.icon = Image.open(icon).resize(
            [int( 3 * self.gap )] * 2
        )
        self.title = title
        self.price = f'{price}pix'
        if diff > 0:
            self.diff = f'+{diff}%'
            self.diff_color = (0, 155, 0)
        elif diff < 0:
            self.diff = f'-{abs(diff)}%'
            self.diff_color = (155, 0, 0)
        else:
            self.diff = f'-'
            self.diff_color = (155, 155, 155)
    
    def export_image(self, background_color):
        image = Image.new("RGBA", (self.width, self.height), background_color)
        draw = ImageDraw.Draw(image)

        image.paste(self.icon, [int(self.gap/2)]*2, self.icon)

        
        # draw the centered text title on the left.
        draw.text((self.unit, self.gap), self.title, (0, 0, 0, 255), self.title_font, anchor="lt")
        draw.text((self.unit, self.height-self.gap), self.price, (0, 0, 0, 255), self.text_font, anchor="lb")

        # draw price diff
        price_width = 250
        price_height = 100
        draw.rounded_rectangle((self.width - self.gap - price_width, self.height - self.gap - price_height, self.width - self.gap, self.height - self.gap), 10, self.diff_color)
        draw.text((self.width - price_width/2 - self.gap, self.unit/2), self.diff, (255, 255, 255), self.title_font, "mm")

        return image


class MarketCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name='market')
    async def market(self, inter : disnake.interactions.AppCmdInter):
        image = Image.new("RGBA", (Stock.width, Stock.height*9), (255, 255, 255))

        for i, (cell, acronym) in enumerate(zip([
            'Mover', 'Generator', 'CW Rotator', 'CCW Rotator', 'Slide', 'Push', 'Immobile', 'Trash', 'Enemy'
        ], ['MOV', 'GNE', 'CWR', 'CCW', 'SLD', 'PSH', 'IMB', 'TSH', 'NMY'])):

            image.paste(Stock(
                icon=f'cells/{cell}.png',
                title=f'{acronym} ({cell})',
                price=random.randint(0, 300),
                diff=random.randint(-20, 20),
            ).export_image((255, 255, 255) if i % 2 == 0 else (240, 240, 240)), (0, Stock.height*i))

        # Save the image
        image_bytes = BytesIO()
        image.save(image_bytes, format='PNG')
        image_bytes.seek(0)

        await inter.response.send_message(file=disnake.File(image_bytes, filename='market.png'))

def setup(bot):
    bot.add_cog(MarketCog(bot))