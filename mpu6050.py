import time
import numpy as np
from smbus2 import SMBus

class MPU6050:
    def __init__(self, address=0x68, bus_num=1):
        self.address = address
        self.bus = SMBus(bus_num)
        self.initialize_sensor()

    def initialize_sensor(self):
        # Sensörü uyandırmak için güç yönetimi register'ı (0x6B)'na 0 yazılır.
        self.bus.write_byte_data(self.address, 0x6B, 0)

    def read_word(self, reg):
        high = self.bus.read_byte_data(self.address, reg)
        low = self.bus.read_byte_data(self.address, reg + 1)
        val = (high << 8) + low
        if val >= 0x8000:
            return -((65535 - val) + 1)
        else:
            return val

    def get_gyro_x(self):
        # X ekseni ölçümü: 0x43 adresinden başlar; ±250°/s ölçeklendirme uygulanır.
        raw_gyro_x = self.read_word(0x43)
        return raw_gyro_x / 131.0

def calibrate_gyro_x(sensor, duration=10):
    """
    Gyro sensörün X ekseni için kalibrasyonu yapar.
    Sensör hareketsiz tutulduğunda, offset değeri hesaplanır.
    """
    print("Gyro (X ekseni) kalibrasyonu yapılıyor... Lütfen sensörü hareketsiz tutun. (10 saniye)")
    import time

    samples = []
    start_time = time.monotonic()
    while time.monotonic() - start_time < duration:
        samples.append(sensor.get_gyro_x())
        time.sleep(0.01)
    offset = np.mean(samples)
    print(f"Gyro kalibrasyonu tamamlandı. Offset: {offset:.4f} °/s\n")
    return offset
