import disnake
from disnake.ext import commands
import cellmachine as cm
import io
from PIL import Image

class MainCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.slash_command(name='simulate')
    async def _simulate(self, inter : disnake.CommandInteraction, level : str, ticks : int, speed : bool = False):
        await inter.response.defer(with_message=True)
        try:
            level : cm.Level = cm.levelstring.import_level(level)
        except Exception as e:
            return await inter.followup.send('Failed to parse levelstring.')

        # limits

        images = []
        for i in range(ticks+1):
            image = level.preview()

            if image.mode == 'RGBA':
                # Create a solid background image with the desired color
                background = Image.new('RGB', image.size, (25, 25, 25))
                
                # Paste the original image on top of the background, using the alpha channel as a mask
                background.paste(image, (0, 0), image)
                
                # Replace the original image with the new composite
                image = background


            level.tick()
            
        
            images.append(image)
        
        gif_bytes = io.BytesIO()
        images[0].save(
            gif_bytes,
            format='GIF',
            append_images=images[1:],
            save_all=True,
            duration=1 if speed else 200,  # Duration between frames in milliseconds (adjust as needed)
            loop=0  # Set loop=0 for infinite loop, or any other number for a finite loop
        )
        gif_bytes.seek(0)
        
        await inter.followup.send(file=disnake.File(gif_bytes, filename='simulation.gif'))



def setup(bot):
    bot.add_cog(MainCog(bot))