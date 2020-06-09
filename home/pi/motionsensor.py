#!/usr/bin/python
# -*- coding: iso-8859-1 -*-

import RPi.GPIO as GPIO
import time
import os
import datetime
import argparse
import sys
import subprocess

class TimedCommand:
  def __init__(self, command = 'irsend SEND_ONCE TWEEN_LIGHT KEY_GREEN', periods = '00:00-23:59', repeat = True, priority = 1):
    self.periods = periods
    self.command = command
    self.repeat = repeat
    self.priority = priority
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
      t = self.createTime(times[0])
      if now.time()>=t.time() and now.time()<=t.time():
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
  TimedCommand('irsend SEND_ONCE TWEEN_LIGHT KEY_RED', priority=2, repeat=False), 
  TimedCommand('irsend SEND_ONCE TWEEN_LIGHT KEY_PURPLE','08:00-22:00', priority=1, repeat=False),
  TimedCommand('irsend SEND_ONCE TWEEN_LIGHT KEY_GREEN','15:15-15:30,18:00-18:03,18:12-18:15', priority=0, repeat=False)
]
# these commands are always executed, even if the motion detector is in idle mode
idleCommands = [
  TimedCommand('irsend SEND_ONCE TWEEN_LIGHT KEY_POWER', '18:00', priority=2, repeat=False)
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

# Make sure the timezone is set correctly (e.g. sudo timedatectl set-timezone Europe/Berlin)

def getCurrentTimestamp(format = "%Y-%m-%d %H:%M:%S"):
  return datetime.datetime.now().strftime(format)

def execute(command):
  global verbosity
  global log
  log("Executing Command: "+command)
  os.system(command);

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
      print "["+getCurrentTimestamp()+"]: "+message

def parseArguments():
  global verbosity
  global logfileName
  global logfile
  global mode
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
  args = vars(ap.parse_args())

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
  execute(COMMAND_INIT)

  time.sleep(2)

  os.system('cd /home/pi/');
  execute(COMMAND_OFF)

  time.sleep(2)

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
      log("Movement detected!")
    elif read == 0 and state == 1:
      # PIR wieder im Ruhezustand
      log("Infrared Movement Detection Ready ...")
      execute(COMMAND_OFF);
    
    if read == 1:
      # checking for timedCommands and execute the one with the lowest priority value
      toDo = None
      for timedCommand in timedCommands:
        if timedCommand.isDue():
          if toDo == None or timedCommand.priority < toDo.priority:
            toDo = timedCommand
      if toDo != None:
        if lastTimedCommand == None or lastTimedCommand.command != toDo.command or toDo.repeat == True:
          log("Executing timed command ('"+toDo.periods+"')")
          execute(toDo.command)
          lastTimedCommand = toDo

    state = read
    # kleine Pause
    time.sleep(1)

except KeyboardInterrupt:
  # Programm beenden
  log("Terminating Infrared Movement Detection ...")
  execute(COMMAND_OFF)
  GPIO.cleanup()

