"""Utility functions to more easily read and write the CARTO3 files on a low level.
"""

from typing import Iterable, List, Dict, Tuple, IO, Union
import pandas as pd
import xml.etree.ElementTree as ET 
from xml.etree.ElementTree import Element
import os
from collections import defaultdict
import re
from os import PathLike
import numpy as np
from scipy.interpolate import interp1d
from scipy.spatial import cKDTree

multi_whitespace_re = re.compile("\s\s+")

def read_connectors(xml_elem : Element, path_prefix : str) -> Dict[str, List[pd.DataFrame]]:
    """Reads connector data from the main XML element, pointing to multiple files with the attached connector data.

    Parameters
    ----------
    xml_elem : Element
        The XML Connector element where the data will be found
    path_prefix : str
        The path prefix where to search for the connector files

    Returns
    -------
    Dict[str, List[pd.DataFrame]]
        A dictionary mapping from the connector names to the associated pandas DataFrames that will contain the connector data.
    """
    connectors = defaultdict(lambda: [])
    for connector in xml_elem:
        assert connector.tag == f"Connector", "Non connector XML element found ({connector.tag})"
        assert len(connector.attrib.keys()) == 1, f"More than one attribute found for connector: {connector.attrib:s}"
        k, fname = list(connector.items())[0]
        full_fname = os.path.join(path_prefix, fname)
        with open(full_fname, "r") as f:
            metadata = (os.path.splitext(fname)[0], f.readline().strip())
            connectors[k].append((metadata, pd.read_csv(f, sep="\s+"))) #skiprows=1))) #Not necessary to skiprows if we don't seek to the beginning

    return dict(connectors)

def read_contact_force(fname : str) -> pd.DataFrame:
    with open(fname, "r") as f:
        metadata = [f.readline().strip() for i in range(7)]
        data = pd.read_csv(f, sep="\s+")

    return metadata, data

def read_point_data(map_name : str, point_id : int, path_prefix : str = None) -> Tuple[Dict, Dict]:
    """Reads all the available point data for given map and point ID, along with its metadata.

    Parameters
    ----------
    map_name : str
        Name of the map
    point_id : int
        Point ID to read
    path_prefix : str, optional
        Path prefix used while looking for files. 
        Will default to the current directory

    Returns
    -------
    Tuple[Dict, Dict]
        A tuple containing both a dictionary of metadata and the actual data
    """

    #e.g. 1-1-ReLA_P1380_Point_Export.xml
    #print(f"Reading point {point_id}")
    xml_fname = f"{map_name:s}_P{point_id:d}_Point_Export.xml"
    if path_prefix is not None:
        xml_fname = os.path.join(path_prefix, xml_fname)

    point_xml = ET.parse(xml_fname)
    xml_root = point_xml.getroot()
    
    metadata = {}
    data = {}
    for elem in xml_root:
        if elem.tag == "Positions":
            data["connector_data"] = read_connectors(elem, path_prefix)
        elif elem.tag == "ECG":
            #ecg_metadata = 
            ecg_fname = os.path.join(path_prefix, elem.attrib["FileName"])
            with open(ecg_fname, "r") as ecg_f:
                ecg_metadata = [ecg_f.readline().strip() for i in range(3)]
                ecg_header = ecg_f.readline()
                ecg_header = [elem for elem in re.split(multi_whitespace_re, ecg_header) if len(elem) > 0] #Two or more whitespaces as delimiters
                #ecg_f.seek(0)
                ecg_data = pd.read_csv(ecg_f, #skiprows=4, #Not necessary if we don't seek to the beginning
                                        header=None, sep="\s+", names=ecg_header, dtype=np.int16)
            data["ecg"] = (ecg_metadata, ecg_data) 
        elif elem.tag == "ContactForce":
            data["contact_force_data"] = read_contact_force(os.path.join(path_prefix, elem.attrib["FileName"]))
        else:
            metadata[elem.tag] = xml_elem_to_dict(elem)

    return metadata, data

def convert_df_dtypes(df : pd.DataFrame, inplace=True) -> pd.DataFrame:
    if not inplace:
        df = df.copy()

    #Convert to numerical values wherever possible
    for k in df:
        df[k] = pd.to_numeric(df[k], errors="ignore")

    return df

def xml_elem_to_dict(xml_elem : Element) -> dict:
    return xml_elem.attrib


def xml_to_dataframe(xml_elem : Element, attribs=None) -> pd.DataFrame:
    dataframe_dict = defaultdict(lambda: [])

    for single_elem in xml_elem:
        for k, v in single_elem.items(): #XML-Attributes
            dataframe_dict[k].append(v)

    df = pd.DataFrame.from_dict(dataframe_dict)
    return convert_df_dtypes(df)

_camel_pattern = re.compile(r"(?<!^)(?=[A-Z])")

#https://stackoverflow.com/questions/1175208/elegant-python-function-to-convert-camelcase-to-snake-case
def camel_to_snake_case(name : str) -> str:
    return _camel_pattern.sub('_', name).lower()

