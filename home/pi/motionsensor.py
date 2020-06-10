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
import threading

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

class TimedCommander:
  def __init__(self):
    self.lastTimedCommand = None
    self.timedCommands = [
      TimedCommand('irsend SEND_ONCE TWEEN_LIGHT KEY_RED', priority=5, repeat=False, name="Nachtruhe"), 
      TimedCommand('irsend SEND_ONCE TWEEN_LIGHT KEY_PURPLE','08:00-22:00', priority=4, repeat=False, name="Tageszeit"),
      TimedCommand('irsend SEND_ONCE TWEEN_LIGHT KEY_PINK','12:00-18:00', priority=3, repeat=False, name="Mahlzeit!"),
      TimedCommand('irsend SEND_ONCE TWEEN_LIGHT KEY_GREEN','13:12-13:20', priority=0, repeat=False, name="Test"),
      TimedCommand('irsend SEND_ONCE TWEEN_LIGHT KEY_POWER', '13:18', priority=0, repeat=False, wakeup=True, name="Aufwachen!")
    ]
  def run(self, active = False, forceRefresh = False):
    toDo = None
    for timedCommand in self.timedCommands:
      if timedCommand.isDue() and (timedCommand.wakeup or active == True):
        if toDo == None or timedCommand.priority < toDo.priority:
          toDo = timedCommand

    if toDo != None:
      if self.lastTimedCommand == None or toDo.repeat == True or forceRefresh == True:
        log("Executing timed command ('"+toDo.name+":"+toDo.periods+"')")
        execute(toDo.command)
        self.lastTimedCommand = toDo
      elif self.lastTimedCommand.command == toDo.command:
        log("Skipped redundant timed command ('"+toDo.name+":"+toDo.periods+"')", 4)
    else:
        log("No timed commands due", 4)

class MotionDetector:
  def __init__(self, interval = 1):
    self.interval = interval
    self.currentStatus = 0
    self.recentStatus = 0

    self.commandOff = 'irsend SEND_ONCE TWEEN_LIGHT KEY_SUSPEND'
    self.commandOn = 'irsend SEND_ONCE TWEEN_LIGHT KEY_POWER'
    self.commandInit  = 'irsend SEND_ONCE TWEEN_LIGHT KEY_FLASH'

    self.gpioPir = 23

    self.init()

  def init(self):
    # BCM GPIO-Referenen verwenden (anstelle der Pin-Nummern)
    # und GPIO-Eingang definieren
    GPIO.setmode(GPIO.BCM)

    # Set pin as input
    GPIO.setup(self.gpioPir,GPIO.IN)

    os.system('cd /home/pi/');

    execute(self.commandOn)
    time.sleep(0.2)

    execute(self.commandInit)
    time.sleep(1.2)

    execute(self.commandOff)

    time.sleep(0.5)

  def run(self):
    self.recentStatus = self.currentStatus
    self.currentStatus = GPIO.input(self.gpioPir)
    if self.currentStatus != self.recentStatus:
      log ("New IR Status '"+str(self.currentStatus)+"' detected (old status '"+str(self.recentStatus)+"')", 3)
    else:
      log ("Current IR Status '"+str(self.currentStatus)+"'", 4)

    if self.currentStatus == 1 and self.recentStatus == 0:
      # PIR wurde getriggert
      execute(self.commandOn);
      # @TODO: lastTimedCommand = None
      log("Movement detected!")
    elif self.currentStatus == 0 and self.recentStatus == 1:
      # PIR wieder im Ruhezustand
      log("Infrared Movement Detection Ready ...")
      execute(self.commandOff);

  def terminate(self):
    log("Terminating Infrared Movement Detection ...")
    execute(self.commandOff)
    GPIO.cleanup()

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

  md = MotionDetector()
  tc = TimedCommander()

  while True:
    md.run()
    tc.run(active = (md.currentStatus == 1),forceRefresh = (md.currentStatus == 1 and md.recentStatus == 0))
    time.sleep(intervalMotionDetection)

except KeyboardInterrupt:
  # Programm beenden
  md.terminate()

