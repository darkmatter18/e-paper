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

        # Load fonts once
        try:
            time_font = ImageFont.truetype(os.path.join(BASE_DIR, "fonts", "HennyPenny-Regular.ttf"), 120)
            date_font = ImageFont.truetype(os.path.join(BASE_DIR, "fonts", "HennyPenny-Regular.ttf"), 40)
        except Exception:
            time_font = ImageFont.load_default()
            date_font = ImageFont.load_default()

        # Full image for initial display and periodic refresh
        full_image = Image.new("1", (epd.width, epd.height), 255)
        draw_full = ImageDraw.Draw(full_image)

        # Draw static elements once (border and date)
        draw_full.rectangle([10, 10, epd.width - 10, epd.height - 10], outline=0, width=3)

        # Red channel layer (static decorations)
        red_image = Image.new("1", (epd.width, epd.height), 255)
        draw_red = ImageDraw.Draw(red_image)

        # Corner decorations in red (static)
        for corner_x in [30, epd.width - 50]:
            for corner_y in [30, epd.height - 50]:
                draw_red.ellipse([corner_x, corner_y, corner_x + 20, corner_y + 20], fill=0)

        # Initialize for partial updates
        epd.init_part()

        last_time_str = ""
        last_date_str = ""
        last_minute = -1
        update_count = 0

        while True:
            now = datetime.now()
            time_str = now.strftime("%H:%M:%S")
            date_str = now.strftime("%A, %B %d, %Y")

            # Do a full refresh every minute or when date changes
            if now.minute != last_minute or date_str != last_date_str:
                logging.info("Full refresh - minute changed")

                # Re-initialize for full refresh
                epd.init()

                # Redraw everything
                full_image = Image.new("1", (epd.width, epd.height), 255)
                draw_full = ImageDraw.Draw(full_image)
                draw_full.rectangle([10, 10, epd.width - 10, epd.height - 10], outline=0, width=3)

                # Calculate positions
                time_bbox = draw_full.textbbox((0, 0), time_str, font=time_font)
                time_w = time_bbox[2] - time_bbox[0]
                time_h = time_bbox[3] - time_bbox[1]
                time_x = (epd.width - time_w) // 2
                time_y = (epd.height - time_h) // 2 - 50

                draw_full.text((time_x, time_y), time_str, font=time_font, fill=0)

                date_bbox = draw_full.textbbox((0, 0), date_str, font=date_font)
                date_w = date_bbox[2] - date_bbox[0]
                date_x = (epd.width - date_w) // 2
                date_y = time_y + time_h + 30

                draw_full.text((date_x, date_y), date_str, font=date_font, fill=0)

                # Update red channel with progress bar
                red_image = Image.new("1", (epd.width, epd.height), 255)
                draw_red = ImageDraw.Draw(red_image)

                for corner_x in [30, epd.width - 50]:
                    for corner_y in [30, epd.height - 50]:
                        draw_red.ellipse([corner_x, corner_y, corner_x + 20, corner_y + 20], fill=0)

                seconds = now.second
                bar_width = int((epd.width - 40) * (seconds / 60))
                draw_red.rectangle([20, epd.height - 30, 20 + bar_width, epd.height - 20], fill=0)

                epd.display(epd.getbuffer(full_image), epd.getbuffer(red_image))

                # Re-initialize for partial updates
                epd.init_part()

                last_minute = now.minute
                last_date_str = date_str
                last_time_str = time_str

            elif time_str != last_time_str:
                # Partial update for seconds only
                logging.info("Partial refresh - seconds changed")

                # Create a small image for just the time area
                time_bbox = draw_full.textbbox((0, 0), time_str, font=time_font)
                time_w = time_bbox[2] - time_bbox[0]
                time_h = time_bbox[3] - time_bbox[1]
                time_x = (epd.width - time_w) // 2
                time_y = (epd.height - time_h) // 2 - 50

                # Add padding to the update region
                padding = 10
                region_x = max(0, time_x - padding)
                region_y = max(0, time_y - padding)
                region_w = int(min(epd.width, time_w + 2 * padding))
                region_h = int(min(epd.height, time_h + 2 * padding))

                # Align region_x to 8-pixel boundary (required by display_Partial)
                region_x = (region_x // 8) * 8
                region_w = ((region_w + 7) // 8) * 8

                # Create partial image
                partial_image = Image.new("1", (region_w, region_h), 255)
                draw_partial = ImageDraw.Draw(partial_image)

                # Calculate text position within partial image
                text_x_offset = time_x - region_x
                text_y_offset = padding
                draw_partial.text((text_x_offset, text_y_offset), time_str, font=time_font, fill=0)

                # Convert partial image to buffer manually
                partial_image = partial_image.convert('1')
                buf = bytearray(partial_image.tobytes('raw'))
                # Invert bytes (PIL: 0=black, 1=white; e-paper: 0=white, 1=black)
                for i in range(len(buf)):
                    buf[i] ^= 0xFF

                epd.display_Partial(buf, region_x, region_y, region_x + region_w, region_y + region_h)

                last_time_str = time_str
                update_count += 1

                # Reset partial flag every 10 updates to avoid ghosting
                if update_count >= 10:
                    epd.partFlag = 1
                    update_count = 0

            time.sleep(1)

    except IOError as e:
        logging.info(e)

    except KeyboardInterrupt:
        logging.info("ctrl + c:")
        epd7in5b_V2.epdconfig.module_exit(cleanup=True)


if __name__ == "__main__":
    main()
