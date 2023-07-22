from bmp085 import BMP085
import time

sensor = BMP085(
    i2cChannel = 1,
    slaveAddress = 0x77
)

while True:
    sensor.getNewData()
    
    temprature = sensor.getTemprature()

    pressure = sensor.getPressure()

    print(
        "temprature：{}℃\npressure；{}hPa"
        .format(
            temprature,
            pressure
        )
    )

    time.sleep(10)