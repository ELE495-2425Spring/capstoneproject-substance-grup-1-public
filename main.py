import time
import numpy as np
from rtlsdr import RtlSdr

# Kendi yazdığımız modüller
from mpu6050 import MPU6050, calibrate_gyro_x
from sdr_utils import calibrate_signal, get_signal_power
from motor import move_forward, stop_motors, cleanup
from scanning import scan_full_rotation, get_best_angle, rotate_by_angle_pid

def main():
    # 1) MPU6050 sensörünü başlat ve kalibre et
    sensor = MPU6050(address=0x68, bus_num=1)
    gyro_offset = calibrate_gyro_x(sensor, duration=10)

    # 2) SDR ayarları
    sdr = RtlSdr()
    sdr.sample_rate = 2.048e6
    sdr.center_freq = 433.92e6
    sdr.gain = 0

    # 3) SDR sinyal kalibrasyonu
    baseline = calibrate_signal(sdr, duration=10, sample_interval=0.1)

    # 4) 360° tarama ve veri kayıt
    print("Kalibrasyonlar tamamlandı. Araç 1 saniye bekleyecek...")
    time.sleep(1)
    signal_data = scan_full_rotation(
        sensor, gyro_offset, sdr,
        scan_step=15, max_duration=1.5,
        update_interval=0.01, sampling_duration=1.0, sampling_interval=0.1
    )

    # Ölçüm sonuçlarını bir dosyaya kaydet
    with open("signal_data.txt", "w") as f:
        for angle, power in signal_data:
            f.write(f"{angle:.2f}, {power:.2f}\n")

    # 5) En iyi açıya dön
    best_angle = get_best_angle(signal_data)
    if best_angle > 0:
        print(f"\nAraç en yüksek sinyalin bulunduğu {best_angle:.2f}° açısına dönüyor...")
        rotate_by_angle_pid(sensor, gyro_offset, target_angle=best_angle,
                            max_duration=5.0, update_interval=0.01, is_final_rotation=True)
    else:
        print("\nAraç zaten en iyi yönde (0°) konumlanmış.")

    # 6) Düz hareket ve sinyal kontrol
    print("\nAraç düz hareket ediyor...")
    move_forward(80)

    start_time = time.monotonic()
    while time.monotonic() - start_time < 10.0:  # Maksimum 10 saniye hareket
        signal_power = get_signal_power(sdr)
        print(f"Mevcut Sinyal Gücü: {signal_power:.2f} dB")

        if signal_power >= 46:
            print(f"46 dB sinyal gücü algılandı! Araç duruyor...")
            break

        time.sleep(0.10)  # 100 ms aralıklarla ölçüm yap

    stop_motors()
    sdr.close()

if __name__ == "__main__":
    try:
        main()
    finally:
        cleanup()
