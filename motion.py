#! /usr/bin/env python
#
# motion.py is invoked by motioneye when movement is detected
#   - the white LED is turned on when motion is detected at night
#   - calculate sunrise (dawn) and sunset (dusk) using astral
#   - optionally a text message is sent
#   - enable command line usage
#   - write significant events to a log file
#   - options:
#      - debug on or off
#      - alerts on or off
#      - white LED on when motion detected
#      - white LED on from sunset (dusk) to sunrise (dawn)
#      - ID for forwarding gmail to text message on phone
#      - time for white LED to be on after motion detection
#
# Run using:
#   sudo python3 motion.py
#
# To Do List:
#  ??? If Sunset option is selected then this needs a cron job (or are both invoke methods required?)
#
#########################


#########################
# Modules to import
import smtplib
import time
import datetime
import dateutil
from dateutil import tz
import astral   # pip install astral, or pip3 install astral
import os
import subprocess
import sys
import getopt
import RPi.GPIO as GPIO


#########################
# Global constants (all upper) and variables (first upper)
#   White LED GPIO pin
WHITE_LED = 17
YEAR = datetime.datetime.today().strftime('%Y')
MONTH = datetime.datetime.today().strftime('%m')
DAY = datetime.datetime.today().strftime('%d')
REGION = "TX, USA"
TIMEZONE = "US/Central"

#   *** CHANGE THE ITEMS BELOW - DO NOT PUBLISH ***

#     Change the items in the angle brackets, and remove the angle brackets
#     use google maps to find your home, and then tap on the icon and scroll down to get your latitude and logitude

LATITUDE = "<your latitude>"
LONGITUDE = "<your longitude>"
NAME = "<your city's name>"

#   *** CHANGE THE ITEMS ABOVE - DO NOT PUBLISH ***


#########################
# Global variables (first upper)

#   *** CHANGE THE ITEMS BELOW - DO NOT PUBLISH ***

#     Change the items in the angle brackets, and remove the angle brackets
#     Create a gmail rule to look for the ID and forward the message to your cellphone number

GmailPassword = '<your throwaway gmail password>'
GmailAddress = '<your throwaway gmail account>@gmail.com'
ID = '<your project ID>' # This is the ID gmail fowards to your smart phone

#   *** CHANGE THE ITEMS ABOVE - DO NOT PUBLISH ***

LogFile = open('/home/pi/motion.log', 'w+')
#   if Debug = true, then should be running on command line and output to terminal window
Alerts = False
Debug = False
Motion = False
Sunset = False
Timer = 20      # in seconds


#########################
# Modules
#   Log messages should be time stamped
def getTimeStamp():
    t = time.time()
    s = datetime.datetime.fromtimestamp(t).strftime('%Y/%m/%d %H:%M:%S - ')
    return s

#   Write messages in a standard format
def printMsg(s):
    global LogFile
    global Debug

    # don't Time Stamp blank lines
    if s == '':
        LogFile.write("\n")
        if Debug:
            print('')
    else:
        LogFile.write(getTimeStamp() + s + "\n")
        if Debug:
            print(getTimeStamp() + s)

    LogFile.flush()

#   Process and create command line options (arguments)
def processCommandLine(argv):
    # All command line variables need to be declared here
    global Alerts
    global Debug
    global ID
    global Motion
    global Sunset
    global Timer

    try:
        # new options must be added on both lines below:
        #   options that require values are followed by a colon (e.g., x:, -x 4)
        validOpts = "adhi:mst:"
        opts, args = getopt.getopt(argv,validOpts,["help=", "alerts=", "debug=", "help=", "id=", "motion=", "sunset=", "timer="])
    except getopt.GetoptError:
        print('motion.py [options, ...]' )
        print('motion.py -h' )
        sys.exit(2)

    for opt, arg in opts:
        # help option goes first and exits, regardless of other options
        if opt in ('-h', "--help"):
            print('Decription: ')
            print('  motion.py is started by motionEye when motion is detected')
            print('  motion.py must be added to motionEye configuration under Motion Notifications')
            print('')
            print('Usage:')
            print('  python3 motion.py [options...]')
            print('')
            print('Options:')
            print('  -h          this help')
            print('  -a          alerts off')
            print('  -d          debug on')
            print('  -i          sets ID value')
            print('  -m          turn on LED on motions')
            print('  -s          turn on LED from sunset to sunrise. Sunset overrides -m, motion.')
            print('  -t          turn on LED on motion for timer length seconds (default = 20s)')
            sys.exit()
        elif opt in ("-a", "--alerts"):
            Alerts = True
        elif opt in ("-d", "--debug"):
            Debug = True
        elif opt in ("-i", "--id"):
            ID = arg
        elif opt in ("-m", "--motion"):
            Motion = True
        elif opt in ("-s", "--sunset"):
            Sunset = True
        elif opt in ("-t", "--timer"):
            Timer = int(arg)

    if Sunset:
        Motion = False
    if Motion:
        if Timer <= 0:
            print('Error: Timer is 0 and Motion is enabled. Timer must be greater than 0. Exiting')
            exit()
    return


