Overview
========

This is an EMC2 configuration for the Buildlog.net 2.x laser cutter.
It has the following features:

* X/Y axis for the laser gantry and carriage.  Configured for MXL belts, 400 step motors and 8x microstepping.
* U axis for the table.  Configured for 1/4" 20 TPI threaded rod driven by a 400 step motor, 8x microstepping via a 48:20 belt reduction.
* Z axis which does not move the table at all but instead activates the laser when Z<0.  This provides some "instant compatibility" with mill/router CAM.

There is some minor customization to Axis, the primary EMC2 GUI.  Some
of the viewing angle buttons have been eliminated and page up/down have
been shifted to the U (table) axis.

The laser has a master enable provided by M3/M5 (spindle control).  When the
"spindle" is off the laser cannot fire.  This means the laser turns off when
you expect it to, such as when aborting a job.

When the laser is enabled via M3 it can be fired either by digital IO or
by moving the imaginary Z axis to any negative position.  Using a high "plunge"
speed in the CAM job and a very small depth of cut (such as 0.01mm) avoids
having the laser pause when it starts and stops cuts.

A custom "M" script is provided, M144, which can raster engrave images.

Special Commands
================

Laser control
-------------

Laser firing control is on parallel port pin 17.

Set laser power with M68 E0 Qxxx where xxx is a number from 0.0 to 1.0.
It is likely that your printer port's PWM output at 1.0 will be *more
than 100% power* for your laser.  In my case my laser PSU current is
20mA when there is 3V at the IN terminal.  My parallel port's "on"
voltage is about 4.3V, so M68 E0 Q0.7 produces full power for my setup.
Below about 0.5V (or Q0.012) my laser will not fire.  This power setting
can generally go in the preamble of your CAM setup since you will vary
PPI and speed rather than power for most cutting jobs.

Enable the laser with M3 Sxx where the spindle speed xx is in "pulses
per mm" (or about 1/25th a PPI or "pulses per inch" setting).  M3 S0 is
equivalent to "off" (or M5) and the laser will not fire.  Based on Dirk's
research the pulse length is set (in 2x_Laser.ini) to 3ms, so you can get
continuous wave output by simply picking a high enough S value for your
feed rate that pulses happen more frequently than 3ms (e.g. S10000 is
continuous for anything faster than F2).

