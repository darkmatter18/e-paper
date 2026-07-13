import logging
import os
import time
from datetime import datetime

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

        while True:
            logging.info("Updating clock")
            Himage = Image.new("1", (epd.width, epd.height), 255)
            draw = ImageDraw.Draw(Himage)

            # Get current time
            now = datetime.now()
            time_str = now.strftime("%H:%M:%S")
            date_str = now.strftime("%A, %B %d, %Y")

            # Load fonts
            try:
                time_font = ImageFont.truetype(os.path.join(BASE_DIR, "fonts", "HennyPenny-Regular.ttf"), 120)
                date_font = ImageFont.truetype(os.path.join(BASE_DIR, "fonts", "HennyPenny-Regular.ttf"), 40)
            except:
                time_font = ImageFont.load_default()
                date_font = ImageFont.load_default()

            # Draw time centered
            time_bbox = draw.textbbox((0, 0), time_str, font=time_font)
            time_w = time_bbox[2] - time_bbox[0]
            time_h = time_bbox[3] - time_bbox[1]
            time_x = (epd.width - time_w) // 2
            time_y = (epd.height - time_h) // 2 - 50

            draw.text((time_x, time_y), time_str, font=time_font, fill=0)

            # Draw date below time
            date_bbox = draw.textbbox((0, 0), date_str, font=date_font)
            date_w = date_bbox[2] - date_bbox[0]
            date_x = (epd.width - date_w) // 2
            date_y = time_y + time_h + 30

            draw.text((date_x, date_y), date_str, font=date_font, fill=0)

            # Draw decorative border
            draw.rectangle([10, 10, epd.width - 10, epd.height - 10], outline=0, width=3)

            # Red channel layer with seconds indicator
            Himage_Other = Image.new("1", (epd.width, epd.height), 255)
            draw_red = ImageDraw.Draw(Himage_Other)

            # Draw seconds as a progress bar at the bottom
            seconds = now.second
            bar_width = int((epd.width - 40) * (seconds / 60))
            draw_red.rectangle([20, epd.height - 30, 20 + bar_width, epd.height - 20], fill=0)

            # Corner decorations in red
            for corner_x in [30, epd.width - 50]:
                for corner_y in [30, epd.height - 50]:
                    draw_red.ellipse([corner_x, corner_y, corner_x + 20, corner_y + 20], fill=0)

            epd.display(epd.getbuffer(Himage), epd.getbuffer(Himage_Other))

            # Update every second
            time.sleep(1)

    except IOError as e:
        logging.info(e)

    except KeyboardInterrupt:
        logging.info("ctrl + c:")
        epd7in5b_V2.epdconfig.module_exit(cleanup=True)


if __name__ == "__main__":
    main()
