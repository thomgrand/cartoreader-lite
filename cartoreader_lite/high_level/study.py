from __future__ import annotations #recursive type hinting
import logging as log
import pickle
from typing import Dict, List, Tuple, IO, Union

from cartoreader_lite.low_level.utils import convert_fname_to_handle, simplify_dataframe_dtypes, unify_time_data, xyz_to_pos_vec
from ..low_level.study import CartoLLStudy, CartoLLMap, CartoAuxMesh
import pandas as pd
import numpy as np
import re
import gzip
from os import PathLike
import os
import pyvista as pv
from ..postprocessing.geometry import project_points

dtype_simplify_dict = {"InAccurateSeverity": np.int8,
                        "ChannelID": np.int32,
                        "MetalSeverity": np.int8,
                        "NeedZeroing": np.int8,
                        "ChannelID": np.int16,
                        "TagIndexStatus": np.int8,
                        "Valid": np.int8}

#np.iinfo(np.int8)
#np.issubdtype(np.int8, np.integer)

class AblationSites():
    """High level class for easily referencing ablation sites read from the visitag files.
    Automatically generated from :class:`.CartoStudy`.

    Parameters
    ----------
    visitag_data : Dict[str, pd.DataFrame]
        Visitag data read by the low level function :ref:`.low_level.visitags.read_visitag_dir`.
    resample_unified_time : bool, optional
        If true, the visitag file with different time intervals and frequencies will be resampled into a single pandas Dataframe with unified time steps.
        By default True
    position_to_vec : bool, optional
        If true, the entries X, Y, Z of the dataframes will be unified in the resulting tables to a single 3D vector pos.
        By default, True
    """

    session_avg_data : pd.DataFrame #: Contains average data of each ablation session, such as :term:`RFIndex`, average force and position
    session_time_data : List[Tuple[int, pd.DataFrame]] #: List of time data associated with each Ablation session. Each item contains the session ID + the ablation data over the course of the session
    session_rf_data : List[Tuple[int, pd.DataFrame]] = None #: Ablation data (impedance, power, temperature, ...) provided by the low level classes. Only present if `resample_unified_time` was False
    session_force_data : List[Tuple[int, pd.DataFrame]] = None #: Force data provided by the low level classes. Only present if `resample_unified_time` was False

    def __init__(self, visitag_data : Dict[str, pd.DataFrame], resample_unified_time=True,
                 position_to_vec=True) -> None:
                 
        if resample_unified_time:
            #Contact force data uses a different time label, but the timings look the same as the other data
            contact_force_data = visitag_data["ContactForceData"].rename(columns={"Time": "TimeStamp"})
            time_data = unify_time_data([visitag_data["RawPositions"], visitag_data["AblationData"], contact_force_data], time_k="TimeStamp", 
                                         time_interval=100, kind="quadratic")
            self.session_time_data = list(simplify_dataframe_dtypes(time_data, dtype_simplify_dict).groupby("Session"))
            
        else:
            self.session_time_data = list(simplify_dataframe_dtypes(visitag_data["RawPositions"], dtype_simplify_dict).groupby("Session"))
            self.session_rf_data = list(simplify_dataframe_dtypes(visitag_data["AblationData"], dtype_simplify_dict).groupby("Session"))
            self.session_force_data = list(simplify_dataframe_dtypes(visitag_data["ContactForceData"], dtype_simplify_dict).groupby("Session"))

        self.session_avg_data = simplify_dataframe_dtypes(visitag_data["Sites"], dtype_simplify_dict)

        if position_to_vec:
            self.session_avg_data = xyz_to_pos_vec(self.session_avg_data)
            self.session_time_data = [(session_id, xyz_to_pos_vec(time_data)) for session_id, time_data in self.session_time_data]

ecg_gain_re = re.compile("\s*Raw ECG to MV \(gain\)\s*\=\s*(-?\d+\.?\d*)\s*")
ecg_labels = ["I", "II", "III", "aVR", "aVL", "aVF"] + [f"V{i+1}" for i in range(6)]
ecg_labels_re = [re.compile(l + "\(\d+\)") for l in ecg_labels]
egm_label_re = re.compile("(.+)\((\d+)\)")

