[Home](index.md) > [CAD Parts](cad-parts.md) > Brushed DC Motor

<iframe src="https://gmail3021534.autodesk360.com/shares/public/SH512d4QTec90decfa6ee884568e9083a6b5?mode=embed" width="800" height="600" allowfullscreen="true" webkitallowfullscreen="true" mozallowfullscreen="true"  frameborder="0"></iframe>

{% include youtubePlayer.html id="5srIUrAuiNM" %}

# Parts and Materials

Required
* [Copper sheet](https://www.amazon.com/dp/B0C1ZZLR97?th=1):  Used to build commutator plates.
* [30 AWG enameled magnet wire](https://www.amazon.com/dp/B00UWCXRK6?th=1):  Used to create electromagnetic windings.
* [Soft iron rod](https://www.amazon.com/dp/B0BNNCZ4ZR):  Enhances the field strength of electromagnetic windings.
* Hacksaw:  Or some other way to cut lengths of the soft iron rod.
* [Ceramic magnets](https://www.amazon.com/dp/B07S75MD7X?th=1):  Forms the fixed stator fields of the motor.
* [Bearings](https://www.amazon.com/dp/B07B8VZJGD):  Holds the rotor.
* [Carbon motor brushes](https://www.amazon.com/dp/B07CVT2TG8):  Conducts current from a source to the commutator by physical contact.
* [Superglue](https://www.amazon.com/dp/B00ELV2D0Y):  Used in a couple spots to hold parts together (e.g., commutator plates to the rotor).
* [Shrink tubing](https://www.amazon.com/dp/B01MFA3OFA?ref=ppx_yo2ov_dt_b_product_details&th=1):  For soldered connections.
* Thin-gauge wire (e.g., 22 AWG jumper cables as provided in kits like [this](https://www.amazon.com/gp/product/B06W54L7B5/ref=ppx_yo_dt_b_search_asin_title?ie=UTF8&psc=1)):  For providing current to the carbon motor brushes.
* Soldering iron:  Wire connections.
* Solder:  Wire connections.
* [DC power supply](https://www.amazon.com/gp/product/B087LY94T6/ref=ppx_yo_dt_b_search_asin_title?ie=UTF8&th=1):  This is usable depending on the total resistance of the windings. If the resistance is too low because the windings are too small, then this power supply will short and self-disable.
* [DC power jack](https://www.amazon.com/dp/B00QJAW9F4?ref=ppx_yo2ov_dt_b_product_details&th=1):  To connect power from the supply to the carbon motor brushes.
* Lots of patience:  Given all of the parts freshly printed, it likely takes several hours to build and assemble.

Optional but useful
* [Soldering station](https://www.amazon.com/dp/B0BHHVP467?ref=ppx_yo2ov_dt_b_product_details&th=1):  The connections, particularly to the commutator, are challenging without this handy tool.
* [Autoranging multimeter](https://www.amazon.com/s?k=autoranging+multimeter&crid=2RJH49VDBDN9Y&sprefix=autoranging%2Caps%2C68&ref=nb_sb_ss_ts-doa-p_1_11):  Very helpful in checking winding resistance and circuit integrity.

# General Assembly

## Print the Parts

See [here](cad-parts.md) for the 3d-printing tech that I use. Links to part files for particular designs can be found 
below.

## Assemble the Windings

The soft iron winding cores need to leave 10mm exposed after insertion into the holder, as shown below:

![winding-core](brushed-dc-motor/winding-core.png)
 
Insert the iron rod fully into the holder, mark off 10mm exposed, and cut to length. It is important to leave no more 
than 10mm exposed so that the windings clear the stators when rotating. Attach the winding washer to the end of the
core leaving 2mm exposed:

![winding-washer](brushed-dc-motor/winding-washer.png)

This bit on the end will be clamped in a drill when winding the electromagnetic coils. Repeat for all windings. 
Depending on the design (see below), there will be either two or four windings.

Before gluing the winding cores and washers in place, assemble the winding holder on the rotor and ensure that it 
spins freely:

{% include youtubePlayer.html id="DvroBsg1bpU" %}

Add a drop of superglue in the core holder to keep each iron core in place. Once these dry, position the winding 
washers on the ends of their cores. Do not glue them yet, just get them in place as follows:

![washer-starts](brushed-dc-motor/washer-starts.png)

Note that the collar of each washer is facing the inside and not the outside. This is important. Next, for each washer 
in turn, place a small drop of superglue on the inside surface as circled in green below:

![washer-glue](brushed-dc-motor/washer-glue.png)

Move the washer inward while rotating it on the core, such that the glue enters between the core and the washer. When 
done, the washer should leave exactly 2mm of exposed core on the end. To make this easy, print the small spacer part and 
use it to push the washers inward. The spacer has a collar with depth 2mm.

![washer-spacer](brushed-dc-motor/washer-spacer.png)

The assembly should look as follows after the washers are placed and glued:

![washers-complete](brushed-dc-motor/washers-complete.png)

Let everything dry.

## Wind the Electromagnetic Coils

A good strategy here is to clamp the exposed ends of the cores into a drill, and clamp the drill in a vise:

![in-drill](brushed-dc-motor/in-drill.png)

Each washer has a 1mm hole near the central hole as circled in green below:

![washer-hole](brushed-dc-motor/washer-hole.png)

If your 3d printer is sufficiently accurate, then this hole will be present and will accept the 30 AWG enameled magnet
wire. If the hole is not preserved, then you might need to open it up with a pin. The purpose of this hole is to provide 
the magnet wire an exit from the coil and to get the winding started. The coil should look as follows just prior to 
engaging the drill:

Note that a good length of wire has been pulled through the small hole. Now for the tricky part:  the winding direction.
Study up on the "right-hand rule" of electromagnetism. There are many good articles.
[This](https://www.aplusphysics.com/courses/honors/magnets/electromagnetism.html) one is helpful, particularly the 
visual:

![rhr](brushed-dc-motor/2ndRHR.png)

The specific winding direction to use at this point depends on the design you are building. See the three designs below
for winding polarities to use for your design. When you're ready, _slowly_ start the drill and begin winding the coil.
Try to get the layers as even as possible. Fill in the valleys that develop and don't worry about making them perfect.
Stop the drill when the first coil is wound. See the design-specific winding polarities below for how to proceed with 
the coil on the other end.

## Build the Commutator

## Build the Power Circuit

# Two-Stator Two-Coil Design

The files for this design can be downloaded from Thingiverse [here](https://www.thingiverse.com/thing:6153166).

## Winding Polarities

Guide the feed-end of the wire across the winding holder using the notches as guides and then continue winding the other 
end. Do not change the drill direction. Once the other end is complete, secure the wire, leave a good length exposed for 
wiring, and then cut the wire.

(work in progress)

# Two-Stator Four-Coil Design

## Winding Polarities

Guide the feed-end of the wire across the winding holder using the notches as guides and then continue winding the other
end. Do not change the drill direction. Once the other end is complete, secure the wire, leave a good length exposed for 
wiring, and then cut the wire.

(work in progress)

# Four-Stator Four-Coil Design

## Winding Polarities

You will need to reverse the drill before winding the other end. Once the other end is complete, secure the wire, leave 
a good length exposed for wiring, and then cut the wire. Be sure to flip the drill direction before commencing winding 
the other pair of coils.

(work in progress)

# References

1. [Voltage, Current, and Resistance (a basic overview)](https://learn.sparkfun.com/tutorials/voltage-current-resistance-and-ohms-law/all)
2. [Electromagnets](http://www.coolmagnetman.com/magelect.htm):  In particular, the author's [coildata.xls](../manuals/coildata.xls) spreadsheet is a fantastic way to learn about the ingredients of an electromagnet (coil gauge, winding count, current input, gauss output, etc.)
3. [Brushed DC electric motor (Wikipedia)](https://en.wikipedia.org/wiki/Brushed_DC_electric_motor).

Other parts can be found [here](cad-parts.md).