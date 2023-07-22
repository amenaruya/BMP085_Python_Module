# https://www.sparkfun.com/datasheets/Components/General/BST-BMP085-DS000-05.pdf

import time
from smbus2 import SMBus
# if you haven't installed this, 
# pip3 install smbus2

class BMP085:
# variable
    lReadData = []
    iAddress = 0xAA
    # Calibration Coefficients
    dictCCs: dict = {
        "iAC1": 0, "iAC2": 0, "iAC3": 0, "iAC4": 0, "iAC5": 0, "iAC6": 0,
        "iB1": 0, "iB2": 0, "iB3": 0, "iB4": 0, "iB5": 0, "iB6": 0, "iB7": 0,
        "iMB": 0, "iMC": 0, "iMD": 0
    }

# function
    def __init__(self, i2cChannel, slaveAddress) -> None:
        self.iI2CChannel = i2cChannel
        self.i2c = SMBus(bus = self.iI2CChannel)
        # I²C address
        self.iSlaveAddress = slaveAddress
    
# get data from bmp085
    def getNewData(self):
        # start：0xAA
        # end：0xBF
        while self.iAddress <= 0xBF:
            lData = self.i2c.read_i2c_block_data(
                i2c_addr = self.iSlaveAddress,
                register = self.iAddress,
                length = 1
            )

            # negative or not
            if ((self.iAddress < 0xB0 or self.iAddress > 0xB5) and self.iAddress % 2 == 0):
                if (lData[0] > 127):
                    lData[0] -= 256

            self.lReadData.append(lData[0])

            self.iAddress += 0x01
        
        self.__calculateCalibrationCoefficients()

    def __calculateCalibrationCoefficients(self):
        self.dictCCs["iAC1"] = (self.lReadData[0] << 8) + self.lReadData[1]
        self.dictCCs["iAC2"] = (self.lReadData[2] << 8) + self.lReadData[3]
        self.dictCCs["iAC3"] = (self.lReadData[4] << 8) + self.lReadData[5]
        self.dictCCs["iAC4"] = (self.lReadData[6] << 8) + self.lReadData[7]
        self.dictCCs["iAC5"] = (self.lReadData[8] << 8) + self.lReadData[9]
        self.dictCCs["iAC6"] = (self.lReadData[10] << 8) + self.lReadData[11]
        self.dictCCs["iB1"] = (self.lReadData[12] << 8) + self.lReadData[13]
        self.dictCCs["iB2"] = (self.lReadData[14] << 8) + self.lReadData[15]
        self.dictCCs["iMB"] = (self.lReadData[16] << 8) + self.lReadData[17]
        self.dictCCs["iMC"] = (self.lReadData[18] << 8) + self.lReadData[19]
        self.dictCCs["iMD"] = (self.lReadData[20] << 8) + self.lReadData[21]
    
# get temprature [℃]
    def __getUncompensatedTemperature(self):
        self.i2c.write_byte_data(
            i2c_addr = self.iSlaveAddress,
            register = 0xF4,
            value = 0x2E
        )

        time.sleep(0.0045)

        iMSB_UT = self.i2c.read_i2c_block_data(
            i2c_addr = self.iSlaveAddress,
            register = 0xF6,
            length = 1
        )[0]
        iLSB_UT = self.i2c.read_i2c_block_data(
            i2c_addr = self.iSlaveAddress,
            register = 0xF7,
            length = 1
        )[0]

        # Uncompensated Temperature
        iUT = (iMSB_UT << 8) + iLSB_UT

        return iUT
    
    def getTemprature(self):
        # get uncompensated temprature data
        iUT = self.__getUncompensatedTemperature()

        X1 = int(((iUT - self.dictCCs["iAC6"]) * self.dictCCs["iAC5"]) >> 15)
        X2 = int((self.dictCCs["iMC"] << 11) / (X1 + self.dictCCs["iMD"]))
        self.dictCCs["iB5"] = X1 + X2

        fTemperature = int((self.dictCCs["iB5"] + 8) >> 4) / 10

        return fTemperature

# get pressure [h㎩]
    def __getUncompensatedPressure(self):
        self.iSetting = 0
        # 0: ultralow power mode
        # 1: standard mode
        # 2: high resolution mode
        # 3: ultra high mode

        self.i2c.write_byte_data(
            i2c_addr = self.iSlaveAddress,
            register = 0xF4,
            value = 0x34 + (self.iSetting << 6)
        )

        time.sleep(0.0045)

        iMSB_UP = self.i2c.read_i2c_block_data(
            i2c_addr = self.iSlaveAddress,
            register = 0xF6,
            length = 1
        )[0]
        iLSB_UP = self.i2c.read_i2c_block_data(
            i2c_addr = self.iSlaveAddress,
            register = 0xF7,
            length = 1
        )[0]
        iXLSB_UP = self.i2c.read_i2c_block_data(
            i2c_addr = self.iSlaveAddress,
            register = 0xF8,
            length = 1
        )[0]

        # Uncompensated Pressure
        iUP = (((iMSB_UP << 16) + (iLSB_UP << 8) + iXLSB_UP) >> (8 - self.iSetting))

        return iUP
    
    def getPressure(self):
        iUP = self.__getUncompensatedPressure()

        self.dictCCs["iB6"] = (self.dictCCs["iB5"] - 4000)
        X1 = int((self.dictCCs["iB2"] * (self.dictCCs["iB6"] * self.dictCCs["iB6"] >> 12)) >> 11)
        X2 = int((self.dictCCs["iAC2"] * self.dictCCs["iB6"]) >> 11)
        X3 = X1 + X2
        self.dictCCs["iB3"] = int((((self.dictCCs["iAC1"] * 4 + X3) << self.iSetting) + 2) / 4)

        X1 = int((self.dictCCs["iAC3"] * self.dictCCs["iB6"]) >> 13)
        X2 = int((self.dictCCs["iB1"] * ((self.dictCCs["iB6"] * self.dictCCs["iB6"]) >> 12)) >> 16)
        X3 = int((X1 + X2 + 2) >> 2)
        self.dictCCs["iB4"] = int(self.dictCCs["iAC4"] * (X3+32768 ) >> 15)
        self.dictCCs["iB7"] = int((iUP - self.dictCCs["iB3"]) * (50000 >> self.iSetting))

        if self.dictCCs["iB7"] < 0x80000000:
            iPressure = int((self.dictCCs["iB7"] * 2) / self.dictCCs["iB4"])
        else:
            iPressure = int((self.dictCCs["iB7"] / self.dictCCs["iB4"]) * 2)

        X1 = int((iPressure >> 8) ** 2)
        X1 = int((X1 * 3038) >> 16)
        X2 = int((- 7357 * iPressure) >> 16)

        iPressure += int((X1 + X2 + 3791) >> 4)

        # [㎩] → [h㎩]
        return iPressure / 100.0