class CartoPointDetailData():
    """Detailed data associated to a CARTO3 point.

    Parameters
    ----------
    main_data : pd.Series
        Metadata of the point, such as ID and mean position
    raw_data : Tuple[Dict[str, Dict], Dict[str, Dict]]
        Raw data provided by :class:`cartoreader_lite.low_level.study.CartoLLMap`, including details such as :term:`EGMs<EGM>`.
    remove_egm_header_numbers : bool, optional
        If true, the :term:`EGM` header numbers will be discarded (e.g. I(110) -> I).
        By default True
    """

    id : int #: Carto generated ID of the point
    pos : np.ndarray #: Position of the point in 3D
    cath_orientation : np.ndarray #: 3D-Orientation of the catheter while recording the point
    cath_id : int #: ID of the Catheter
    woi : np.ndarray #: :term:`WOI`. Only recordings located in this window are deemed valid.
    start_time : int #: System start time of the recording
    ref_annotation : int #: Reference annotation to synchronize all recordings
    map_annotation : int #: Annotation of the activation of this point, also often called :term:`LAT`
    uni_volt : float #: Unipolar voltage magnitdue
    bip_volt : float #: Bipolar voltage magnitdue    
    connectors : List[str] #: List of the recorded connector names
    ecg_gain : float #: Gain of the recorded :term:`ECGs<ECG>`
    ecg_metadata : object #: Additional provided metadata regarding the :term:`ECGs<ECG>` or :term:`EGMs<EGM>`
    surface_ecg : pd.DataFrame #: Recorded surface :term:`ECG`. Has type np.int16 and needs to be multiplied by :attr:`~CartoPointDetailData.ecg_gain` to get the ECG in Volts
    egm : pd.DataFrame #: Recorded electrograms at the point through the connectors. Naming and columns differ for each setup

    def __init__(self, main_data : pd.Series, raw_data : Tuple[Dict[str, Dict], Dict[str, Dict]],
                remove_egm_header_numbers=True) -> None:

        #Read the easy metadata first
        self.id = main_data["Id"]
        self.pos = main_data["Position3D"]
        self.cath_orientation = main_data["CathOrientation"]
        self.cath_id = main_data["Cath_Id"]

        #Metadata is the first tuple object, actual data in the second tuple
        #WOI
        self.woi = np.array([float(raw_data[0]["WOI"]["From"]), float(raw_data[0]["WOI"]["To"])])
        self.start_time = int(raw_data[0]["Annotations"]["StartTime"])
        self.ref_annotation = int(raw_data[0]["Annotations"]["Reference_Annotation"])
        self.map_annotation = int(raw_data[0]["Annotations"]["Map_Annotation"])

        #Voltages
        self.uni_volt = float(raw_data[0]["Voltages"]["Unipolar"])
        self.bip_volt = float(raw_data[0]["Voltages"]["Bipolar"])

        #Connectors
        self.connectors = list(raw_data[1]["connector_data"].keys())

        #Contact Forces
        if "contact_force_data" in raw_data[1]:
            self.contact_force_metadata, self.contact_force_data = raw_data[1]["contact_force_data"]
            self.contact_force_data = simplify_dataframe_dtypes(self.contact_force_data, dtype_simplify_dict)

        #TODO: Not yet sure what the OnAnnotation file does

        #ECG
        ecg_gain_str = raw_data[1]["ecg"][0][1] #Pass ECG metadata
        self.ecg_gain = float(ecg_gain_re.match(ecg_gain_str).group(1))
        self.ecg_metadata = raw_data[1]["ecg"][0][2]
        #self.ecg_export_version_number = data[1]["ecg"][0][0]""
        ecg_data = raw_data[1]["ecg"][1]
        assert np.iinfo(np.int16).min <= ecg_data.min().min() and np.iinfo(np.int16).max >= ecg_data.max().max(), "ECG can not be simplified to np.in16"
        ecg_data = ecg_data.astype(np.int16)

        #Find the surface ECGs in the data and split the data into surface and other EGMs
        surface_ecg_inds = [[j for j, c in enumerate(ecg_data.columns) if l.match(c) is not None] for l in ecg_labels_re]
        assert all([len(l) == 1 for l in surface_ecg_inds]), "12-lead ECG not present in the point data"
        surface_ecg_inds = [l[0] for l in surface_ecg_inds]
        self.surface_ecg = ecg_data.iloc[:, surface_ecg_inds]
        self.egm = ecg_data.drop(ecg_data.columns[surface_ecg_inds], axis=1)

        #Remove the numbers after electrode description numbering
        if remove_egm_header_numbers:
            self.surface_ecg.columns = np.array(ecg_labels) 
            self.egm.columns = np.array([egm_label_re.match(col).group(1) for col in self.egm.columns])

    @property
    def main_point_pd_row(self):
        pd_attrs = ["id", "pos", "cath_orientation", "cath_id", "woi", "start_time", "ref_annotation", 
                    "map_annotation", "uni_volt", "bip_volt", "connectors",
                    ] #"surface_ecg", "egm"]

        #This represents a single row of the returning pandas DataFrame
        return {**{k: getattr(self, k) for k in pd_attrs}, **{"detail": self}}

