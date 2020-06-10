#!/usr/bin/python
# -*- coding: iso-8859-1 -*-

import RPi.GPIO as GPIO
import time
import os
import datetime
import argparse
import sys
import subprocess
import shlex

class TimedCommand:
  def __init__(self, command = 'irsend SEND_ONCE TWEEN_LIGHT KEY_GREEN', periods = '00:00-23:59', repeat = True, priority = 1, wakeup = False, name = ''):
    self.periods = periods
    self.command = command
    self.repeat = repeat
    self.priority = priority
    self.wakeup = wakeup
    self.name = name if name else command
  def isDue(self):
    periods = self.periods.split(",")
    match = 0
    for period in periods:
      if self.isTimeWithinRange(period):
        match = match + 1
    return match > 0
  def isTimeWithinRange(self, period):
    times = period.split("-")
    now = datetime.datetime.now()
    if len(times) == 1:
      t = self.createTimeFromString(times[0])
      if now.time()>=t.time() and now.time()<=(t + datetime.timedelta(seconds=60)).time():
        return True      
    else:
      t1 = self.createTimeFromString(times[0])
      t2 = self.createTimeFromString(times[1])
      if now.time()>t1.time() and now.time()<t2.time():
        return True
  def createTimeFromString(self, string):
    try:
      time = datetime.datetime.strptime(string, '%H:%M:%S')
    except ValueError:
      time = datetime.datetime.strptime(string, '%H:%M')
    return time

# these commands are only executed if a recent motion has been detected
timedCommands = [
  TimedCommand('irsend SEND_ONCE TWEEN_LIGHT KEY_RED', priority=5, repeat=False, name="Nachtruhe"), 
  TimedCommand('irsend SEND_ONCE TWEEN_LIGHT KEY_PURPLE','08:00-22:00', priority=4, repeat=False, name="Tageszeit"),
  TimedCommand('irsend SEND_ONCE TWEEN_LIGHT KEY_PINK','12:00-18:00', priority=3, repeat=False, name="Mahlzeit!"),
  TimedCommand('irsend SEND_ONCE TWEEN_LIGHT KEY_GREEN','15:15-15:30,18:00-18:03,18:12-18:15', priority=0, repeat=False, name="Test"),
  TimedCommand('irsend SEND_ONCE TWEEN_LIGHT KEY_POWER', '20:31', priority=0, repeat=False, wakeup=True, name="Aufwachen!")
]

# BCM GPIO-Referenen verwenden (anstelle der Pin-Nummern)
# und GPIO-Eingang definieren
GPIO.setmode(GPIO.BCM)
GPIO_PIR = 23

#Command_OFF = './codesend 4462028 -l 198 -p 0'
COMMAND_OFF = 'irsend SEND_ONCE TWEEN_LIGHT KEY_SUSPEND'
COMMAND_ON = 'irsend SEND_ONCE TWEEN_LIGHT KEY_POWER'

COMMAND_INIT = 'irsend SEND_ONCE TWEEN_LIGHT KEY_FLASH'

# Set pin as input
GPIO.setup(GPIO_PIR,GPIO.IN)

# Initialisierung
read  = 0
state = 0
verbosity = 2
logfileName = ""
lastTimedCommand = None
logfile = ""
mode = "a+"
intervalMotionDetection = 1
intervalTimedCommands = 5

# Make sure the timezone is set correctly (e.g. sudo timedatectl set-timezone Europe/Berlin)

def getCurrentTimestamp(format = "%Y-%m-%d %H:%M:%S"):
  return datetime.datetime.now().strftime(format)

def execute(command):
  global verbosity
  global log
  log("Executing Command: "+command+"...")
  args = shlex.split(command+" &")
  process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def log(message, level = 2):
  global verbosity
  global getCurrentTimestamp
  global logfile
  global mode
  if verbosity >= level:
    if logfileName:
        logfile = open(logfileName, mode)
        logfile.write("["+getCurrentTimestamp()+"]: "+message+"\n")
        logfile.close()
    else:
      print("["+getCurrentTimestamp()+"]: "+message)

