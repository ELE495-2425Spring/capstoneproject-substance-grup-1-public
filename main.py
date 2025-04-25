import time
import numpy as np
from smbus2 import SMBus
import RPi.GPIO as GPIO
from rtlsdr import RtlSdr
import socket
import threading
import json

######################
# GLOBALS & SETTINGS
######################
SERVER_IP         = "10.5.64.137"
PORT              = 5000

robot_running     = False
operation_status  = "Idle"
current_direction = 0
current_spectrum  = 0

client_conn = None
conn_lock   = threading.Lock()

# SDR access must be serialized
sdr_global = None
sdr_lock   = threading.Lock()

######################
# COMMUNICATION
######################
def send_update_to_client(update):
    with conn_lock:
        if client_conn:
            client_conn.sendall((json.dumps(update) + "\n").encode())

######################
# SDR HELPERS
######################
def get_fft_data(n=256):
    global sdr_global
    try:
        with sdr_lock:
            samples = sdr_global.read_samples(n)
        spec = np.fft.fftshift(np.fft.fft(samples))
        return np.abs(spec)
    except:
        return np.array([])

def get_signal_power(sdr):
    vals = []
    for _ in range(3):
        try:
            with sdr_lock:
                samp = sdr.read_samples(1024 * 64)
        except OSError:
            continue
        spec = np.fft.fftshift(np.fft.fft(samp))
        ps = np.abs(spec)**2 + 1e-12
        vals.append(10 * np.log10(np.percentile(ps,99)))
    return np.mean(vals) if vals else current_spectrum

def calibrate_signal(sdr, dur=5, interval=0.2):
    send_update_to_client({"type":"status","status":"Calibrating SDR..."})
    arr = []
    start = time.monotonic()
    while time.monotonic() - start < dur:
        arr.append(get_signal_power(sdr))
        time.sleep(interval)
    base = np.mean(arr)
    send_update_to_client({"type":"status","status":f"SDR baseline: {base:.2f} dBm"})
    return base

######################
# GYRO HELPERS
######################
class MPU6050:
    def __init__(self, addr=0x68, busnum=1):
        self.bus = SMBus(busnum)
        self.bus.write_byte_data(addr, 0x6B, 0)
    def read_word(self, r):
        h = self.bus.read_byte_data(0x68, r)
        l = self.bus.read_byte_data(0x68, r+1)
        v = (h<<8)|l
        return v-65536 if v>=0x8000 else v
    def get_gyro_x(self):
        return self.read_word(0x43)/131.0

def calibrate_gyro_x(sensor, dur=5):
    send_update_to_client({"type":"status","status":"Calibrating gyro..."})
    xs=[]
    start=time.monotonic()
    while time.monotonic()-start<dur:
        xs.append(sensor.get_gyro_x())
        time.sleep(0.02)
    off=np.mean(xs)
    send_update_to_client({"type":"status","status":f"Gyro offset: {off:.4f}"})
    return off

######################
# MOTOR & PID SETUP
######################
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
motor_pins  = [17,27,24,18]
enable_pins = [22,23]
GPIO.setup(motor_pins, GPIO.OUT)
GPIO.setup(enable_pins, GPIO.OUT)
GPIO.output(motor_pins, GPIO.LOW)
pwm_ena=GPIO.PWM(enable_pins[0],1000); pwm_ena.start(0)
pwm_enb=GPIO.PWM(enable_pins[1],1000); pwm_enb.start(0)

class PID:
    def __init__(self,kp,ki,kd,setp=0):
        self.kp,self.ki,self.kd,self.setp=kp,ki,kd,setp
        self.I=0; self.last_e=0
    def update(self,x,dt):
        e=self.setp-x
        self.I+=e*dt
        d=(e-self.last_e)/dt if dt>0 else 0
        self.last_e=e
        return self.kp*e+self.ki*self.I+self.kd*d

def start_right(duty):
    GPIO.output(17,GPIO.HIGH); GPIO.output(27,GPIO.LOW)
    GPIO.output(24,GPIO.LOW);  GPIO.output(18,GPIO.HIGH)
    pwm_ena.ChangeDutyCycle(duty); pwm_enb.ChangeDutyCycle(duty)

def stop_all():
    GPIO.output(motor_pins, GPIO.LOW)
    pwm_ena.ChangeDutyCycle(0); pwm_enb.ChangeDutyCycle(0)

def rotate_by_angle_pid(sensor, off, tgt, maxd=1.5, upd=0.01, final=False):
    global robot_running
    ang=0.0
    lt=time.monotonic(); prev=time.monotonic()
    rate_prev=sensor.get_gyro_x()-off
    pid=PID(30,0.1,5,setp=tgt)
    start_right(80)
    thr = 5 if final else 0
    while ang < (tgt-thr) and (time.monotonic()-lt)<maxd and robot_running:
        now=time.monotonic(); dt=now-prev; prev=now
        rate=sensor.get_gyro_x()-off
        ang+=0.5*(rate_prev+rate)*dt; rate_prev=rate
        duty=max(45,min(80,pid.update(ang,dt)))
        pwm_ena.ChangeDutyCycle(duty); pwm_enb.ChangeDutyCycle(duty)
        time.sleep(upd)
    stop_all()
    msg=f"Rotasyon tamam: {ang:.2f} (Hedef {tgt-thr})"
    send_update_to_client({"type":"status","status":msg})
    return ang

def sample_stop(sdr,dur=1.,iv=0.1):
    arr=[]; s=time.monotonic()
    while time.monotonic()-s<dur:
        arr.append(get_signal_power(sdr))
        time.sleep(iv)
    return np.mean(arr)

