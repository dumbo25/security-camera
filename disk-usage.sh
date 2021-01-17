#!/bin/bash
#
# This script checks a microSD card on a raspberry camera and if the usage is above
# the alert threshold, then video files are auto-deleted until disk usage is below
# a stop threshold
#
# The script should be run every five minutes or so as a crontab
#
#   sudo bash disk-usage.sh
#
# Assume 15% od microSD Card is used for OS and other stuff
# The remainded is used for videos and photos, with videos consuming the majority
#
# Delete files when disk usage exceeeds the alert Threshold
alertThreshold=75
# stop deleting files when disk usage falls below the stopThreshold
#stopThreshold=50
stopThreshold=50
# settings from MotionEye
fileStorageRootDirectory="/var/lib/motioneye/Camera1"
preserveMovies=7
movieExtension="*.mp4"

# function to calculate whether or not over threshold
function calculateOverThreshold {
        overThreshold=0

        spaceUsed=`df -H $fileStorageRootDirectory | grep /dev/root | awk -F" " '{print $5}' | tr --delete %`

        if [ $1 == "alert" ]
        then
                if [ "$spaceUsed" -gt "$alertThreshold" ]
                then
                        overThreshold=$(($spaceUsed - $alertThreshold))
                fi
        elif [ $1 == "stop" ]
        then
                if [ "$spaceUsed" -gt "$stopThreshold" ]
                then
                        overThreshold=$(($spaceUsed -  $stopThreshold))
                fi
        fi

        if [ $overThreshold -lt 0 ]
        then
                $overThreshold=0
        fi
}


# decide if too much disk space is being used
calculateOverThreshold "alert"
if [ $overThreshold -gt 0 ]
then
        # assume files are retained for a week
        # if too much disk space is being used, then delete oldest day's directory and all its files
        # for N = 7..1 delete over day N and then check if under stop threahold
        days=$preserveMovies
        for (( i=$days; i>=1; i-- ))
        do
                removeDate=$(date -d "-$i days" '+%Y-%m-%d')
                rmDirAndFiles="$fileStorageRootDirectory/$removeDate"
                # need to write to log file each time files are deleted becasue it might indicate
                # something is wrong with the camera's thresholds for motion detection
                [[ -d $rmDirAndFiles ]] && rm -r $rmDirAndFiles

                calculateOverThreshold "stop"
                if [ $overThreshold -le 0 ]
                then
                        # When below stopThreshold, then exit
                        break
                fi
        done

fi

# decide if there is still too much disk space is being used
calculateOverThreshold "alert"
if [ $overThreshold -gt 0 ]
then
        # if current day is over threshold, then drop into today's directory and loop through deleting oldest file first untilunder stop threshold
        removeDate=$(date -d "-0 days" '+%Y-%m-%d')
        rmFiles="$fileStorageRootDirectory/$removeDate/$movieExtension"
        ls -1rt $rmFiles | while read -r fname; do
                [[ -f $fname ]] && rm $fname
                # each mp4 also has an associated thumb file thaat needs to be deleted
                [[ -f $fname.thumb ]] && rm $fname.thumb

                calculateOverThreshold "stop"
                if [ $overThreshold -le 0 ]
                then
                        # When below stopThreshold, then exit
                        break
                fi
        done
fi
