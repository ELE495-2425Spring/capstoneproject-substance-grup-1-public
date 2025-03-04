# TOBB ETÜ ELE495 - Capstone Project

# Table of Contents
- [Introduction](#introduction)
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Screenshots](#screenshots)
- [Acknowledgements](#acknowledgements)

## Introduction
This project focuses on developing a small autonomous vehicle prototype capable of detecting and homing in on a target RF (radio frequency) signal. The vehicle uses an SDR (Software Defined Radio) to identify the direction of the strongest signal, aligns itself accordingly using a PID-controlled gyroscope, and moves toward the signal source. Once it reaches a predefined proximity threshold, the vehicle stops. The entire process is monitored in real-time through a user interface, providing live feedback on the vehicle's position, signal strength, and movement.Traditional methods of locating RF signals often require manual intervention or expensive equipment. This project addresses these challenges by automating the process, enabling small, low-cost vehicles to autonomously detect and approach signal sources with high accuracy. The real-time monitoring interface further enhances usability, making it a practical tool for various applications.



## Features
### **Hardware Components**

The project utilizes the following hardware components:

### **Raspberry Pi 4**  
The main processing unit for running the control algorithms and interfacing with other components.  
[Raspberry Pi 4 Official Page](https://www.raspberrypi.org/products/raspberry-pi-4-model-b/)

### **L298N Motor Driver**  
Used to control the motors for movement and steering.  
[L298N Motor Driver Datasheet](https://www.st.com/resource/en/datasheet/l298.pdf)

### **MPU6050 Gyroscope and Accelerometer**  
Provides orientation and angular velocity data for precise movement control.  
[MPU6050 Datasheet](https://invensense.tdk.com/products/motion-tracking/6-axis/mpu-6050/)

### **RTL-SDR (Software Defined Radio)**  
Used for detecting and analyzing RF signals to determine the direction of the target signal.  
[RTL-SDR Overview](https://www.rtl-sdr.com/about-rtl-sdr/)

### **DC Motors**  
4 Motors drive the wheels of the vehicle for movement.

### **Power Supply**  
Provides power to the Raspberry Pi, motors, and other components.

### **Yagi Antenna**  
Specificly designd for 433MHz signal.
![WhatsApp Görsel 2025-03-04 saat 20 18 01_9a7b3627](https://github.com/user-attachments/assets/56c2e664-893d-43f8-a1b7-cee4644cb22c)


## Installation
### Project Setup and Execution
This project creates a signal homing system on a Raspberry Pi using the MPU6050 gyro sensor, RTL-SDR receiver, and L298N motor driver. The project is designed to find the strongest signal at a specific frequency and steer the vehicle in that direction.

![WhatsApp Görsel 2025-03-04 saat 20 48 31_fb0f18e1](https://github.com/user-attachments/assets/a1845dbd-c294-4dc1-babd-b25384cae38c)


### Prerequisites
Raspberry Pi (Model 3 or higher recommended)
Raspbian (or Raspberry Pi OS) installed
MPU6050 gyro sensor
RTL-SDR receiver
L298N motor driver and DC motors
Necessary wiring and connections
Dependencies
The following Python libraries need to be installed for the project to run:

smbus2: For I2C communication
numpy: For numerical operations
RPi.GPIO: To control GPIO pins
rtlsdr: To control the RTL-SDR receiver
Use the following commands to install these libraries:

```Bash

sudo apt-get update
sudo apt-get install python3-smbus i2c-tools
sudo pip3 install smbus2 numpy RPi.GPIO pyrtlsdr
Installation Steps
Clone the Repository:
```
```Bash

git clone <repo_url>
cd <repo_directory>
Replace <repo_url> with the GitHub repository URL and <repo_directory> with the cloned directory name.
```
#### Hardware Connections:

Connect the MPU6050 sensor to the Raspberry Pi's I2C pins.
Connect the RTL-SDR receiver to the Raspberry Pi's USB port.
Connect the L298N motor driver and DC motors to the Raspberry Pi's GPIO pins.
Ensure the connections are correct.
Running the Code:

To run the project, use the following command:

```Bash

sudo python3 main.py
```
This command will calibrate the gyro sensor and SDR, perform a 360° scan, find the angle with the strongest signal, and steer the vehicle in that direction.

Signal Data File:

The signal data obtained during the scan is saved to the signal_data.txt file. This file contains the signal strength at each angle.

#### Additional Notes
The calibration times for the gyro sensor and SDR may vary depending on environmental conditions.
The PID control parameters (kp, ki, kd) and motor PWM values can be adjusted to optimize the vehicle's behavior.
The signal strength threshold (48.0 dB) should be adjusted according to the signal source strength and environmental conditions.
Using sudo when running the code is necessary for accessing GPIO pins.
You can stop the program by pressing Ctrl+C while the code is running.


## Usage
#### 1. Check Hardware Connections
Before running the project, ensure that all hardware connections are correctly made. Verify that the MPU6050 sensor, RTL-SDR receiver, and L298N motor driver are properly connected to the Raspberry Pi.

#### 2. Open Terminal and Navigate to Project Directory
Open a terminal on your Raspberry Pi and navigate to the project directory. For example, if the project is in a directory named signal_homing, use the following command:

```Bash

cd signal_homing
```
#### 3. Run the Project
To start the project, use the following command:

```Bash

sudo python3 main.py
```
This command will calibrate the gyro sensor and SDR, perform a 360° scan, find the angle with the strongest signal, and steer the vehicle in that direction.

#### 4. Monitor Calibration Processes
Once the project starts, calibration processes for the gyro sensor and SDR will begin. You can monitor the progress and results of the calibration processes in the terminal.
```
Gyro (X ekseni) kalibrasyonu yapılıyor... Lütfen sensörü hareketsiz tutun. (10 saniye)
Gyro kalibrasyonu tamamlandı. Offset: -0.0234 °/s

SDR sinyal kalibrasyonu yapılıyor... Lütfen ortam sessiz kalsın. (10 saniye)
Sinyal kalibrasyonu tamamlandı. Baseline dBm: 41.12 dBm

Kalibrasyonlar tamamlandı. Araç 10 saniye bekleyecek...
```
#### 5. Monitor 360° Scan Process
After calibration is complete, the vehicle will start a 360° scan. It will stop every 15° and measure the signal strength. You can monitor the progress of the scan process and the measured signal strengths in the terminal.
```
360° tarama başlatılıyor. (Çıkmak için Ctrl+C)

İterasyon 1: Hedef döndürme: 15.00°
PID rotasyon tamamlandı: 15.02° (Hedef: 15.00°)
Güncel açı: 15.02°
15.00° boyunca ölçülen ortalama dBm: 41.54 dBm

İterasyon 2: Hedef döndürme: 15.00°
PID rotasyon tamamlandı: 30.01° (Hedef: 15.00°)
Güncel açı: 30.01°
30.00° boyunca ölçülen ortalama dBm: 42.12 dBm

```
#### 6. Monitor Turn to Strongest Signal Direction
After the 360° scan is complete, the vehicle will turn to the angle with the strongest signal. You can monitor the progress of this turn in the terminal.
```
En yüksek sinyal: 39.87 dBm, Açı: 180.05°

Araç en yüksek sinyalin bulunduğu 180.05° açısına dönüyor...
PID rotasyon tamamlandı: 180.03° (Hedef: 175.00°)
```
#### 7. Straight Movement and Signal Monitoring
After turning to the strongest signal direction, the vehicle will start moving straight. The signal strength will be continuously monitored during movement. You can see the current signal strength in the terminal.
```
Araç düz hareket ediyor...
Mevcut Sinyal Gücü: 45.23 dB
Mevcut Sinyal Gücü: 45.56 dB
Mevcut Sinyal Gücü: 47.12 dB
46 dB sinyal gücü algılandı! Araç duruyor...
```
#### 8. Review Signal Data File
The signal data obtained during the scan is saved to the signal_data.txt file. You can review this file to see the signal strength at each angle.
```
15.02, 44.54
30.01, 45.12
45.03, 45.89
...
9. Stop the Program
To stop the program, press Ctrl+C in the terminal.
```
#### Additional Notes
You can modify the PID control parameters and motor PWM values to optimize the vehicle's behavior.
Adjust the signal strength threshold (46.0 dB) according to the signal source strength and environmental conditions.
Using sudo when running the code is necessary for accessing GPIO pins.
The scan step (15°) and sampling times can be adjusted based on your application's requirements.

## Screenshots
Here are some screenshots of the project in action to give a visual representation of its functionality.
![WhatsApp Görsel 2025-03-04 saat 17 54 19_957e1602](https://github.com/user-attachments/assets/1648fbea-08fc-4193-9cf3-e280c1c7bb3a)

Here you can see the code on the run:https://youtu.be/CCXCw5RzqFc?si=u4j-X_F-LWBFjULp 

## Acknowledgements
This project has been inspired and developed through various resources and contributions.


