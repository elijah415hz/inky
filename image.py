from PIL import Image, ImageDraw, ImageFont

# get an image
def make_image(text: str, bg_color=(0, 0, 0, 255)):
    # make a blank image for the text, initialized to transparent text color
    txt = Image.new("RGBA", [600, 448], bg_color)

    # get a font
    fnt = ImageFont.truetype("JosefinSans-Bold.ttf", 40)
    # get a drawing context
    d = ImageDraw.Draw(txt)

    # draw text, full opacity
    d.text((10, 60), text, font=fnt, fill=(255, 255, 255, 255))

    txt.show()