class CartoMap():

    """High level container for carto maps with the associated point data and mesh.

    Parameters
    ----------
    ll_map : CartoLLMap
        The low level study to load and simplify
    """

    points : pd.DataFrame #: Recorded point data associated with this map. The column `detail` returns the associated :class:`CartoPointDetailData` where the ECGs and EGMs can be found.
    mesh : pv.UnstructuredGrid #: Mesh associated with the map

    def _simplify(self, ll_map : CartoLLMap, discard_invalid_points=True, remove_egm_header_numbers=True,
                        proj_points=True):
        """Function to simplify the data given by the lower level ll_map.

        Parameters
        ----------
        ll_map : CartoLLMap
            Data of the low level map to be simplified into this high level map
        discard_invalid_points : bool, optional
            If true, points with :term:`LAT` outside the :term:`WOI` will be automatically discarded.
            By default True
        """
        self.name = ll_map.name

        #Point data
        if len(ll_map.points_main_data) > 0:
            self._points_raw = np.array([CartoPointDetailData(main_data, raw_data, remove_egm_header_numbers) for (row_i, main_data), raw_data in zip(ll_map.points_main_data.iterrows(), ll_map.point_raw_data)])
            self.points = pd.DataFrame([p.main_point_pd_row for p in self._points_raw])

            if discard_invalid_points:
                corrected_woi = np.stack((self.points.woi + self.points.ref_annotation).to_numpy())
                lat = self.points.map_annotation
                valid_mask = (lat >= corrected_woi[..., 0]) & (lat <= corrected_woi[..., 1])
                log.info(f"Discarding {np.sum(~valid_mask)}/{valid_mask.size} invalid points in map {self.name} (LAT outside WOI)")
                self._points_raw = self._points_raw[valid_mask]
                self.points = self.points[valid_mask].reset_index(drop=True)
        else:
            self.points = self._points_raw = []


        #Mesh data
        self.mesh = ll_map.mesh
        self.mesh_affine = np.fromstring(ll_map.mesh_metadata["Matrix"], sep=" ").reshape([4, 4])
        assert self.mesh.n_points == int(ll_map.mesh_metadata["NumVertex"]), "Metadata and mesh mismatch"
        assert self.mesh.n_cells == int(ll_map.mesh_metadata["NumTriangle"]), "Metadata and mesh mismatch"

        #Project points onto the geometry
        if proj_points:
            if len(self.points) > 0:
                proj_points, proj_dist = project_points(self.mesh, np.stack(self.points["pos"].to_numpy()))[:2]
                self.points["proj_pos"] = proj_points.tolist()
                self.points["proj_dist"] = proj_dist

            elif type(self.points) == pd.DataFrame: #Add empty columns just to be consistent
                self.points["proj_pos"] = []
                self.points["proj_dist"] = []

    @property
    def nr_points(self):
        return len(self.points)

    def __init__(self, ll_map : CartoLLMap, *simplify_args, **simplify_kwargs) -> None:
        #self.ll_map = ll_map
        self._simplify(ll_map, *simplify_args, **simplify_kwargs)
        #del self.ll_map

