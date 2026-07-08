import logging
import time

from PIL import Image, ImageDraw

from lib.waveshare_epd import epd7in5b_V2

logging.basicConfig(level=logging.DEBUG)


def main():
    try:
        epd = epd7in5b_V2.EPD()
        logging.info("init and Clear")
        epd.init()
        epd.Clear()

        logging.info("Drawing X pattern to mark center")
        Himage = Image.new("1", (epd.width, epd.height), 255)
        draw = ImageDraw.Draw(Himage)

        draw.line((0, 0, epd.width - 1, epd.height - 1), fill=0, width=2)
        draw.line((epd.width - 1, 0, 0, epd.height - 1), fill=0, width=2)

        # second layer (red channel on B model) left blank
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