def parseArguments():
  global verbosity
  global logfileName
  global logfile
  global mode
  global intervalMotionDetection, intervalTimedCommands
  # Construct the argument parser
  ap = argparse.ArgumentParser()

  # Add the arguments to the parser
  ap.add_argument("-v", "--verbosity", required=False, default='2',
     help="verbosity level. default: 2")
  ap.add_argument("-l", "--logfile", required=False,
     help="logfile name. if specified, all log messages will be written to the specified file instead of stdout. default: none")
  ap.add_argument("-m", "--mode", required=False, nargs='?', default='a+', 
     help="open logfile in specified file mode (use w+ to create new file and overwrite existing messages). default: a+ (append)")
  ap.add_argument("-o", "--overwrite", required=False, nargs='?', const='w+', default='',
     help="open logfile and overwrite existing messages (uses w+ when opening log file)")
  ap.add_argument('-c', "--interval_commands", required=False, nargs='?', const=5, default=5,
     help="specifies the refreshment interval for timed commands. default: 5 seconds")
  ap.add_argument('-i', "--interval_detection", required=False, nargs='?', const=1, default=1,
     help="specifies the motion detection interval. default: 1 second")

  args = vars(ap.parse_args())

  if args['interval_commands']:
    intervalTimedCommands = args['interval_commands'];

  if args['interval_detection']:
    intervalMotionDetection = args['interval_detection']

  if args['verbosity']:
    verbosity = int(args['verbosity'])

  if args['logfile']:
    logfileName = args['logfile']
    mode = args['mode']
    if args['overwrite'] != '':
      mode = 'w+'

try:

  parseArguments()


  log("*** PIR-Module started (CTRL-C to exit) ***")
  log("Starting Infrared Movement Detection Surveillance with verbosity level '"+str(verbosity)+"'")
  if logfileName:
    log("Using file '"+logfileName+"' with mode '"+mode+"' for log messages...",3)

  execute(COMMAND_ON)
  time.sleep(0.2)

  execute(COMMAND_INIT)
  time.sleep(1.2)

  os.system('cd /home/pi/');
  execute(COMMAND_OFF)

  time.sleep(0.5)

  # Endlosschleife, Ende mit STRG-C
  while True:
    # PIR-Status lesen
    read = GPIO.input(GPIO_PIR)
    if state != read:
      log ("New IR Status '"+str(read)+"' detected (old status '"+str(state)+"')", 3)
    else:
      log ("Current IR Status '"+str(read)+"'", 4)

    if read == 1 and state == 0:
      # PIR wurde getriggert
      execute(COMMAND_ON);
      lastTimedCommand = None
      log("Movement detected!")
    elif read == 0 and state == 1:
      # PIR wieder im Ruhezustand
      log("Infrared Movement Detection Ready ...")
      execute(COMMAND_OFF);
    
    toDo = None
    for timedCommand in timedCommands:
      if timedCommand.isDue() and (timedCommand.wakeup or read == 1):
        if toDo == None or timedCommand.priority < toDo.priority:
          toDo = timedCommand

    if toDo != None:
      if lastTimedCommand == None or toDo.repeat == True:
        log("Executing timed command ('"+toDo.name+":"+toDo.periods+"')")
        execute(toDo.command)
        lastTimedCommand = toDo
      elif lastTimedCommand.command == toDo.command:
        log("Skipped redundant timed command ('"+toDo.name+":"+toDo.periods+"')", 4)
    else:
        log("No timed commands due", 4)

    state = read
    # kleine Pause
    time.sleep(intervalMotionDetection)

except KeyboardInterrupt:
  # Programm beenden
  log("Terminating Infrared Movement Detection ...")
  execute(COMMAND_OFF)
  GPIO.cleanup()

