import board
import time
from adafruit_pcf8523.pcf8523 import PCF8523

i2c = board.I2C()
rtc = PCF8523(i2c)

# Force set time regardless of lost_power flag
rtc.datetime = time.struct_time((2026, 3, 11, 15, 42, 0, 0, -1, -1))  # UPDATE to current time
rtc.lost_power = False

t = rtc.datetime
print(f"RTC set to: {t.tm_year}-{t.tm_mon:02d}-{t.tm_mday:02d} {t.tm_hour:02d}:{t.tm_min:02d}:{t.tm_sec:02d}")

while True:
    time.sleep(1)