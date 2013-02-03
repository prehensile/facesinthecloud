#!/usr/bin/python

import subprocess
import os
import datetime
import syslog

now = datetime.datetime.now()
hourdaystarts = 10  # civilised
if now.hour < hourdaystarts:
    # bail if it's the middle of the night
    syslog.syslog( "cloudface_runner: asleep. Bailing." )
    exit(1)

home_dir = os.path.expanduser("~")
cloudface_dir = os.path.join( home_dir, ".cloudface" )
success_path = os.path.join( cloudface_dir, ".success" )

syslog.syslog( "cloudface_runner: starting run..." )

# check for an existing success file
if os.path.exists( success_path ):
    # get modification time & date of success file
    mtime = os.path.getmtime( success_path )
    mdate = datetime.datetime.fromtimestamp( mtime )
    if( now.day != mdate.day ):
        syslog.syslog( "cloudface_runner: last sucess was yesterday. clearing success file..." )
        os.remove( success_path )
    else:
        syslog.syslog( "cloudface_runner: has already run successfully today. Bailing." )
        exit(1)
        
# run cloudface
cloudface_script = os.path.join( home_dir, "cloudface.py" )
retcode = subprocess.call( [ "python", cloudface_script ] )
if retcode == 0:
    # run completed successfully
    syslog.syslog( "cloudface_runner: successful run. writing success file." )
    # write sucess file
    subprocess.call( ["touch", success_path ] )
else:
    syslog.syslog( "cloudface_runner: unsuccessful run. better luck next time." )
    exit( 1 )