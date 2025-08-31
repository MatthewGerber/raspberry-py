[Home](index.md) > CAD Parts
* Content
{:toc}

This page documents parts I have designed for 3D printing. See [here](https://github.com/MatthewGerber/3d-printing) for 
general 3d-printing notes, and [here](https://www.printables.com/@MatthewGerbe_3143168/models) for my model files.

# Reinforcement Learning for the Cart-Pole Apparatus

<iframe src="https://gmail3021534.autodesk360.com/shares/public/SH512d4QTec90decfa6e100c90ac15102a61?mode=embed" width="800" height="600" allowfullscreen="true" webkitallowfullscreen="true" mozallowfullscreen="true"  frameborder="0"></iframe>

This is not a new concept. If you search for "cart-pole balancing", you'll see that this problem has been solved in a
variety of ways. However, the details are always interesting, and I was curious whether my [RLAI](https://matthewgerber.github.io/rlai/)
would find a solution. This is [a work in progress](https://github.com/MatthewGerber/cart-pole).

# H-Gantry

<iframe src="https://gmail3021534.autodesk360.com/shares/public/SH286ddQT78850c0d8a4f16d8ed322db9a1e?mode=embed" width="800" height="600" allowfullscreen="true" webkitallowfullscreen="true" mozallowfullscreen="true"  frameborder="0"></iframe>

How do you control a two-axis linear gantry system? The simple solution is to [use two stepper motors](https://www.youtube.com/watch?v=uOSCsBbsX4w), 
one attached to each axis. The harder solution:  Use [two fixed-position stepper motors with a crazy, winding belt](https://www.youtube.com/watch?v=IkM2K7CsiHo).
There are advantages each way. The former is simpler to design and build; however, the motor mass is attached to each
axis, which is not ideal when the axes are changing direction quickly. In the latter design, the motors have fixed 
positions, so the motor mass is not attached to a moving axis. The control is more complicated, but this makes it 
interesting, which is also an advantage! The software is [here](https://github.com/MatthewGerber/h-gantry).

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
