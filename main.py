import logging
import time

from PIL import Image, ImageDraw, ImageFont

from lib.waveshare_epd import epd7in5b_V2

logging.basicConfig(level=logging.DEBUG)


def main():
    try:
        epd = epd7in5b_V2.EPD()
        logging.info("init and Clear")
        epd.init()
        epd.Clear()

        logging.info("Displaying name")
        Himage = Image.new("1", (epd.width, epd.height), 255)
        draw = ImageDraw.Draw(Himage)

        # font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)

        line1 = "Arkadip"
        line2 = "Bhattacharya"
        spacing = 10

        bbox1 = draw.textbbox((0, 0), line1)
        bbox2 = draw.textbbox((0, 0), line2)
        w1, h1 = bbox1[2] - bbox1[0], bbox1[3] - bbox1[1]
        w2, h2 = bbox2[2] - bbox2[0], bbox2[3] - bbox2[1]

        total_height = h1 + spacing + h2
        y1 = (epd.height - total_height) // 2
        y2 = y1 + h1 + spacing

        draw.text(((epd.width - w1) // 2, y1), line1, fill=0)
        draw.text(((epd.width - w2) // 2, y2), line2, fill=0)

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
