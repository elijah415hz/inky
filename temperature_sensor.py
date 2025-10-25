import board
import busio
import adafruit_pct2075

def get_inside_temperature():
    """
    Get temperature reading from the PCT2075 temperature sensor.
    Returns temperature in Fahrenheit.
    """
    try:
        i2c = busio.I2C(board.SCL, board.SDA)
        pct = adafruit_pct2075.PCT2075(i2c)
        celsius = pct.temperature
        fahrenheit = round((celsius * 1.8) + 32, 2)
        return fahrenheit
    except Exception as e:
        print(f"Error reading temperature sensor: {e}")
        return None
