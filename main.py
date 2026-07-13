import logging
import os
import time

from PIL import Image, ImageDraw, ImageFont

from lib.waveshare_epd import epd7in5b_V2

logging.basicConfig(level=logging.DEBUG)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def main():
    try:
        epd = epd7in5b_V2.EPD()
        logging.info("init and Clear")
        epd.init()
        epd.Clear()

        logging.info("Displaying name")
        Himage = Image.new("1", (epd.width, epd.height), 255)
        draw = ImageDraw.Draw(Himage)

        font = ImageFont.truetype(os.path.join(BASE_DIR, "fonts", "HennyPenny-Regular.ttf"), 72)

        line1 = "Arkadip"
        line2 = "Bhattacharya"
        spacing = 10

        bbox1 = draw.textbbox((0, 0), line1, font=font)
        bbox2 = draw.textbbox((0, 0), line2, font=font)
        w1, h1 = bbox1[2] - bbox1[0], bbox1[3] - bbox1[1]
        w2, h2 = bbox2[2] - bbox2[0], bbox2[3] - bbox2[1]

        total_height = h1 + spacing + h2
        y1 = (epd.height - total_height) // 2
        y2 = y1 + h1 + spacing

        draw.text(((epd.width - w1) // 2, y1), line1, font=font, fill=0)
        draw.text(((epd.width - w2) // 2, y2), line2, font=font, fill=0)

        # Draw a cat at the bottom right
        cat_x = epd.width - 120
        cat_y = epd.height - 120

        # Cat head
        draw.ellipse([cat_x + 20, cat_y + 20, cat_x + 80, cat_y + 80], outline=0, fill=255, width=2)

        # Cat ears
        draw.polygon([cat_x + 25, cat_y + 30, cat_x + 20, cat_y + 10, cat_x + 35, cat_y + 25], outline=0, fill=255)
        draw.polygon([cat_x + 65, cat_y + 25, cat_x + 80, cat_y + 10, cat_x + 75, cat_y + 30], outline=0, fill=255)

        # Cat eyes
        draw.ellipse([cat_x + 35, cat_y + 40, cat_x + 42, cat_y + 47], fill=0)
        draw.ellipse([cat_x + 58, cat_y + 40, cat_x + 65, cat_y + 47], fill=0)

        # Cat nose
        draw.polygon([cat_x + 50, cat_y + 55, cat_x + 47, cat_y + 60, cat_x + 53, cat_y + 60], fill=0)

        # Cat whiskers
        draw.line([cat_x + 20, cat_y + 55, cat_x + 5, cat_y + 50], fill=0, width=1)
        draw.line([cat_x + 20, cat_y + 60, cat_x + 5, cat_y + 60], fill=0, width=1)
        draw.line([cat_x + 80, cat_y + 55, cat_x + 95, cat_y + 50], fill=0, width=1)
        draw.line([cat_x + 80, cat_y + 60, cat_x + 95, cat_y + 60], fill=0, width=1)

        # Draw funky decorations on the sides
        # Stars on the left
        for i in range(3):
            star_y = 100 + i * 120
            draw.polygon([
                20, star_y,
                25, star_y + 15,
                40, star_y + 15,
                28, star_y + 24,
                32, star_y + 40,
                20, star_y + 30,
                8, star_y + 40,
                12, star_y + 24,
                0, star_y + 15,
                15, star_y + 15
            ], outline=0, fill=255, width=2)

        # Circles on the right
        for i in range(3):
            circle_y = 80 + i * 100
            draw.ellipse([epd.width - 50, circle_y, epd.width - 20, circle_y + 30], outline=0, width=2)
            draw.ellipse([epd.width - 43, circle_y + 7, epd.width - 27, circle_y + 23], fill=0)

        # Top border decoration
        for i in range(0, epd.width, 60):
            draw.arc([i, 5, i + 40, 35], 0, 180, fill=0, width=2)

        Himage_Other = Image.new("1", (epd.width, epd.height), 255)

        epd.display(epd.getbuffer(Himage), epd.getbuffer(Himage_Other))
        time.sleep(2)

        logging.info("Goto Sleep...")
        epd.sleep()

    except IOError as e:
        logging.info(e)

    except KeyboardInterrupt:
        logging.info("ctrl + c:")
        epd7in5b_V2.epdconfig.module_exit(cleanup=True)


if __name__ == "__main__":
    main()
