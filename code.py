import time
import board
import busio
import digitalio
import storage
import adafruit_sdcard
from analogio import AnalogIn
from adafruit_pcf8523.pcf8523 import PCF8523
import adafruit_ahtx0
import alarm

# Initialize I2C bus and devices
i2c = board.I2C()  # uses board.SCL and board.SDA

# Initialize temperature/humidity sensor (AHT20 via AHTx0 library)
sensor = adafruit_ahtx0.AHTx0(i2c)

# Initialize real-time clock (RTC) PCF8523
rtc = PCF8523(i2c)

# Check if the RTC lost power and might need time set
if rtc.lost_power:
    print("RTC lost power, time is not set!")  # Could set rtc.datetime here if needed

# Initialize SD card (SPI interface) and mount filesystem
sd_cs = digitalio.DigitalInOut(board.D10)       # SD card CS pin (D10 on Feather)
sd_cs.switch_to_output(value=True)              # Ensure CS is high before init
spi = board.SPI()                               # SPI bus (SCK, MOSI, MISO)
sd_card = adafruit_sdcard.SDCard(spi, sd_cs)    # Create SD card interface
vfs = storage.VfsFat(sd_card)                   # Create a FAT filesystem on the card
storage.mount(vfs, "/sd")                       # Mount the filesystem at "/sd"

# Set up battery voltage monitoring
vbat_voltage = AnalogIn(board.VOLTAGE_MONITOR)
def get_voltage(pin):
    """Helper to convert AnalogIn value to a voltage."""
    return (pin.value * 3.3) / 65536 * 2  # 3.3V reference, 16-bit ADC, 2x divider

# Read sensors and time
temperature = sensor.temperature
humidity = sensor.relative_humidity
battery_voltage = get_voltage(vbat_voltage)
current_time = rtc.datetime  # time.struct_time from the RTC

# Format a data line (CSV format: date, time, temperature, humidity, battery)
data_line = (
    f"{current_time.tm_year:04d}-{current_time.tm_mon:02d}-{current_time.tm_mday:02d}, "
    f"{current_time.tm_hour:02d}:{current_time.tm_min:02d}:{current_time.tm_sec:02d}, "
    f"{temperature:.2f}, {humidity:.2f}, {battery_voltage:.2f}\n"
)

led = digitalio.DigitalInOut(board.LED)
led.direction = digitalio.Direction.OUTPUT
led.value = True  # Turn on LED
time.sleep(10)    # Wait 10 seconds

# Append the data to the log file on the SD card
with open("/sd/log.txt", "a") as log_file:
    log_file.write(data_line)
    # File is closed automatically at the end of the with-block

led.value = False

# Schedule wake-up alarm for 15 minutes from now and enter deep sleep
now = rtc.datetime
next_wake = time.mktime(now) + 60
time_alarm = alarm.time.TimeAlarm(epoch_time=next_wake)
alarm.exit_and_deep_sleep_until_alarms(time_alarm)