class CartoStudy():
    """High level class to easily read Carto3 archives, directories or buffered studies.

        Parameters
        ----------
        arg1 : str
            A path to either

                * A directory containing the study
                * A zip file with the study inside
                * A path to a previously saved study
                * A :class:`cartoreader_lite.low_level.study.CartoLLStudy` instance
        arg2 : str, optional
            The name of the study to load, contained inside the directory or zip file.
            Has to be None when loading a pickled study.
            Will default to either the zip name, bottom most directory name or None, depending on your choice of arg1.
        ablation_sites_kwargs : Dict
            Optional keyword arguments to be passed to :class:`AblationSites`
        carto_map_kwargs : Dict
            Optional keyword arguments to be passed to :class:`CartoMap`
    """

    name : str #: The name of the study
    ablation_data : AblationSites #: Detailed information about the ablation sites and their readings over time
    maps : List[CartoMap] #: All recorded maps associated with this study
    aux_meshes : List[CartoAuxMesh] #: Auxiliary meshes generated by the CARTO system, not associated with any specific map, e.g. CT segmentations from `CARTOSeg`_.
    aux_mesh_reg_mat : np.ndarray #: 4x4 affine registration matrix to map the auxiliary meshes.

    
    def _simplify(self, ll_study : CartoLLStudy, ablation_sites_kwargs : Dict, carto_map_kwargs : Dict):
        """Function to simplify the data given by the lower level ll_study.

        Parameters
        ----------
        ll_study : CartoLLStudy
            Data of the low level study to be simplified into this high level study
        ablation_sites_kwargs : Dict
            Optional keyword arguments to be passed to :class:`AblationSites`
        carto_map_kwargs : Dict
            Optional keyword arguments to be passed to :class:`CartoMap`
        """
        self.ablation_data = AblationSites(ll_study.visitag_data, **ablation_sites_kwargs)
        self.maps = [CartoMap(m, **carto_map_kwargs) for m in ll_study.maps]
        self.name = ll_study.name
        self.aux_meshes = ll_study.aux_meshes
        self.aux_mesh_reg_mat = ll_study.aux_mesh_reg_mat

    def __init__(self, arg1, arg2 = None, ablation_sites_kwargs=None, carto_map_kwargs=None) -> None:

        if ablation_sites_kwargs is None:
            ablation_sites_kwargs = {}
        if carto_map_kwargs is None:
            carto_map_kwargs = {}

        if issubclass(type(arg1), str) and os.path.isfile(arg1) and arg1.endswith(".pkl.gz") and arg2 is None:
            loaded_study = CartoStudy.load_pickled_study(arg1)

            #https://stackoverflow.com/questions/2709800/how-to-pickle-yourself
            self.__dict__.update(loaded_study.__dict__)
        elif issubclass(type(arg1), CartoLLStudy) and arg2 is None:
            ll_study = arg1
            self._simplify(ll_study, ablation_sites_kwargs, carto_map_kwargs)

        else:
            ll_study = CartoLLStudy(arg1, arg2)
            self._simplify(ll_study, ablation_sites_kwargs, carto_map_kwargs)

    @property
    def nr_maps(self):
        return len(self.maps)

    def save(self, file : Union[IO, PathLike] = None):
        """Backup the current study into a pickled and compressed file or buffer.

        Parameters
        ----------
        file : Union[IO, PathLike], optional
            Target to write the study to. Can be on of the following:
            
                * Name of the file which the study will be written to
                * A file, or buffer handle to write to
                
            Will default to the study name with the ending `.pkl.gz`
        """
        if file is None:
            file = self.name + ".pkl.gz"

        assert not issubclass(type(file), str) or file.endswith("pkl.gz"), "Only allowed file type is currently pkl.gz"
        file, is_fname = convert_fname_to_handle(file, "wb")

        with gzip.GzipFile(fileobj=file, mode="wb", compresslevel=2) as g_h:
            pickle.dump(self, g_h)
            
        if is_fname:
            file.close()

    @staticmethod
    def load_pickled_study(file : Union[IO, PathLike]) -> CartoStudy:
        """Will load a pickled study either from 

        Parameters
        ----------
        file : Union[IO, PathLike]
            [description]

        Returns
        -------
        CartoStudy
            [description]
        """
        assert not issubclass(type(file), str) or file.endswith("pkl.gz"), "Only allowed file type is currently pkl.gz"
        file, is_fname = convert_fname_to_handle(file, "rb")
        with gzip.GzipFile(fileobj=file, mode="rb") as f:
            data = pickle.load(f)       

        if is_fname:
            file.close()

        assert issubclass(type(data), CartoStudy), "Unexpected unpickling result"
        return data
