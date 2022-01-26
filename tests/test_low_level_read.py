from cartoreader_lite.low_level.study import CartoLLStudy, _parallelize_pool
from concurrent.futures import ThreadPoolExecutor
import pyvista as pv
import numpy as np
import pytest

"""
@pytest.fixture()
def prepare_lib():
    global _parallelize_pool
    _parallelize_pool = ThreadPoolExecutor
    yield None
"""

def low_level_sanity_check(study):
    assert len(study.maps) == 4
    assert study.maps[0].name == "1-Map"

    map2 = study.maps[2]
    assert len(map2.point_raw_data) == 2
    point_data = map2.points_main_data
    assert "Position3D" in point_data
    assert "CathOrientation" in point_data
    assert hasattr(map2, "mesh") and type(map2.mesh) == pv.UnstructuredGrid and map2.mesh.n_cells >= 5e3 and map2.mesh.n_points >= 2e3
    assert hasattr(map2, "mesh_metadata") and "MeshName" in map2.mesh_metadata

class TestLowLevelCartoReader():

    def test_from_dir(self):
        study_dir = "openep-testingdata/Carto/Export_Study-1-11_25_2021-15-01-32"
        study_name = "Study 1 11_25_2021 15-01-32.xml"
        study = CartoLLStudy(study_dir, study_name)
        low_level_sanity_check(study)

    def test_from_zip(self):
        study_dir = "openep-testingdata.zip"
        study_name = "Carto/Export_Study-1-11_25_2021-15-01-32/Study 1 11_25_2021 15-01-32.xml"
        study = CartoLLStudy(study_dir, study_name)
        low_level_sanity_check(study)
        
    def test_invalid_args(self):
        with pytest.raises(Exception):
            study = CartoLLStudy([5, 4, 3])

        with pytest.raises(Exception):
            study = CartoLLStudy("N/A File")
