from bmp085 import BMP085
import time

sensor = BMP085(
    i2cChannel = 1,
    slaveAddress = 0x77
)

while True:
    sensor.getNewData()
    
    temperature = sensor.getTemperature()

    pressure = sensor.getPressure()

    print(
        "temperature：{}℃\npressure；{}hPa"
        .format(
            temperature,
            pressure
        )
    )

    time.sleep(10)