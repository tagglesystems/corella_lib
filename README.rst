Corella
=======

.. image:: https://c2.staticflickr.com/4/3820/19822349529_b3c3316fcc.jpg

The Corella Low Power Wide Area Network (LPWAN) module allows developers to connect a range of IoT devices to the Taggle network.

The Taggle network is an LPWAN solution based on world leading Australian developed technology operating in the 916-928MHz Low Interference Potential Device (LIPD) class licence band, which has been developed by Taggle Systems to provide one of the lowest cost, lowest power, longest range, and highest capacity LPWAN solutions available. The Taggle network is based on one-way transmissions from endpoint nodes to the Taggle receiver network, and is particularly well suited to battery powered endpoint applications with low data rate requirements, such as automatic meter reading, wireless sensors for smart agriculture and environmental monitoring, and cost sensitive smart city applications.

Corella is based on the popular XBee module format, and provides a single serial port with a simple "AT" command style interface to allow rapid integration of the module into both lab prototypes and volume production IoT devices. The module has a single radio transmit output via an SMA connector, and can be supplied with a 2dBi - wave dipole antenna to enable rapid connection to the Taggle network.

All receive functions are handled seamlessly by the Taggle network, with the user's receive data presented via a custom web portal. A range of data plans are available depending on the number of endpoints connected to the Taggle network and the frequency of messages per endpoint.

Requirements
============

corella_lib requires Python >= 3.5.

Installation
============

To install corella_lib, simply use `pip <https://pip.pypa.io/>`_:

.. code-block:: bash

    $ pip install corella_lib

Usage
=====

.. code-block:: python

    # Import Corella
    from corella_lib.serial import Corella

    # Initialize Corella
    corella = Corella('<device-port-goes-here>')

    # Send a message through Taggle network with packet ID
    corella.send(<packet-id-goes-here>, '<12-bytes-data-goes-here>')

Examples
========

.. code-block:: python

    # Initialize Corella
    >>> corella = Corella('/dev/ttyAMA0')

.. code-block:: python

    # Send a message through Taggle network with packet ID 2
    >>> corella.send(2, 'temp:23C')
    True

.. code-block:: python

    # Check if the device is connected
    >>> corella.connected
    True

.. code-block:: python

    # Get device ID
    >>> corella.id
    '130065'

.. code-block:: python

    # Get device version information
    >>> corella.version
    {'F.W': '1.1.01', 'H.W': 'REV_A'}

.. code-block:: python

    # Get device firmware version
    >>> corella.firmware_version
    '1.0.31'

.. code-block:: python

    # Get device hardware version
    >>> corella.hardware_version
    'REV_A'

.. code-block:: python

    # Get device diagnostics information
    >>> corella.diagnostics
    {'CURR_TEMP': '32', 'BATT': '3.21V', 'MAX_TEMP': '58', 'MIN_TEMP': '31'}

.. code-block:: python

    # Get device supply voltage
    >>> corella.battery
    3.21

.. code-block:: python

    # Get device current temperature in degrees Celsius
    >>> corella.curr_temp
    58.0

.. code-block:: python

    # Get device max temperature in degrees Celsius
    >>> corella.max_temp
    58.0

.. code-block:: python

    # Get device min temperature in degrees Celsius
    >>> corella.min_temp
    31.0

.. code-block:: python

    # Turn off device LEDs
    >>> corella.turn_off_leds()
    True

.. code-block:: python

    # Turn on device LEDs
    >>> corella.turn_on_leds()
    True

Documentation
=============

Documentation is available at http://corella.taggle.com.au.
