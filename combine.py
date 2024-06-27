from PIL import Image
import io
import discord

async def combine_images(images):
    image_objects = [Image.open(io.BytesIO(await image.read())) for image in images]
    widths, heights = zip(*(img.size for img in image_objects))
    
    total_height = sum(heights)
    max_width = max(widths)
    
    combined_image = Image.new('RGB', (max_width, total_height))
    y_offset = 0
    
    for img in image_objects:
        combined_image.paste(img, (0, y_offset))
        y_offset += img.height
    
    byte_array = io.BytesIO()
    combined_image.save(byte_array, format='PNG')
    byte_array.seek(0)
    
    return byte_array
