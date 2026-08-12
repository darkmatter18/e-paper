from dotenv import load_dotenv

from display_clock import clock
from utils.log import configure_logging

load_dotenv()
configure_logging()

if __name__ == "__main__":
    clock()
