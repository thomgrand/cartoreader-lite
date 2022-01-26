.. _file_format:

CARTO3 File Format
==================

This document contains information and a few pointers on the terminology used both inside the CARTO3 file format and also in this library.
There's also a replicating python class associated to each of these parts that will hold the information after reading (listed at the bottom of the section).

.. warning::

    The information provided in this document is not an official documentation of the proprietary data format. 
    As such, the information is merely meant as a guideline to better understand the available data for scientific purposes. 
    It is in no way a complete and error free documentation that can be used in production, yet alone medical devices.
    **No** warranty is provided that the given information is complete or error-free.

Study
----------

The highest abstraction level of the CARTO3 system is a study and the entry point of `cartoreader-lite itself`.
It can contain an arbitrary combination of multiple:

    - `Maps <#map>`_
    - `Visitags <#visitag>`_
    - `Auxiliary Meshes <#auxiliary-mesh>`_

Associated class: :class:`.CartoStudy`.

Map
----------

During a study, multiple maps a generated according to the need of the attending staff (e.g. pre- and post ablation).
Each map contains:

    - A mesh with which to associate the recordings
    - Multiple `points <#point>`_ with electrical recordings. These are not registered to the mesh

Associated class: :class:`.CartoMap`.

Point
-----------

Each point represents an electrical recording at a single location.
A point contains not just the position, but also :term:`ECG` and :term:`EGM` readings over time.

Associated class: :class:`.CartoPointDetailData`.

Visitag
----------

Visitag sites store information about the ablation sites.

Associated class: :class:`.AblationSites`

Auxiliary Mesh
------------------

Additional meshes exported by CARTO3, e.g. by `CartoSeg`_.

Associated class :class:`.CartoAuxMesh`
