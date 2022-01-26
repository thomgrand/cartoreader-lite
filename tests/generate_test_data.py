import os
import subprocess
import zipfile
import shutil

if __name__ == "__main__":
    subprocess.check_call(["git", "clone", "https://github.com/thomgrand/openep-testingdata"])

    #Unzip the large file
    visitag_dir = "openep-testingdata/Carto/Export_Study-1-11_25_2021-15-01-32/VisiTagExport/"
    with zipfile.ZipFile(os.path.join(visitag_dir, "AllPositionInGrids.zip"), "r") as zip_f:
        zip_f.extractall(visitag_dir)

    shutil.make_archive("openep-testingdata", "zip", "openep-testingdata")

    

