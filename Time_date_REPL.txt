import board, time
from adafruit_pcf8523.pcf8523 import PCF8523
i2c = board.I2C()
rtc = PCF8523(i2c)
rtc.datetime = time.struct_time((2026, 1, 9, 13, 45, 0, 0, -1, -1))  # Set current time
