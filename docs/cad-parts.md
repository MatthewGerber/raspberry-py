[Home](index.md) > CAD Parts
* Content
{:toc}

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
* Automatic bed leveling: I added the [CR Touch Automatic Leveling Kit](https://www.amazon.com/Creality-Leveling-Compatible-Mainboard-Printer/dp/B098LQ9WPX/ref=sr_1_3?th=1) 
to my Ender 3. The sensor comes with a mounting bracket for the Ender 3; however, it isn't truly designed for this model,
and I had previously replaced the hot end with something different. As a result, the sensor was mounted too far above
the bed, which caused the hot end to drop down into the bed. After much experimenting and searching, I found that the 
sensor needed to be offset down toward the bed in order for everything to work. I did this by adding spacers as shown
below:
  
  ![cr-touch-spacers](cr-touch-spacers.png)

  The steps for calibrating the leveling probe's z-offset are as follows:
  1. Auto-home the printer.
  2. Move the z-axis to identify the appropriate z-offset, using a sheet of A4 paper for thickness. Note the z-offset 
     that causes the nozzle to just slightly grab the paper. Call this `adjustment`.
  3. Auto-home the printer.
  4. Access the leveling probe's z-offset and note its value. Call this `current`. Then set the leveling probe's 
     z-offset to `current + adjustment`.
  5. Save the configuration settings.
  6. Level the bed. The hot end should be in the correct position above the bed, with the z-value showing 0.0 on the 
  printer display and a very small gap between the nozzle and bed.
  7. Add `G28 G29` to your slicer's g-code preamble. The `G28` (home) command is probably already present, in which case
  you just tack on `G29` (level bed).
  8. Octoprint has a [bed leveling visualizer plugin](https://plugins.octoprint.org/plugins/bedlevelvisualizer), which 
  displays the bed mesh as shown below:
  
  ![bed-mesh](bed-mesh.png)
  
* 3D printer web interface:  I use [OctoPrint](https://octoprint.org) with my Raspberry Pi as an efficient and easy way
to manage print jobs. See [here](octoprint.md) for tips on configuring OctoPrint on the Pi.
* Tips for changing the bowden tube and nozzle, particularly when the extruder stepper motor is skipping, the extruder 
  gear is slipping on the filament, or the printer is under-extruding.
  1. Remove the nozzle:  The flat end should be clean without any filament sitting on top, which might indicate that the 
     bowden tube isn't tightly seated against the nozzle entry within the hot end.
  2. Replace the bowden tube.
     1. Replace the tube couplings in the extruder and hot end to ensure they will properly grab the new tube.
     2. Heat the hot end.
     3. Tighten the nozzle.
     4. Loosen the nozzle 1/2 a turn.
     5. Insert the bowden tube firmly and fully into the hot end coupling.
     6. Tighten the nozzle, which seats the bowden tube firmly against the nozzle.
     7. Trim the tube to length for the extruder so that it can easily reach all print positions.
     8. Insert the bowden tube firmly and fully into the extruder coupling.
     9. Level the bed if needed.

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

The files for this design can be downloaded from Thingiverse [here](https://www.thingiverse.com/thing:6153142).

Related projects:

* [Smart car](smart-car.md)

# Elevator

This is an elevator designed for the stepper motors found 
[here](https://www.digikey.com/en/products/detail/adafruit-industries-llc/858/5629414).

<iframe src="https://gmail3021534.autodesk360.com/shares/public/SH35dfcQT936092f0e43161fdf97e4f7a1b0?mode=embed" width="800" height="600" allowfullscreen="true" webkitallowfullscreen="true" mozallowfullscreen="true"  frameborder="0"></iframe>

Full details can be found [here](elevator.md).

Related projects:

* [Smart car](smart-car.md)

# DC Motors

The following is a four-coil brushed direct-current (DC) motor:

<iframe src="https://gmail3021534.autodesk360.com/shares/public/SH512d4QTec90decfa6ee884568e9083a6b5?mode=embed" width="800" height="600" allowfullscreen="true" webkitallowfullscreen="true" mozallowfullscreen="true"  frameborder="0"></iframe>

Full details can be found [here](brushed-dc-motor.md).


# Tips and Tricks

1. The small deboss labels on various components contain the Fusion 360 version numbers of the design file. This is a 
handy way to keep track of the design file version used to print each component, particularly when diagnosing issues, 
updating the design, and printing new versions. I use the 
[ParametricText](https://parametrictext.readthedocs.io/en/stable/) add-in to automatically update the version numbers 
when saving the design file.