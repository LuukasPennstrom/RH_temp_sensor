import time
import board
import busio
import digitalio
import storage
import sdioio
import microcontroller
from analogio import AnalogIn
from adafruit_pcf8523.pcf8523 import PCF8523
import adafruit_ahtx0
import alarm

# Hardware Setup
i2c = board.I2C()
sensor = adafruit_ahtx0.AHTx0(i2c)
rtc = PCF8523(i2c)

# Safety check — warn but don't set, time must be set via set_time.py
if rtc.lost_power:
    t = rtc.datetime
    if t.tm_year < 2025:
        print("WARNING: RTC lost time! Run set_time.py")
    else:
        rtc.lost_power = False

# SD Card Setup (SDIO with retry)
sd = None
mounted = False
for attempt in range(5):
    try:
        sd = sdioio.SDCard(
            clock=board.SDIO_CLOCK,
            command=board.SDIO_COMMAND,
            data=board.SDIO_DATA,
            frequency=1000000
        )
        vfs = storage.VfsFat(sd)
        storage.mount(vfs, "/sd")
        mounted = True
        break
    except (ValueError, OSError):
        try:
            storage.umount("/sd")
        except:
            pass
        if sd:
            sd.deinit()
        sd = None
        time.sleep(0.5)

if not mounted:
    print("SD card failed after 5 attempts, going back to sleep")
    time_alarm = alarm.time.TimeAlarm(monotonic_time=time.monotonic() + 60)
    alarm.exit_and_deep_sleep_until_alarms(time_alarm)

# Device UID
raw_uid = microcontroller.cpu.uid
uid_str = "".join(f"{b:02x}" for b in raw_uid)
uid_short = uid_str[:8]

# Read time once — used for both filename and data
current_time = rtc.datetime

# Build log filename: /sd/YYYYMMDD_UID.txt
log_filename = (
    f"/sd/{current_time.tm_year:04d}{current_time.tm_mon:02d}{current_time.tm_mday:02d}"
    f"_{uid_short}.txt"
)

# New session write for log
if alarm.wake_alarm is None:
    try:
        with open(log_filename, "a") as log_file:
            log_file.write("\n--- NEW SESSION ---\n")
    except OSError as e:
        print(f"Session write failed: {e}")

# Voltage Reading
vbat_voltage = AnalogIn(board.VOLTAGE_MONITOR)
def get_voltage(pin):
    return (pin.value * 3.3) / 65536 * 2

# Main Logic
temperature = sensor.temperature
humidity = sensor.relative_humidity
battery_voltage = get_voltage(vbat_voltage)

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
time.sleep(3)
led.value = False

# Write Data to SD
try:
    with open(log_filename, "a") as log_file:
        log_file.write(data_line)
except OSError as e:
    print(f"Data write failed: {e}")

# Deep Sleep Calculation
current_seconds_in_hour = (current_time.tm_min * 60) + current_time.tm_sec
log_interval = 3600
seconds_past_interval = current_seconds_in_hour % log_interval
seconds_to_sleep = log_interval - seconds_past_interval

# Sleep
time_alarm = alarm.time.TimeAlarm(monotonic_time=time.monotonic() + seconds_to_sleep)
alarm.exit_and_deep_sleep_until_alarms(time_alarm)