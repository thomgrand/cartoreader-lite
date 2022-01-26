"""This file provides routines to read .mesh files from CARTO3
"""

from io import StringIO
import os
from typing import Iterable, List, Tuple, Union
import pandas as pd
from pandas.errors import EmptyDataError
import numpy as np
import re
import pyvista as pv
import vtk
import logging as log

section_re_expr_str = "\[(\S+)\]"
section_re_expr = re.compile(section_re_expr_str)

attribute_re_expr_str = "(\S+)\s+=\s*(.*)"
attribute_re_expr = re.compile(attribute_re_expr_str)

blank_line_expr = re.compile("\s+")

def read_section(lines : Iterable[str]) -> pd.DataFrame:
    """Reads a single section of the .mesh files

    Parameters
    ----------
    lines : Iterable[str]
        The lines of the section

    Returns
    -------
    pd.DataFrame
        The section data in a dataframe
    """
    vertices_str = "\n".join(lines)
    verts_io = StringIO(vertices_str)
    df = pd.read_csv(verts_io, comment=";", header=None, sep="\s+")
    valid_line_i = [i for i, l in enumerate(lines) if not l.strip().startswith(";")][0] #Find first non-comment line
    assert valid_line_i > 0, "No header row found"
    names = [name for name in re.split("\s+", lines[valid_line_i-1]) if name not in ["", ";"]]
    return df, names

def read_vertices(data : pd.DataFrame):
    points = np.stack([data[n] for n in ["X", "Y", "Z"]], axis=-1)
    normals = np.stack([data[f"Normal{n:s}"] for n in ["X", "Y", "Z"]], axis=-1)
    group_id = np.array(data["GroupID"])

    return points, normals, group_id

def read_tris(data : pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Converts the dataframe of the TrianglesSection into multiple numpy array

    Parameters
    ----------
    data : pd.DataFrame
        The data containing the TrianglesSection

    Returns
    -------
    Tuple[np.ndarray, np.ndarray, np.ndarray]
        Returns the triplet (faces [Mx3], normals [Mx3], group-ID [M])
    """
    tris = np.stack([data[f"Vertex{i:d}"] for i in range(3)], axis=-1)
    normals = np.stack([data[f"Normal{n:s}"] for n in ["X", "Y", "Z"]], axis=-1)
    group_id = np.array(data["GroupID"])

    return tris, normals, group_id


def read_mesh_file(fname : str) -> Tuple[Union[pv.UnstructuredGrid, pv.PolyData], dict]:
    """Reads a single mesh file in CARTO3 mesh format and returns it as a pyvista object

    Parameters
    ----------
    fname : str
        Filename of the mesh file

    Returns
    -------
    Tuple[Union[pv.UnstructuredGrid, pv.PolyData], dict]
        Returns the constructred mesh from the data, along with the header data as a dictionary
    """
    with open(fname, "r", errors="replace") as f:
        lines = f.readlines()

    section_inds = [(i, section_re_expr.match(lines[i])) for i in np.arange(len(lines)) if section_re_expr.match(lines[i]) is not None]

    assert len(section_inds) > 1, "Not enough section headers found in the file"
    assert section_inds[0][1].group(1) == "GeneralAttributes", "Expected attributes first"

    section_inds.append((len(lines), None)) #To ease iteration

    header = {}
    for line in lines[section_inds[0][0]+1:section_inds[1][0]]:
        if not line.startswith(";") and blank_line_expr.match(line) is None:
            match = attribute_re_expr.match(line)
            assert match is not None, f"Could not parse header line '{line:s}'"
            header[match.group(1)] = match.group(2)
    
    points = vert_normals = vert_groups = None
    tris = tri_normals = tri_groups = None
    for i in range(1, len(section_inds) - 1):
        sec = section_inds[i]
        next_sec = section_inds[i+1]
        section_name = sec[1].group(1)

        section_lines = lines[sec[0]:next_sec[0]]

        try:
            df, header_names = read_section(section_lines[1:])
            assert np.all(df[0] == np.arange(len(df))), f"Non continuous index sequence in section {section_name:s}"
            assert np.all(df[1] == "="), f"Equality sign expected in section {section_name:s}"

            df = df[range(2, len(df.columns))] #Actual dataframe
            if len(df.columns) > len(header_names):
                log.warn(f"Error while reading mesh {fname}, section {section_name}: Mismatch between number of given column headers and data columns." 
                                f"Expected {len(df.columns)}, but got {len(header_names)}. Later headers will be 'N/A'")
                header_names += ["N/A"] * (len(df.columns) - len(header_names))
            if section_name != "VerticesAttributesSection":
                df.columns = header_names

            if section_name == "VerticesSection":
                points, vert_normals, vert_groups = read_vertices(df)
            elif section_name == "TrianglesSection":
                tris, tri_normals, tri_groups = read_tris(df)
            elif section_name == "VerticesAttributesSection":
                log.info("Skipping VerticesAttributesSection (not yet implemented)")
        except EmptyDataError as err:
            print(f"Skipping section {section_name}. Section is empty.")
            print("Original error: ", err)

    
    assert points is not None, "No vertices found in the file"

    if tris is None:
        mesh = pv.PolyData(points)

    else:
        mesh = pv.UnstructuredGrid({vtk.VTK_TRIANGLE: tris}, points)
        mesh.cell_data["normals"] = tri_normals
        mesh.cell_data["group_id"] = tri_groups

    mesh.point_data["normals"] = vert_normals
    mesh.point_data["group_id"] = vert_groups

    return mesh, header
