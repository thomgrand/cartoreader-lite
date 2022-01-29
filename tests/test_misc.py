import pkg_resources 
import cartoreader_lite
import re

def test_version_consistency():
    version = pkg_resources.require("cartoreader-lite")[0].version
    assert version == cartoreader_lite.__version__
