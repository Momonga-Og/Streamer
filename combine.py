from PIL import Image
import io
import discord
import zipfile
import re

MAX_FILE_SIZE = 8 * 1024 * 1024  # 8 MB
MAX_DIMENSION = 65500  # Maximum supported image dimension

def extract_number(filename):
    match = re.search(r'\d+', filename)
    return int(match.group()) if match else float('inf')

async def combine_images(images):
    # Sort images based on numbers in their filenames
    images = sorted(images, key=lambda img: extract_number(img.filename))
    
    image_objects = [Image.open(io.BytesIO(await image.read())) for image in images]
    widths, heights = zip(*(img.size for img in image_objects))
    
    total_height = sum(heights)
    max_width = max(widths)
    
    if max_width > MAX_DIMENSION or total_height > MAX_DIMENSION:
        return split_and_combine_images(image_objects, max_width)
    
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

def split_and_combine_images(image_objects, max_width):
    part_index = 0
    y_offset = 0
    combined_images = []
    
    while image_objects:
        combined_image = Image.new('RGB', (max_width, MAX_DIMENSION))
        part_height = 0
        
        while image_objects and part_height + image_objects[0].height <= MAX_DIMENSION:
            img = image_objects.pop(0)
            combined_image.paste(img, (0, part_height))
            part_height += img.height
        
        byte_array = io.BytesIO()
        combined_image.crop((0, 0, max_width, part_height)).save(byte_array, format='PNG', optimize=True)
        byte_array.seek(0)
        combined_images.append((byte_array, part_index))
        part_index += 1
    
    return combined_images

def create_zip(combined_images):
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for byte_array, part_index in combined_images:
            zip_file.writestr(f"combined_image_part_{part_index}.jpg", byte_array.getvalue())
    zip_buffer.seek(0)
    return zip_buffer
