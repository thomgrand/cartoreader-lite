import numpy as np
import pyvista as pv
import vtk
from cartoreader_lite.postprocessing.geometry import project_points, create_tri_mesh
import trimesh

class TestPostprocessing():

    def test_create_tri_mesh(self):
        mesh = pv.UnstructuredGrid({vtk.VTK_TRIANGLE: np.array([[0, 1, 2]])}, 
                                np.array([[0, 0, 0], [1.0, 0., 0.], [0, 1, 0]]))
        tri_mesh = create_tri_mesh(mesh)
        assert type(tri_mesh) == trimesh.Trimesh
        assert len(tri_mesh.vertices) == 3
        assert len(tri_mesh.faces) == 1

    def test_projection(self):
        mesh = pv.UnstructuredGrid({vtk.VTK_TRIANGLE: np.array([[0, 1, 2]])}, 
                                np.array([[0, 0, 0], [1.0, 0., 0.], [0, 1, 0]]))

        proj_pos, proj_dist, tri_i = project_points(mesh, np.array([[0.5, 0.5, 1]]))
        assert np.allclose(proj_pos, np.array([[0.5, 0.5, 0]]))
        assert np.isclose(proj_dist, 1)
        assert np.all(tri_i == 0)

        #Test with the already converted mesh
        proj_pos, proj_dist, tri_i = project_points(create_tri_mesh(mesh), np.array([[0.5, 0.5, 1]]))
        assert np.allclose(proj_pos, np.array([[0.5, 0.5, 0]]))
        assert np.isclose(proj_dist, 1)
        assert np.all(tri_i == 0)


