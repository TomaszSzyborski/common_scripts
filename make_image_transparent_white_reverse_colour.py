from PIL import Image, ImageOps, ImageDraw


def add_alpha_to_PNG_image(file_name, save_as_output_png=False):
    image = Image.open(file_name)
    mask = Image.new('L', image.size, color=255)
    # draw = ImageDraw.Draw(mask)
    image.putalpha(mask)
    if save_as_output_png:
        image.save('output.png')
    return image


def make_white_transparent(img):
    img = img.convert("RGBA")
    datas = img.getdata()

    new_data = []
    for item in datas:
        if item[0] == 255 and item[1] == 255 and item[2] == 255:
            new_data.append((255, 255, 255, 0))
        else:
            new_data.append(item)

    img.putdata(new_data)
    # img.save("output.png", "PNG")
    return img


def reverse_image_colours(image):
    r, g, b, a = image.split()
    rgb_image = Image.merge('RGB', (r, g, b))
    inverted_image = PIL.ImageOps.invert(rgb_image)
    r2, g2, b2 = inverted_image.split()
    final_transparent_image = Image.merge('RGBA', (r2, g2, b2, a))
    return final_transparent_image


if __name__ == '__main__':
    import sys
    image = add_alpha_to_PNG_image(sys.argv[1])
    image = make_white_transparent(image)
    image = reverse_image_colours(image)
    image.save(sys.argv[2])
