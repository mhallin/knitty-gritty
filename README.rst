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

If that completed successfully, you will now have a ``knitty-gritty``
executable, ready to do its thing!

Downloading Patterns from the Machine
-------------------------------------

.. code-block:: sh

   # First, find your USB cable:
   ls /dev/tty.usbserial-*

   # Replace the file below with the name you found
   # The last parameter `patterns` is the folder where your patterns should be saved
   knitty-gritty emulate-folder /dev/tty.usbserial-A7XTW5YZ patterns

If this is the first time you run knitty-gritty, you should download all
patterns from the machine first. On a KH940, this is done by entering ``CE``,
``552``, ``STEP``, ``1``, ``STEP``. When this is done, the machine should beep
(as it always does). Quit Knitty-gritty by pressing Control-C. The pattern
images should appear in the folder you specified.

Now you can modify/add/remove patterns as much as you like. Just drop them in
the folder together with the other patterns.

Uploading Patterns
------------------

When you're done with fiddling with the images, you should upload them:

.. code-block:: sh

   # Replace the TTY-parameter with the cable you found above.
   knitty-gritty emulate-folder --no-save /dev/tty.usbserial-A7XTW5YZ patterns

The ``--no-save`` argument tells Knitty-gritty to not save any files to the
folder on the computer. This is a safeguard against removing/overwriting
patterns if anything goes wrong.

To load the patterns on the machine, enter ``CE``, ``551``, ``STEP``, ``1``,
``STEP`` and wait until it beeps.

Acknowledgements
================

* The file format/memory dump file format documentation over at STG's
  knittington_ repository was a huge help in writing the parser/serializer.
* Steve Conklin's PDDemulate.py in knitting_machine_ was very useful in
  filling the gaps in Tandy's official floppy drive command documentation.

.. _knittington: https://github.com/stg/knittington
.. _knitting_machine: https://github.com/adafruit/knitting_machine
