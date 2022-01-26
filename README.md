# CARTOreader - lite

[![CI Tests](https://github.com/thomgrand/cartoreader-lite/actions/workflows/python-package.yml/badge.svg)](https://github.com/thomgrand/cartoreader-lite/actions/workflows/python-package.yml)
[![codecov](https://codecov.io/gh/thomgrand/cartoreader-lite/branch/main/graph/badge.svg?token=4A7DD8DWXW)](https://codecov.io/gh/thomgrand/cartoreader-lite)

This repository is an inofficial reader to easily process exported [CARTO3 data](https://www.jnjmedicaldevices.com/en-US/product/carto-3-system) in Python.
It does not provide the more extensive capabilities to analyze the signals, such as [OpenEP](https://openep.io/), but is rather meant as a simple reader to import CARTO data. 
The loaded time data is imported in [pandas](https://pandas.pydata.org) and the meshes in [VTK](https://vtk.org/) provided through [PyVista](https://www.pyvista.org), allowing for easy access, export and interoperatibility with existing software.

# Installation

To install `cartoreader_lite`, you have to clone the repository and install the libary using `pip`.

```bash    
git clone https://github.com/thomgrand/cartoreader-lite
cd cartoreader-lite
pip install -e .
```

# Usage

To test the library, you first need to get CARTO3 data. 
None is provided with this repository, but you can download the testing data provided by [OpenEP](https://openep) to quickly try out the library (make sure the libary was installed first):

```bash
python tests/generate_test_data.py
```

```python
from cartoreader_lite import CartoStudy
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
```

You should see the recorded map of the [OpenEP](https://openep.io) example, together with its recorded points like below.

![openep-example](docs/figures/openep-example.png)

# Documentation

[https://cartoreader-lite.readthedocs.io/en/latest](https://cartoreader-lite.readthedocs.io/en/latest)

# Citation

If you use the library in your scientific projects, please cite the associated Zenodo archive: https://www.zenodo.org.

```bibtex
%TODO: FIM
@software{thomas_grandits_2021_5594452,
  author       = {Thomas Grandits},
  title        = {A Fast Iterative Method Python package},
  month        = oct,
  year         = 2021,
  publisher    = {Zenodo},
  version      = {1.1},
  doi          = {10.5281/zenodo.5594452},
  url          = {https://doi.org/10.5281/zenodo.5594452}
}
```
