To test the library, you first need to get CARTO3 data. 
None is provided with this repository, but you can download the testing data provided by `OpenEP`_ to quickly try out the library (make sure the libary was installed first):

.. code-block:: bash

    python tests/generate_test_data.py


.. code-block:: python
    
    from cartoreader_lite import CartoStudy
    import pyvista as pv
    import numpy as np
    
    study_dir = "openep-testingdata/Carto/Export_Study-1-11_25_2021-15-01-32"
    study_name = "Study 1 11_25_2021 15-01-32.xml"
    study = CartoStudy(study_dir, study_name, 
                    carto_map_kwargs={"discard_invalid_points": False} #All points of the example are outside the WOI, which would be by default discarded
                    )
    ablation_points = pv.PolyData(np.stack(study.ablation_data.session_avg_data["pos"].to_numpy()))
    ablation_points.point_data["RFIndex"] = study.ablation_data.session_avg_data["RFIndex"]
    plotter = pv.Plotter()
    plotter.add_mesh(ablation_points, cmap="jet")
    plotter.add_mesh(study.maps[2].mesh)
    plotter.show()
    
You should see the recorded map of the `OpenEP`_ example, together with its recorded points like below.

.. image:: figures/openep-example.png

`cartoreader_lite` also offers the possibility to directly load the CARTO3 exported zip-files.
For the zipped `OpenEP`_ testing data, this would like the following:

.. code-block:: python

    study_dir = "openep-testingdata.zip"
    study_name = "Carto/Export_Study-1-11_25_2021-15-01-32/Study 1 11_25_2021 15-01-32.xml"
    study = CartoStudy(study_dir, study_name)

Buffering
-----------
Loading the CARTO3 study is heavy on the CPU, which is why it is often useful to backup your studies.
This can be easily achieved through the :meth:`cartoreader_lite.CartoStudy.save` method

.. code-block:: python

    bak_name = "Study 1 11_25_2021 15-01-32.pkl.gz"
    study.save(bak_name)
    study_bak = CartoStudy(bak_name)
