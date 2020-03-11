#!/usr/bin/python
import RPi.GPIO as GPIO
import time
import os

# BCM GPIO-Referenen verwenden (anstelle der Pin-Nummern)
# und GPIO-Eingang definieren
GPIO.setmode(GPIO.BCM)
GPIO_PIR = 23

Command_OFF = './codesend 4462028 -l 198 -p 0'
Command_ON = './codesend 4462019 -l 198 -p 0'

print "PIR-Modul gestartet (CTRL-C to exit)"

# Set pin as input
GPIO.setup(GPIO_PIR,GPIO.IN)

# Initialisierung
Read  = 0
State = 0

try:
  print "Warten, bis PIR im Ruhezustand ist ..."

  # Schleife, bis PIR == 0 ist
  while GPIO.input(GPIO_PIR) != 0:
    time.sleep(0.1)
  print "Bereit..."
  os.system('cd /home/pi/');
  os.system(Command_OFF);

  # Endlosschleife, Ende mit STRG-C
  while True:
    # PIR-Status lesen
    Read = GPIO.input(GPIO_PIR)

    if Read == 1 and State == 0:
      # PIR wurde getriggert
      print "Bewegung erkannt!"
      os.system(Command_ON);
      # Zustand merken
      State = 1
    elif Read == 0 and State == 1:
      # PIR wieder im Ruhezustand
      print "Bereit..."
      os.system(Command_OFF);
      # Zustand merken
      State = 0

    # kleine Pause
    time.sleep(0.1)

except KeyboardInterrupt:
  # Programm beenden
  print "Ende..."
  GPIO.cleanup()

