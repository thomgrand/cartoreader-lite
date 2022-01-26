import pyvista as pv
import numpy as np
import vtk
import trimesh
from trimesh.proximity import ProximityQuery
from typing import Tuple, Union

def create_tri_mesh(mesh : pv.UnstructuredGrid) -> trimesh.Trimesh:
    """Creates a Trimesh from an unstructured grid

    Parameters
    ----------
    mesh : pv.UnstructuredGrid
        mesh to convert. Will be automatically triangulated

    Returns
    -------
    trimesh.Trimesh
        The converted trimesh
    """
    mesh = mesh.triangulate()
    assert vtk.VTK_TRIANGLE in mesh.cells_dict and len(mesh.cells_dict) == 1, "Triangulation of the mesh failed"

    verts = mesh.points
    faces = mesh.cells_dict[vtk.VTK_TRIANGLE]
    return trimesh.Trimesh(verts, faces)

def project_points(mesh : Union[trimesh.Trimesh, pv.UnstructuredGrid], points : np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Projects a set of points onto a triangulated surface mesh

    Parameters
    ----------
    mesh : Union[trimesh.Trimesh, pv.UnstructuredGrid]
        A mesh to project on. Will be converted to a trimesh, if it is not one already (see :func:`create_tri_mesh`)
    points : np.ndarray
        Points to project [Nx3]

    Returns
    -------
    Tuple[np.ndarray, np.ndarray, np.ndarray]
        The returned triplet will consist of:

            * The projected points [Nx3]
            * The projection distance [N]
            * The triangle index on which the projection ended up [N]
    """
    if type(mesh) == pv.UnstructuredGrid:
        mesh = create_tri_mesh(mesh)

    prox = ProximityQuery(mesh)
    points_proj, proj_dist, tri_i = prox.on_surface(points)
    return points_proj, proj_dist, tri_i
