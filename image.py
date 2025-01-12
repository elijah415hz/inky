from PIL import Image, ImageDraw, ImageFont
import colorcet as cc

# get an image
def make_image(text: str, bg_color=(0, 0, 0, 255), text_color=(255, 255, 255, 255)):
    image = Image.new("RGBA", [600, 448], bg_color)

    # get a font
    # fnt = ImageFont.truetype("JosefinSans-Bold.ttf", 40)
    # get a drawing context
    d = ImageDraw.Draw(image)

    # draw text
    d.text((10, 20), text, fill=text_color)
    # draw a line
    d.line((0, 70, image.size[0], 70), fill=text_color, width=7)

    weather_img = Image.open('weather_image.png', 'r')
    image.paste(weather_img, (10, 70), mask=weather_img)


def get_color_from_gradient(value: int, range_min: int, range_max: int, gradient: list) -> tuple[int, int, int, int]:
    normalized_temp = (value - range_min) / (range_max - range_min)
    color = cc.coolwarm[int(normalized_temp * 255)]
    return color
