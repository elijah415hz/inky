from api import get_time_to_destination
import os
home_address = os.getenv('HOME_ADDRESS') or ""
met_address = os.getenv('MET_ADDRESS') or ""

print(f"Time to Misshattan: {get_time_to_destination(home_address, met_address)}")