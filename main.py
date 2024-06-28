from datetime import datetime
import time
from typing import TYPE_CHECKING
import schedule
import uvicorn
import requests
import threading
import sys
import gzip

import os
from dotenv import load_dotenv
load_dotenv()






if __name__ == "__main__":
        
    print("Launching uvicorn.")
    uvicorn.run("api:app", host="0.0.0.0", port=5000)
        