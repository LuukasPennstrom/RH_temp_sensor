import time
import board
import busio
import digitalio
import storage
import adafruit_sdcard
from analogio import AnalogIn
# Keeping your current working import path:
from adafruit_pcf8523.pcf8523 import PCF8523
import adafruit_ahtx0
import alarm

# Hardware Setup
i2c = board.I2C()
sensor = adafruit_ahtx0.AHTx0(i2c)
rtc = PCF8523(i2c)

if rtc.lost_power:
    print("RTC lost power, time is not set!")

sd_cs = digitalio.DigitalInOut(board.D10)
sd_cs.switch_to_output(value=True)
spi = board.SPI()
sd_card = adafruit_sdcard.SDCard(spi, sd_cs)
vfs = storage.VfsFat(sd_card)
storage.mount(vfs, "/sd")

# New session write for log
if alarm.wake_alarm is None:
    with open("/sd/log.txt", "a") as log_file:
        # Adds a blank line and a separator to make the log readable
        log_file.write("\n--- NEW SESSION ---\n")


vbat_voltage = AnalogIn(board.VOLTAGE_MONITOR)

def get_voltage(pin):
    return (pin.value * 3.3) / 65536 * 2

# Main Logic
temperature = sensor.temperature
humidity = sensor.relative_humidity
battery_voltage = get_voltage(vbat_voltage)
current_time = rtc.datetime

# Format Data
data_line = (
    f"{current_time.tm_year:04d}-{current_time.tm_mon:02d}-{current_time.tm_mday:02d}, "
    f"{current_time.tm_hour:02d}:{current_time.tm_min:02d}:{current_time.tm_sec:02d}, "
    f"{temperature:.2f}, {humidity:.2f}, {battery_voltage:.2f}\n"
)

# Flash LED
led = digitalio.DigitalInOut(board.LED)
led.direction = digitalio.Direction.OUTPUT
led.value = True
time.sleep(3) # 3s for indicating it is starting to write
led.value = False

# Write to SD
with open("/sd/log.txt", "a") as log_file:
    log_file.write(data_line)

# Deep Sleep
# Sleep for 900 seconds / 15 minutes (in reality, it's 897 + 3 s from the LED
time_alarm = alarm.time.TimeAlarm(monotonic_time=time.monotonic() + 897)
alarm.exit_and_deep_sleep_until_alarms(time_alarm)
