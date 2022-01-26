import pytest
from cartoreader_lite import CartoStudy
from cartoreader_lite.low_level.study import _parallelize_pool, CartoLLStudy
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
import pandas as pd
import pickle

"""
def prepare_lib():
    global _parallelize_pool
    print("Setup")
    _parallelize_pool = ThreadPoolExecutor
    yield None
    print("Teardown")
"""

def compare_studies(study1 : CartoStudy, study2 : CartoStudy):
    assert len(study1.maps) == len(study2.maps)
    assert all([m1.name == m2.name for m1, m2 in zip(study1.maps, study2.maps)])

class TestHighLevelCartoReader():

    def test_openep_example(self):
        #prepare_lib()
        study_dir = "openep-testingdata/Carto/Export_Study-1-11_25_2021-15-01-32"
        study_name = "Study 1 11_25_2021 15-01-32.xml"
        study = CartoStudy(study_dir, study_name, carto_map_kwargs={"discard_invalid_points": False})

        study.save("test_study.pkl.gz")
        study_restored = CartoStudy.load_pickled_study("test_study.pkl.gz")
        compare_studies(study, study_restored)

        study_restored = CartoStudy("test_study.pkl.gz") #Test direct constructor
        compare_studies(study, study_restored)
        
        #Default arguments
        study.save()
        study_restored = CartoStudy.load_pickled_study(f"{study.name}.pkl.gz")
        compare_studies(study, study_restored)

        #Save into a stream
        with BytesIO() as bytes:
            study.save(bytes)
            bytes.seek(0)
            study_restored = CartoStudy.load_pickled_study(bytes)

        compare_studies(study, study_restored)

    def test_openep_optional_kwargs(self):
        #prepare_lib()
        study_dir = "openep-testingdata/Carto/Export_Study-1-11_25_2021-15-01-32"
        study_name = "Study 1 11_25_2021 15-01-32" #Try without the file ending
        ll_study = CartoLLStudy(study_dir, study_name)
        ll_study_bak = pickle.dumps(ll_study)
        study = CartoStudy(ll_study)

        points = study.maps[2].points
        assert type(points) == pd.DataFrame and len(points) == 0 #All points were discarded

        #Don't unify time
        ll_study = pickle.loads(ll_study_bak)
        study = CartoStudy(ll_study, ablation_sites_kwargs={"resample_unified_time": False})
        assert hasattr(study.ablation_data, "session_rf_data") and type(study.ablation_data.session_rf_data) == list and len(study.ablation_data.session_rf_data) > 0 and type(study.ablation_data.session_rf_data[0][1]) == pd.DataFrame
        assert hasattr(study.ablation_data, "session_force_data") and type(study.ablation_data.session_force_data) == list and len(study.ablation_data.session_force_data) > 0 and type(study.ablation_data.session_force_data[0][1]) == pd.DataFrame
        assert "pos" in study.ablation_data.session_time_data[0][1]

        #Leave the position vector as X, Y, Z
        ll_study = pickle.loads(ll_study_bak)
        study = CartoStudy(ll_study, ablation_sites_kwargs={"resample_unified_time": False, "position_to_vec": False})
        assert hasattr(study.ablation_data, "session_time_data") and type(study.ablation_data.session_time_data) == list and len(study.ablation_data.session_time_data) > 0 and type(study.ablation_data.session_time_data[0][1]) == pd.DataFrame
        assert all([n in study.ablation_data.session_time_data[0][1] for n in ["X", "Y", "Z"]])

        #Leave the EGM header numbers in the frame
        ll_study = pickle.loads(ll_study_bak)
        study = CartoStudy(ll_study, carto_map_kwargs={"remove_egm_header_numbers": False, "discard_invalid_points": False})
        egms = study.maps[2].points.detail[0].egm
        ecgs = study.maps[2].points.detail[0].surface_ecg
        assert all(["(" in col for col in egms.columns])
        assert all(["(" in col for col in ecgs.columns])

        ll_study = pickle.loads(ll_study_bak)
        study = CartoStudy(ll_study, carto_map_kwargs={"remove_egm_header_numbers": True, "discard_invalid_points": False})
        egms = study.maps[2].points.detail[0].egm
        ecgs = study.maps[2].points.detail[0].surface_ecg
        assert all(["(" not in col for col in egms.columns])
        assert all(["(" not in col for col in ecgs.columns])
        assert "proj_pos" in points #Check for the projection of the points
        assert "proj_dist" in points 

        ll_study = pickle.loads(ll_study_bak)
        study = CartoStudy(ll_study, carto_map_kwargs={"discard_invalid_points": False, "proj_points": False})
        points = study.maps[2].points
        assert "proj_pos" not in points #Check that the projection was not performed
        assert "proj_dist" not in points 
