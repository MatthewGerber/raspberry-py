[Home](index.md) > A 3D-Printed Robotic Arm 

<iframe src="https://gmail3021534.autodesk360.com/shares/public/SH35dfcQT936092f0e4344f64dd3dcf58a6f?mode=embed" width="800" height="600" allowfullscreen="true" webkitallowfullscreen="true" mozallowfullscreen="true"  frameborder="0"></iframe>

# Introduction

This page documents the development of a 3D-printed robotic arm for use with the remote-controlled 
[Freenove Smart Car](smart-car.md). Beyond a few small test pieces, this was the first real design/build project that I
pursued with 3D printing. The concept is basic, including a few degrees of freedom driven by the SG90 servo motors that 
come with the car and are ubiquitous in the RC world. The design poses several good challenges for anyone starting out
with CAD or---like me---returning to CAD after a _very_ long time (9th grade high school, if my memory serves):

* Mobility:  A little practice goes a long way toward designing solid objects from 2D sketches (points, lines, circles,
etc.) and 3D operations (extrusions, joins, cuts, holes, etc.). I found the learning curve to be quite gentle in this 
regard, particularly with the right CAD system (more on this later). It was much more difficult to build constrained 
movement into the design. Think hinges and keyed rotation shafts. These were tricky at first, but effective patterns 
became evident after a few attempts.
* Motor-part integration:  This is where the magic happens, where the design comes to life. In the case of the robotic
arm it was a matter of connecting the rotating shaft of the SG90 servo with a mobile part of the arm design.
* Build tolerance:  Parts must be in contact but not too tight. CAD provides exact precision, and although entry-level 
3D printers provide surprising fidelity, they are not exact. However, the inexactness is systematic in my experience, 
making it tolerable.

All of this adds up to a good bit of time, failure, iteration, and fun.  

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

# Degrees of Freedom

The current design has five degrees of freedom listed below.

1. Base rotation
2. Arm elevation
3. Wrist elevation 
4. Wrist rotation
5. Pinch

Due to the symmetry of the design, DoFs 1 and 2 comprise the same parts as 3 and 4. These two pairs provide rotation and 
elevation at each end of the arm, leaving the pincher to sit on top. 

# Parts:  Print Times/Costs and Photos 

The table below shows the arm parts with estimated print times and materials from the Cura slicer and costs based on $20 
per 1000 grams ($0.02 per gram) of filament
(e.g., [here](https://www.amazon.com/Polymaker-PolyTerra-Bioplastic-Printing-Filament/dp/B08QN5FQX7/)).

| Part                           | Print Time (HH:MM) | Print Cost  | Image                                          |
|--------------------------------|--------------------|-------------|------------------------------------------------|
| Base rotator                   | 3:45               | $0.48 (24g) | ![base-rotator](arm-parts/rotator.png)         |
| Arm base                       | 1:45               | $0.20 (10g) | ![arm-base](arm-parts/arm-base.png)            |
| Arm elevator wheel             | 0:30               | $0.04 (2g)  | ![arm-wheel](arm-parts/wheel.png)              |
| Arm                            | 0:30               | $0.06 (3g)  | ![arm](arm-parts/arm.png)                      |
| Wrist elevator wheel           | 0:30               | $0.04 (2g)  | ![wrist-wheel](arm-parts/wheel.png)            | 
| Wrist base                     | 1:45               | $0.20 (10g) | ![wrist-base](arm-parts/arm-base.png)          |
| Wrist rotator                  | 3:45               | $0.48 (24g) | ![wrist-rotator](arm-parts/rotator.png)        | 
| Pincher base with fixed finger | 2:30               | $0.30 (15g) | ![pincher-base](arm-parts/pincher-base.png)    |
| Pincher mobile finger          | 0:40               | $0.08 (4g)  | ![finger-mobile](arm-parts/pincher-mobile.png) |
| Pincher pin                    | 0:10               | $0.02 (1g)  | ![pincher-pin](arm-parts/pincher-pin.png)      | 
| Total                          | 15:50              | $1.90 (95g) | ![semi-complete](arm-parts/semi-complete.png)  |                 

The complete design image does not show the base rotator, arm base, and arm elevator wheel. The design is symmetric on
each end of the arm, so it was not necessary to draw these components.

# Assembly

# Performance Evaluation