#https://stackoverflow.com/questions/1175208/elegant-python-function-to-convert-camelcase-to-snake-case
def snake_to_camel_case(name : str, capitalize=False) -> str:
    ret = ''.join(word.title() for word in name.split('_'))
    if not capitalize:
        ret = ret[0].lower() + ret[1:]
    
    return ret

def convert_fname_to_handle(file : Union[IO, PathLike], mode : str):
    is_fname = issubclass(type(file), str)
    if is_fname:
        #assert file.endswith("pkl.gz"), "Only allowed file type is currently pkl.gz"
        file = open(file, mode)

    return file, is_fname


def simplify_dataframe_dtypes(df : pd.DataFrame, dtype_dict : dict, inplace=True, double_to_float = False) -> pd.DataFrame:
    if not inplace:
        df = df.copy()

    for k in df:
        if k in dtype_dict:
            #TODO: Check for min/max values
            df[k] = df[k].astype(dtype_dict[k])

        elif double_to_float and df[k].dtype == np.float64: #np.issubdtype(df[k].dtype, np.floating)
            df[k] = df[k].astype(np.float32)

    return df

def interp1d_dtype(x : np.ndarray, y : np.ndarray, *args, **kwargs):

    #For complex objects (e.g. strings), just take the closest object
    if y.dtype == np.object0:
        kdtree = cKDTree(x[:, np.newaxis])
        interp_f = lambda x_query: y[kdtree.query(x_query[:, np.newaxis])[1]]
    else:
        interp_f = interp1d(x, y, *args, **kwargs)

    if np.issubdtype(y.dtype, np.integer): #Integer values will be rounded back
        _interp_f = interp_f
        interp_f = lambda x_query: np.round(_interp_f(x_query)).astype(y.dtype)

    return interp_f 

def interpolate_time_data(dfs : Iterable[pd.DataFrame], time_k, time_steps, **interp_kwargs) -> pd.DataFrame:
    interp_fs = []
    for df in dfs:
        interp_fs.append({})
        for col_i, col_name in enumerate(df):
            #series = df.iloc[:, col_i]

            interp_fs[-1][col_name] = interp1d_dtype(df[time_k].to_numpy(), df.iloc[:, col_i].to_numpy(), **interp_kwargs)
            #if series.dtype == np.object0:
            #    kdtree = cKDTree(df[time_k].to_numpy()[:, np.newaxis])
            #    interp_fs[-1][col_name] = lambda x: df.iloc[kdtree.query(x[:, np.newaxis])[1], col_i]
            #else:
            #    interp_fs[-1][col_name] = interp1d(df[time_k], df.iloc[:, col_i], **interp_kwargs)

    #Build the unique columns
    all_columns = np.concatenate([df.columns for df in dfs])
    #Set the time as the first key
    unique_columns = np.concatenate([[time_k], np.setdiff1d(np.unique(all_columns), [time_k])])
    new_df_dict = {time_k: time_steps}
    for col_i, col_name in enumerate(unique_columns[1:]): #First column is the timing key
        for df, df_interp in zip(dfs, interp_fs):
            if col_name in df_interp:
                interpolated_val = df_interp[col_name](time_steps)
                if col_name in new_df_dict: #Already present -> Multiple dataframes contain the data
                    assert np.allclose(new_df_dict[col_name], interpolated_val, rtol=1e-1), f"Dataframe values of column {col_name} are not matching"
                else:
                    new_df_dict[col_name] = interpolated_val

    merged_data = pd.DataFrame(new_df_dict)
    return merged_data



def unify_time_data(dfs : Iterable[pd.DataFrame], time_k, time_interval, domain="intersection", **interp_kwargs) -> pd.DataFrame:
    assert domain in ["intersection"], "Selected domain not available or not yet implemented"
    assert all([time_k in df for df in dfs]), f"Selected time key {time_k} not present in all dataframes."

    if domain == "intersection":
        time_extent = (max([df[time_k].min() for df in dfs]), min([df[time_k].max() for df in dfs]))

    timespan = time_extent[1] - time_extent[0]
    nr_samples = int(np.ceil(timespan / time_interval))
    time_samples = np.arange(time_extent[0], time_extent[1], time_interval)
    if time_samples.size != nr_samples + 1:
        time_samples = np.concatenate([time_samples, [time_extent[1]]])
    assert time_samples.size == nr_samples + 1

    return interpolate_time_data(dfs, time_k, time_samples, **interp_kwargs)

def xyz_to_pos_vec(data : pd.DataFrame, pos_label : str = "pos") -> pd.DataFrame:
    xyz_strings = ["X", "Y", "Z"]
    assert all([n in data for n in xyz_strings]), f"Can not convert dataframe position from XYZ to a vector, since not all columns were found. Available columns {data.columns}"

    pos_vec = np.stack([data[n] for n in xyz_strings], axis=-1).tolist()
    data = data.drop(labels=xyz_strings[1:], axis=1)
    data["X"] = pos_vec
    return data.rename(columns={"X": pos_label})
