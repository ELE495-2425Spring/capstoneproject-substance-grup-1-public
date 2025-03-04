import time
import numpy as np
from rtlsdr import RtlSdr

def get_signal_power(sdr):
    """
    SDR'den alınan örneklerle FFT hesaplaması yaparak,
    güç spektrumunun 99. yüzdelik diliminden dBm değerini hesaplar.
    """
    power_values = []
    for _ in range(5):
        samples = sdr.read_samples(1024 * 256)
        spectrum = np.fft.fftshift(np.fft.fft(samples))
        power_spectrum = np.abs(spectrum) ** 2
        power_values.append(10 * np.log10(np.percentile(power_spectrum, 99)))
    return np.mean(power_values)

def calibrate_signal(sdr, duration=10, sample_interval=0.1):
    """
    SDR sinyal kalibrasyonu yapar.
    10 saniyelik periyotla ölçüm alınarak ortalama baz (baseline) değeri hesaplanır.
    """
    print("SDR sinyal kalibrasyonu yapılıyor... Lütfen ortam sessiz kalsın. (10 saniye)")
    samples = []
    start = time.monotonic()
    while time.monotonic() - start < duration:
        samples.append(get_signal_power(sdr))
        time.sleep(sample_interval)
    baseline = np.mean(samples)
    print(f"Sinyal kalibrasyonu tamamlandı. Baseline dBm: {baseline:.2f} dBm\n")
    return baseline
