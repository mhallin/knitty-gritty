*************
Knitty-gritty
*************

    Dropbox for knitting machines

----

Knitty-gritty manages your knitting machine patterns. You place all your
pattern images a folder, and this folder will be uploaded to the machine each
time you tell the machine to import patterns. You can of course pre-populate
the folder with patterns downloaded from the machine.

Features
========

* Reads or writes BMP, PNG, and JPEG images.
* Compacts the memory used to avoid gaps (fragmentation!) in memory, allowing
  you to use (almost) 100% of your machine's 32 kb memory.

What Doesn't Work?
------------------

* Adding data to the memo display.
* Validating that the pattern fits within the machine's working memory.

Platform Support
----------------

Only tested on OS X, but should work out of the box on both Windows and Linux
given that you have the software requirements listed below installed. Please
let me know if it does not - preferably with a pull request fixing the issue
:-)

What You Will Need
==================

Hardware:

* Brother KH940 knitting machine. KH930 *might* work but is untested.
* USB FTDI cable connected to the machine.

Software:

* A Python (2.7) installation.
* Preferably a Python virtual environment.

Installation Instructions
=========================

Knitty-gritty is distributed as a Python package. Install it via pip:

.. code-block:: sh

   pip install knitty-gritty

Acknowledgements
================

* The file format/memory dump file format documentation over at STG's
  knittington_ repository was a huge help in writing the parser/serializer.
* Steve Conklin's PDDemulate.py in knitting_machine_ was very useful in
  filling the gaps in Tandy's official floppy drive command documentation.

.. _knittington: https://github.com/stg/knittington
.. _knitting_machine: https://github.com/adafruit/knitting_machine