If you choose direct digital control of the laser, use M65 P0 ("immediate
off") in your preamble and use M62 P0/M63 P0 to turn the laser on and off
within a sequence of G1 movements.  The M62/63 are queued with movement
while M64/65 happen immediately.

If you choose "magic Z" control of the laser simply configure your CAM
job to make very shallow (0.01mm) cuts with a very fast plunge rate and
the laser will turn on whenever the CAM job "moves the router bit down".

Chiller/Assist Air Control
--------------------------

There is a digital output on parallel port pin 1 for switching an outlet
that controls the laser coolant and the assist air.  It comes on
automatically whenever M3 (the master laser enable) is on and stays on for
20 seconds after M5 (configurable in the INI as EXTRA_CHILLER_TIME).

Blower Control
--------------

There is another digital output on parallel port pin 2.  It can be
directly controlled with M62/63/64/65 P2.  I use it to control the blower
that removes smoke from the laser.

Raster Engraving
----------------

Raster operation is done by calling a subroutine O145 from within gcode
with several parameters.  It invokes M144 and M145 which are external
python scripts.  Those stream data back into EMC2's realtime engine while
the subroutine in O145 sweeps out the raster pattern.

Due to limitations in EMC2 there is no way to pass a filename for the
rastering process.  Instead you must put a number in the filename, such
as "flower-123.png".  The text name is for your convenience, but only the
"123" will select the image from within gcode.  The program will search for
the wildcard `*-123.*` in [RASTER]IMAGE_PATH (can be a colon separated list)
and use the first one it finds.  If that is not configured in your INI it
will default to your home directory.  If it does not find the file it will
prompt you with a file selector.

The image can be of any size or shape and will be rescaled and dithered to
black and white to match the parameters of the engraving (see below).  You
can provide a black and white image with the correct DPI and size and it will
be used unmodified.

To do a raster engraving, the spindle must be enabled with M3 (as always
for any laser firing operation).  However, the pulse setting does not
matter and all pulsing is controlled by the engraving process.

The O145 script will operate in inches or mm (G20 or G21) and all sizes
just need to be in the appropriate units:

    M3 S1         (enable spindle)
    M68 E0 Q0.2   (choose an engraving power)
    F28200        (choose an engraving feed rate)
    O145 call [pic] [x] [y] [w] [h] [x-gap] [y-gap] [overscan]

Where the parameters are:

* pic - number used to select the image file (with the wildcard `*-pic.*`)
* x, y - the upper lefthand corner of the engraving (the spot where the image's (0,0) will appear)
* w, h - the width and height of the engraving
* x-gap - units per pixel column (in mm, 25.4/DPI, in inches 1/DPI)
* y-gap - units per pixel row (see x-gap)
* overscan - overshoot of the laser carriage to either side of the image

The x-gap and y-gap are independent.  Choosing a y-gap of 0.085mm (about
300 DPI) means that the laser carriage will sweep back and forth 300 times
for every inch of image height.  The finer the y-gap the longer the engraving
will take.  The x-gap only modifies how frequently the laser is modulated
and thus has no effect on rastering time as long as your system has enough
memory.  Obviously any x-gap smaller than 1/SCALE is meaningless, but with
the stock setup that would be close to 2000 DPI.

The overscan is to give the laser carriage time to accelerate to full speed.
If the laser is still accelerating within the field of the image then the
left/right edges will be engraved slightly darker.  You can compute the
exact distance needed as 0.5 * F^2 / A where F is feed speed (in mm/s, not
mm/min) and A is [AXIS_0]MAX_ACCELERATION.  Assuming you always engrave
at top speed ([AXIS_0]MAX_VELOCITY = 470mm/s) and modulate power to suit,
the value of overscan should be about 15mm.  If you tune the accel faster
or engrave at a lower speed you can use smaller overscan.  If you are willing
to tolerate some uneven engraving power at the edges you can turn overscan
way down to get near the edge of your work area.  I have not tested with
overscan of 0, that might break the algorithm.

Example:

    G20            ( set inches mode )
    M3 S20
    M68 E0 Q0.5
    F1110
    O145 call [1587] [0.2133] [10.2867] [10.0733] [10.0733] [0.0033] [0.0033] [0.5]

(Note that the example is in inches due to G20!) That engraves an image
"dominos-1587.png" at X0.2133 Y10.2867 which is 10.0733 inches square.
The x- and y-gaps are both 0.0033" making 303 DPI.  The feedrate is 1110 IPM
and the overscan is 0.5".

Installation
============

This is based on an installed copy of the EMC2 Ubuntu 10.04 LTS Live CD.

Install the custom laser pulse HAL component.  The first command installs
the necessary tools in case you don't have them.  For more information see
http://wiki.linuxcnc.org/emcinfo.pl?ContributedComponents

    sudo apt-get install emc2-dev build-essential
    sudo comp --install laserfreq.comp

The configuration will not work without that component installed.

Find all occurances of "/home/bjj/Desktop/2x_Laser" in the INI and replace
with the path to your own configuration.

Configuration
=============

You must first get EMC2's realtime configuration sorted out on your hardware.
There is extensive documentation for this online based around the EMC2
latency-test program:  http://wiki.linuxcnc.org/emcinfo.pl?Latency-Test

My system was able to use a [EMCMOT]BASE_PERIOD of 27000 (27us) which
(along with the microstepping setting) dictates my system's maximum velocity.
If you change SCALE or BASE_PERIOD you will need to compute new MAX_VELOCITY
settings for each axis.

If your stepper configuration does not match what is described above,
compute new values for [AXIS_0]SCALE, [AXIS_1]SCALE and [AXIS_6]SCALE
in 2x_Laser.ini.  Ignore AXIS_2, it is the imaginary Z axis.

My build resulted in a maximum travel of 285x535mm.  These are the
[AXIS_0]MAX_LIMIT and [AXIS_1]MAX_LIMIT.  Setting these correctly will keep
you from banging into the physical endstops.  The 2.x build homes in the
lower left, but you can cause EMC2 to automatically reposition anywhere
after homing with the [AXIS_0]HOME and [AXIS_1]HOME.

If any axis moves backwards from what you expect, modify the parport
"invert" lines in 2x_Laser.hal.  Where you see
"setp parport.0.pin-03-out-invert 1", for example, change the 1 to a 0
as needed for the pins associated with xdir, ydir, udir.

If your stepper configuration varies significantly from Bart's Pololu
board, you may need to just start by running "stepconf" to find the
several detailed parameters required of your stepper driver.  You can then
port these values into the 2x_Laser HAL file.

Acknowledgements
================

Jedediah Smith at Hacklab Toronto created an EMC2 configuration for their
laser which opened my eyes to how powerful the HAL is.  In particular the
use of halstreamer synchronized with an external script is key to the
raster implementation.

Barton Dring's buildlog.net 2.x laser is one of the best open hardware
projects on the net.  The engineering work and documentation is second to
none.  Without his work on the plans and kits I wouldn't own a laser cutter.

Dirk Van Essendelft has done numerous experiments in DIY lasercutting
which he has documented on the buildlog.net forums.  His research into the
behavior of PPI with our CO2 lasers lead to improved the performance of the
PPI implementation in this configuration.
