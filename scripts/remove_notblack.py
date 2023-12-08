from PIL import Image
import os

# Input file name
input_file = "24bitmap.bmp"

# Generate the output file name by appending "2mono" to the input file name
output_file = os.path.splitext(input_file)[0] + "_removeblack.bmp"

# Open the image using Pillow
image = Image.open(input_file)

# Convert the image to grayscale
image = image.convert("L")

# Convert the grayscale image to monochrome (1-bit)
image = image.point(lambda x: 0 if x < 30 else 255, '1')

# Save the monochrome BMP with the generated output file name
image.save(output_file)

print(f"{input_file} converted to monochrome and saved as {output_file}")