#   Send email to gmail, and then send text messages to cell phone using a gmail rule and an ID
def sendText(s):
    global ID
    global GmailAddress
    global GmailPassword

    subject = ID + " Camera: " + s
    message = 'Subject: %s' % (subject)
    # 587 uses TLS
    # 465 uses SSL - not supported see edits to /etc/ssmtp/ssmtp.conf
    mail = smtplib.SMTP("smtp.gmail.com", 587)
    mail.ehlo()
    mail.starttls()
    mail.login(GmailAddress, GmailPassword)
    mail.sendmail("cell", GmailAddress, message)
    mail.close()

#   using astral, get your home's location
def getLocation():
    global NAME
    global REGION
    global TIMEZONE
    global LATITUDE
    global LONGITUDE

    # Latitude, longitude, and timezone are required
    #   The name and region are informational
    #   Use google maps to find your home, and then tap on the icon and scroll down to get your latitude and logitude
    location = astral.LocationInfo(name=NAME, region=REGION, timezone=TIMEZONE, latitude=LATITUDE, longitude=LONGITUDE)

    return (location)

def convertTimeZone(d):
    # convert UTC to US Central Time Zone
    fromZone = tz.gettz('UTC')
    toZone = tz.gettz('America/Chicago')

    d = d.replace(tzinfo=fromZone)
    d = d.astimezone(toZone)

    return(d)


##############
def main(sysargv):
    global Alerts
    global Debug
    global ID
    global Motion
    global Sunset
    global Timer
    global YEAR
    global MONTH
    global DAY

    printMsg("Starting motion.py")

    # process command line arguments
    processCommandLine(sysargv[1:])
    if Debug:
        print("-a, alerts = " + str(Alerts))
        print("-d, debug  = True")
        print("-i, ID = " + ID)
        print("-m, motion = " + str(Motion))
        print("-s, sunset = " + str(Sunset))
        print("-t, timer = " + str(Timer))

    location = getLocation()
    if Debug:
        print('location = ' + str(location))
        print('observer = ' + str(location.observer))
        print('date     = ' + str(datetime.date(int(YEAR), int(MONTH), int(DAY))))

    from astral.sun import sun
    s = sun(location.observer, date=datetime.date(int(YEAR), int(MONTH), int(DAY)))
    dawn = s['dawn']
    dusk = s['dusk']

    # Timezone info from dawn or dusk, which are aware of the timezone
    timezone = dawn.tzinfo

    # dawn and dusk will generally return two different dates depending on when sun is called
    # dawn and dusk do not vary that greatly from day to day, so assume both are on the same date
    # get time now
    t = datetime.datetime.now()
    # Current datetime for the timezone of your variable
    t = datetime.datetime.now(timezone)
    t = convertTimeZone(t)

    dusk = convertTimeZone(dusk.replace(t.year, t.month, t.day, dusk.hour, dusk.minute, dusk.second, 00))
    dawn = convertTimeZone(dawn.replace(t.year, t.month, t.day, dawn.hour, dawn.minute, dawn.second, 00))
    midnight = dusk.replace(t.year, t.month, t.day, 11, 59, 59, 00)
    afterMidnight = dusk.replace(t.year, t.month, t.day, 00, 00, 00, 00)

    if Debug:
        sunrise = dawn.strftime('%H:%M:%S')
        sunset = dusk.strftime('%H:%M:%S')
        now = t.strftime('%H:%M:%S')
        print("dawn = " + str(sunrise))
        print("dusk = " + str(sunset))
        print("now  = " + str(now))
        print("midnight  = " + str(midnight))
        print("afterMidnight  = " + str(afterMidnight))

    GPIO.setmode(GPIO.BCM)
    GPIO.setup(WHITE_LED, GPIO.OUT)

    if Alerts:
        sendText('Motion detected')

    # is current time between dusk and midnight or between midnight and dawn
    if (t >= afterMidnight and t <= dawn) or (t <= midnight and t >= dusk):
        if Sunset:
            # is current time between dusk and midnight or between midnight and dawn
            #   if yes, activate white LED
            # turn white LED on
            GPIO.output(WHITE_LED, GPIO.HIGH)
            # no GPIO.cleanup so LED stays on
        elif Motion:
            # turn white LED on
            GPIO.output(WHITE_LED, GPIO.HIGH)

            time.sleep(Timer)

            # turn white LED off
            GPIO.output(WHITE_LED, GPIO.LOW)
    else:
        # turn white LED off
        GPIO.output(WHITE_LED, GPIO.LOW)
        GPIO.cleanup()

    exit()


#########################
if __name__ == '__main__':
    # run as a script from command line
    main(sys.argv)
else:
    # ??? could allow import to another module; needs work
    pass

printMsg("Exiting motion.py")
exit()
