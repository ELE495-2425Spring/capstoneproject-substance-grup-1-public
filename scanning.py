import time
import numpy as np
from pid_controller import PID
from motor import start_rotation_right, stop_motors, move_forward
from sdr_utils import get_signal_power

def rotate_by_angle_pid(sensor, gyro_offset, target_angle, max_duration=1.5, update_interval=0.01, is_final_rotation=False):
    """
    PID kontrolü ile aracı belirtilen target_angle kadar döndürür.
    Eğer is_final_rotation True ise, hedef açıya 5° kala durur.
    """
    integrated_angle = 0.0
    last_time = time.monotonic()
    previous_rate = sensor.get_gyro_x() - gyro_offset
    start_time = time.monotonic()

    pid = PID(kp=30, ki=0.1, kd=5, setpoint=target_angle)
    min_pwm = 45
    max_pwm = 80
    current_pwm = max_pwm
    start_rotation_right(current_pwm)

    # Eğer son dönüş ise, hedef açıya 5° kala dur
    stop_threshold = 5 if is_final_rotation else 0

    while integrated_angle < (target_angle - stop_threshold) and (time.monotonic() - start_time) < max_duration:
        current_time = time.monotonic()
        dt = current_time - last_time
        last_time = current_time

        current_rate = sensor.get_gyro_x() - gyro_offset
        integrated_angle += 0.5 * (previous_rate + current_rate) * dt
        previous_rate = current_rate

        pid_output = pid.update(integrated_angle, dt)
        new_pwm = max(min_pwm, min(max_pwm, pid_output))
        # Burada motorun PWM değerini değiştir
        start_rotation_right(new_pwm)

        time.sleep(update_interval)

    stop_motors()
    print(f"PID rotasyon tamamlandı: {integrated_angle:.2f}° (Hedef: {target_angle - stop_threshold}°)")
    return integrated_angle

def sample_signal_at_stop(sdr, duration=1.0, sample_interval=0.1):
    """
    Hareket durduğunda, belirtilen süre boyunca SDR ile sinyal gücü ölçümü yapar
    ve ortalama dBm değerini döndürür.
    """
    samples = []
    start = time.monotonic()
    while time.monotonic() - start < duration:
        samples.append(get_signal_power(sdr))
        time.sleep(sample_interval)
    return np.mean(samples)

def scan_full_rotation(sensor, gyro_offset, sdr, scan_step=15, max_duration=1.5,
                       update_interval=0.01, sampling_duration=1.0, sampling_interval=0.1):
    """
    Araç, 360°'yi geçmeden taramayı tamamlar ve her adımda sinyal ölçümü yapar.
    """
    total_angle = 0.0
    iteration = 0
    signal_data = []  # (açı, ortalama dBm)
    print("360° tarama başlatılıyor. (Çıkmak için Ctrl+C)")

    while total_angle < 360:  # 360°'yi geçmeden taramayı tamamla
        iteration += 1
        remaining_angle = 360 - total_angle  # Kalan açı
        step_angle = scan_step if remaining_angle >= scan_step else remaining_angle
        print(f"\nİterasyon {iteration}: Hedef döndürme: {step_angle:.2f}°")

        angle = rotate_by_angle_pid(
            sensor, gyro_offset, target_angle=step_angle,
            max_duration=max_duration, update_interval=update_interval
        )
        total_angle += angle
        current_angle = total_angle % 360
        print(f"Güncel açı: {current_angle:.2f}°")

        # Eğer 355° ile 360° arasındaysa, dönüşü tamamla
        if 355 <= current_angle <= 360:
            print("355° ile 360° arasında, dönüş tamamlanıyor.")
            break

        avg_dBm = sample_signal_at_stop(sdr, duration=sampling_duration, sample_interval=sampling_interval)
        print(f"{step_angle:.2f}° boyunca ölçülen ortalama dBm: {avg_dBm:.2f} dBm")
        signal_data.append((current_angle, avg_dBm))

    return signal_data

def get_best_angle(signal_data):
    """
    Kayıtlı sinyal verileri arasından en yüksek dBm değerine sahip açı tespit edilir.
    """
    best_angle, best_power = max(signal_data, key=lambda x: x[1])
    print(f"\nEn yüksek sinyal: {best_power:.2f} dBm, Açı: {best_angle:.2f}°")
    return best_angle
