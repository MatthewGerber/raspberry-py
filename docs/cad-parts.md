[Home](index.md) > CAD Parts

This page documents parts I have designed for 3D printing.

# Materials and Tech

* CAD software:  I started out with [FreeCAD](https://www.freecadweb.org/). I was impressed by the range of capabilities 
that comes with the software and the quality with which they are delivered---at least initially. Everything worked well 
for small parts and the initial phases of the larger arm project. However, as the design grew, the tree-structure 
representation of design elements became unwieldy. It was difficult to predict how the tree would rearrange following
an operation. Ultimately, a bug surfaced in the FreeCAD software, and I was unable to undo and recover my design. I 
started looking elsewhere and found [Autodesk Fusion 360](https://www.autodesk.com/products/fusion-360/personal), which 
can be obtained free of charge for personal use. I was, and still am, quite new to CAD; however, Fusion 360 is obviously 
a top-notch product. Everything just works. The operations are stunningly intuitive and well-crafted. It is difficult to 
imagine a reason for looking elsewhere except, of course, for the facts that the free version cannot be used 
commercially and the commercial version is quite expensive.
* Mesh slicer:  [UltiMaker Cura](https://ultimaker.com/software/ultimaker-cura) is a simple tool with a single purpose:
slice the mesh outputs of CAD into horizontal layers that can be 3D printed. The settings are endlessly configurable, 
but the defaults work quite well. Support structures are effective and efficient, and I haven't had a problem yet.
* 3D printer:  This is the only item in the list that is not free. With endless options on the market it can be 
difficult to choose; however, at under $200 with generally quite positive reviews, it is difficult to get past the
[Creality Ender-3](https://www.creality.com/products/ender-3-3d-printer). It was simple to assemble and has been 
cranking out high-quality pieces since the start.
* 3D printer web interface:  I use [OctoPrint](https://octoprint.org) with my Raspberry Pi as an efficient and easy way
to manage print jobs.

# Robotic Arm

<iframe src="https://gmail3021534.autodesk360.com/shares/public/SH35dfcQT936092f0e4344f64dd3dcf58a6f?mode=embed" width="800" height="600" allowfullscreen="true" webkitallowfullscreen="true" mozallowfullscreen="true"  frameborder="0"></iframe>

This was the first real project that I pursued with 3D printing. The concept is basic, including five degrees of 
freedom driven by [SG90 servo motors](https://www.amazon.com/dp/B08KY49SFX). The design poses several good challenges 
for anyone starting out with CAD or---like me---returning to CAD after a _very_ long time (9th grade high school, if my 
memory serves):

* Mobility:  A little practice goes a long way toward designing solid objects from 2D sketches (points, lines, circles, 
planes, etc.) and 3D operations (extrusions, joins, cuts, holes, etc.). I found the learning curve to be quite gentle in 
this regard, particularly with the right CAD system (more on this later). It was much more difficult to build 
constrained movement into the design. Think hinges and keyed rotation shafts. These were tricky at first, but effective 
patterns became evident after a few attempts.
* Motor-part integration:  This is where the magic happens, where the design comes to life. In the case of the robotic
arm it was a matter of connecting the rotating shaft of the SG90 servo with a mobile part of the arm design.
* Build tolerance:  Mobility requires parts to be in contact but not be too tight. CAD provides exact precision, and 
although entry-level 3D printers provide surprising fidelity, they are not exact. However, the inexactness is systematic 
in my experience, and small tolerances seem to be quite achievable.

All of this adds up to a good bit of time, failure, iteration, and fun. Full details can be found 
[here](robotic-arm.md).

Related projects:

* [Smart car](smart-car.md)

# Freenove Smart Car Rear- and Front-Mounts

The smart car comes out of the box with a front-mounted camera. I designed this bracket to move the camera to the back
and provide room for front-mounted parts like the robotic arm described above.

<iframe src="https://gmail3021534.autodesk360.com/shares/public/SH35dfcQT936092f0e43a682340dfc199b2c?mode=embed" width="800" height="600" allowfullscreen="true" webkitallowfullscreen="true" mozallowfullscreen="true"  frameborder="0"></iframe>

Related projects:

* [Smart car](smart-car.md)

# Elevator

This is an elevator designed for the stepper motors found 
[here](https://www.digikey.com/en/products/detail/adafruit-industries-llc/858/5629414).

<iframe src="https://gmail3021534.autodesk360.com/shares/public/SH35dfcQT936092f0e43161fdf97e4f7a1b0?mode=embed" width="800" height="600" allowfullscreen="true" webkitallowfullscreen="true" mozallowfullscreen="true"  frameborder="0"></iframe>

Full details can be found [here](elevator.md).

Related projects:

* [Smart car](smart-car.md)

# Tips and Tricks

1. The small deboss labels on various components contain the Fusion 360 version numbers of the design file. This is a 
handy way to keep track of the design file version used to print each component, particularly when diagnosing issues, 
updating the design, and printing new versions. I use the 
[ParametricText](https://parametrictext.readthedocs.io/en/stable/) add-in to automatically update the version numbers 
when saving the design file.