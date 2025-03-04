import RPi.GPIO as GPIO

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

# L298N motor kontrolü için GPIO pinleri
motor_pins = [17, 27, 24, 18]
enable_pins = [22, 23]

GPIO.setup(motor_pins, GPIO.OUT)
GPIO.setup(enable_pins, GPIO.OUT)

GPIO.output(motor_pins, GPIO.LOW)

# PWM ayarı (1 kHz); başlangıç duty cycle 0
pwm_ena = GPIO.PWM(enable_pins[0], 1000)
pwm_enb = GPIO.PWM(enable_pins[1], 1000)
pwm_ena.start(0)
pwm_enb.start(0)

def start_rotation_right(pwm_value):
    """
    Sağ dönüş için motor kontrolü.
    Sol motor ileri, sağ motor geri çalıştırılarak araç sağa döner.
    """
    GPIO.output(17, GPIO.HIGH)  # IN1
    GPIO.output(27, GPIO.LOW)   # IN2
    GPIO.output(24, GPIO.LOW)   # IN3
    GPIO.output(18, GPIO.HIGH)  # IN4
    pwm_ena.ChangeDutyCycle(pwm_value)
    pwm_enb.ChangeDutyCycle(pwm_value)

def stop_motors():
    """Tüm motorları durdurur."""
    GPIO.output(motor_pins, GPIO.LOW)
    pwm_ena.ChangeDutyCycle(0)
    pwm_enb.ChangeDutyCycle(0)

def move_forward(pwm_value):
    """Aracı düz ileri hareket ettir."""
    GPIO.output(17, GPIO.HIGH)  # IN1
    GPIO.output(27, GPIO.LOW)   # IN2
    GPIO.output(24, GPIO.HIGH)  # IN3
    GPIO.output(18, GPIO.LOW)   # IN4
    pwm_ena.ChangeDutyCycle(pwm_value)
    pwm_enb.ChangeDutyCycle(pwm_value)

def cleanup():
    """Modül kapanırken PWM'leri durdur ve GPIO temizle."""
    pwm_ena.stop()
    pwm_enb.stop()
    GPIO.cleanup()
