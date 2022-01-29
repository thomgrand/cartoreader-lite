.. Cartoreader Lite documentation master file, created by
   sphinx-quickstart on Wed Jan 19 14:57:28 2022.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Cartoreader Lite's documentation
======================================

.. contents:: Quick Start
    :depth: 3


Introduction
-------------

This repository is an inofficial reader to easily process exported `CARTO3 data <https://www.jnjmedicaldevices.com/en-US/product/carto-3-system>`_ in Python.
It does not provide the more extensive capabilities to analyze the signals, such as `OpenEP`_, but is rather meant as a simple reader to import CARTO data. 
The loaded time data is imported in `pandas <https://pandas.pydata.org>`_ and the meshes in `VTK <https://vtk.org/>`_ provided through `PyVista <https://www.pyvista.org>`_, allowing for easy access, export and interoperatibility with existing software.


CARTO3 System
---------------
The read file format is the output of the CARTO3 system, which is used as an electrical mapping device for guiding catheter ablation and catheter synchronization therapy.
For more details, please read the official website of Biosense Webster (https://www.jnjmedicaldevices.com/en-US/product/carto-3-system).

   **Carto3 System**    

   *CARTO 3 System Version 7 and the CARTO PRIME® Module offers advancement in 3D mapping technology. From signals to diagnosis, across a wide range of electrophysiology procedures, we are reframing the future of electrophysiology.*


A short description can also be found in this documentation at :ref:`file_format`.

Installation
-------------

.. include:: installation.inc

Usage
------

.. include:: example.inc

Citation
------------

If you use the library in your scientific projects, please cite the associated Zenodo archive: https://zenodo.org/record/5918396.

.. code-block:: bibtex

   @software{grandits_2022_5918396,
      author       = {Thomas Grandits},
      title        = {CARTOreader - lite},
      month        = jan,
      year         = 2022,
      publisher    = {Zenodo},
      version      = {v1.0.1},
      doi          = {10.5281/zenodo.5918396},
      url          = {https://doi.org/10.5281/zenodo.5918396}
   }


Detailed Content
-----------------
.. toctree::
   :maxdepth: 2

   interface.rst
   design.rst

Module API
--------------

.. autosummary::
   :toctree: _autosummary
   :recursive:
   :caption: Module API

   cartoreader_lite

.. include::
   glossary.rst

Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
