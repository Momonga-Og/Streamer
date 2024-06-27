from PIL import Image
import io
import discord

MAX_FILE_SIZE = 8 * 1024 * 1024  # 8 MB

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
    combined_image.save(byte_array, format='PNG', optimize=True)
    byte_array.seek(0)
    
    # Compress if the image is too large
    quality = 95  # Start with high quality
    while byte_array.getbuffer().nbytes > MAX_FILE_SIZE and quality > 10:
        byte_array = io.BytesIO()
        combined_image.save(byte_array, format='JPEG', quality=quality)
        byte_array.seek(0)
        quality -= 5
    
    # Resize if compression alone is not enough
    while byte_array.getbuffer().nbytes > MAX_FILE_SIZE:
        combined_image = combined_image.resize((combined_image.width // 2, combined_image.height // 2), Image.ANTIALIAS)
        byte_array = io.BytesIO()
        combined_image.save(byte_array, format='JPEG', quality=quality)
        byte_array.seek(0)
    
    return byte_array
