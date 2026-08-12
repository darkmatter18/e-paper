from dotenv import load_dotenv

load_dotenv()

from display_clock import clock
from utils.log import configure_logging

configure_logging()

if __name__ == "__main__":
    clock()
