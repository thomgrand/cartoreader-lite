import pyvista as pv
import numpy as np
from cartoreader_lite import CartoStudy

if __name__ == "__main__":
    study_dir = "openep-testingdata/Carto/Export_Study-1-11_25_2021-15-01-32"
    study_name = "Study 1 11_25_2021 15-01-32.xml"
    study = CartoStudy(study_dir, study_name, 
                    carto_map_kwargs={"discard_invalid_points": False} #The testing data only contains invalid points (LAT outside WOI)
                        )

    ablation_points = pv.PolyData(np.stack(study.ablation_data.session_avg_data["pos"].to_numpy()))
    ablation_points.point_data["RFIndex"] = study.ablation_data.session_avg_data["RFIndex"]
    plotter = pv.Plotter(off_screen=True)
    plotter.add_mesh(ablation_points, cmap="jet")
    plotter.add_mesh(study.maps[2].mesh)
    plotter.show(screenshot="docs/figures/openep-example.png")
    #plotter.show()