def scan_full_rotation(sensor,off,sdr,step=15,maxd=1.5,upd=0.01,dur=1.,iv=0.1):
    total=0.0; idx=0; data=[]
    send_update_to_client({"type":"status","status":"Starting 360° scan"})
    while total<360 and robot_running:
        idx+=1
        s=step if (360-total)>=step else (360-total)
        send_update_to_client({"type":"status","status":f"Iter {idx}: {s:.1f}°"})
        turned=rotate_by_angle_pid(sensor,off,s,maxd,upd,False)
        total+=turned; angle=total%360
        send_update_to_client({"type":"operation","direction":angle})
        if 355<=angle<=360:
            send_update_to_client({"type":"status","status":"Finishing scan"})
            break
        avg=sample_stop(sdr,dur,iv)
        send_update_to_client({"type":"operation","spectrum":avg})
        data.append((angle,avg))
        global current_direction,current_spectrum
        current_direction,current_spectrum=angle,avg
    return data

def get_best_angle(data):
    b_ang,b_pw=max(data,key=lambda x:x[1])
    send_update_to_client({"type":"status","status":f"Best: {b_pw:.2f} @ {b_ang:.2f}°"})
    return b_ang

######################
# LIVE UPDATE THREAD
######################
def live_update_thread():
    global robot_running,current_direction,current_spectrum,operation_status
    while robot_running:
        upd={
          "type":"live_update",
          "status":operation_status,
          "direction":current_direction,
          "spectrum":current_spectrum
        }
        fft=get_fft_data(256)
        upd["fft"]=fft.tolist() if fft.size else []
        send_update_to_client(upd)
        time.sleep(0.5)

######################
# MAIN OPERATION
######################
def run_robot_operation():
    global robot_running,sdr_global,operation_status
    robot_running=True

    sdr=RtlSdr()
    with sdr_lock:
        sdr_global=sdr
        sdr.sample_rate=2.048e6
        sdr.center_freq=433.92e6
        sdr.gain=0

    sensor=MPU6050()
    off=calibrate_gyro_x(sensor,5)
    base=calibrate_signal(sdr,5,0.2)
    send_update_to_client({"type":"status","status":"Calibrations done"})
    time.sleep(1)

    lt=threading.Thread(target=live_update_thread,daemon=True)
    lt.start()

    for i in range(2):
        if not robot_running:
            break
        send_update_to_client({"type":"status","status":f"--- Scan {i+1} ---"})
        data=scan_full_rotation(sensor,off,sdr)
        with open(f"sigdata_{i+1}.txt","w") as f:
            for a,p in data: f.write(f"{a:.2f},{p:.2f}\n")

        best=get_best_angle(data)
        data_sorted = sorted(data, key=lambda x: x[0])
        angles = [d[0] for d in data_sorted]
        if best in angles:
            idx = angles.index(best)
            target_idx = max(0, idx - 1)
            adjusted_angle = angles[target_idx]
        else:
            adjusted_angle = best

        send_update_to_client({"type":"status","status":f"Turning to adjusted {adjusted_angle:.2f}"})
        rotate_by_angle_pid(sensor, off, adjusted_angle, 5, 0.01, True)

        if i==0:
            send_update_to_client({"type":"status","status":"Moving forward 5s"})
            GPIO.output(17,GPIO.HIGH);GPIO.output(27,GPIO.LOW)
            GPIO.output(24,GPIO.HIGH);GPIO.output(18,GPIO.LOW)
            pwm_ena.ChangeDutyCycle(80);pwm_enb.ChangeDutyCycle(80)
            start_time = time.monotonic()
            while time.monotonic() - start_time < 4 and robot_running:
                time.sleep(0.1)
            stop_all()
        else:
            send_update_to_client({"type": "status", "status": "Checking threshold"})
            threshold_reached = False
            start_time = time.monotonic()
            GPIO.output(17, GPIO.HIGH)
            GPIO.output(27, GPIO.LOW)
            GPIO.output(24, GPIO.HIGH)
            GPIO.output(18, GPIO.LOW)
            pwm_ena.ChangeDutyCycle(80)
            pwm_enb.ChangeDutyCycle(80)
            while time.monotonic() - start_time < 3 and robot_running:
                sp = get_signal_power(sdr)
                send_update_to_client({"type": "live_update", "spectrum": sp})
                if sp >= 34:
                    send_update_to_client({"type": "status", "status": "Threshold reached during movement"})
                    threshold_reached = True
                    break
                time.sleep(0.1)
            stop_all()

    robot_running=False
    lt.join()
    sdr.close()
    send_update_to_client({"type":"status","status":"Operation complete"})

######################
# SOCKET HANDLER
######################
def handle_client_commands(conn):
    global robot_running
    buf=""
    while True:
        data=conn.recv(1024).decode()
        if not data: break
        buf+=data
        while "\n" in buf:
            line,buf=buf.split("\n",1)
            try:
                msg=json.loads(line)
                if msg.get("command") == "start" and not robot_running:
                    threading.Thread(target=run_robot_operation, daemon=True).start()
                elif msg.get("command") == "stop":
                    robot_running = False
                    send_update_to_client({"type": "status", "status": "Manually stopped"})
            except: pass

def main():
    global client_conn
    srv=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    srv.bind((SERVER_IP,PORT)); srv.listen(1)
    print("Server started, waiting for client…")
    client_conn,addr=srv.accept()
    print("Client connected:",addr)
    threading.Thread(target=handle_client_commands,args=(client_conn,),daemon=True).start()
    try:
        while True: time.sleep(1)
    except KeyboardInterrupt: pass
    finally:
        srv.close()
        GPIO.cleanup()

if __name__=="__main__":
    main()
