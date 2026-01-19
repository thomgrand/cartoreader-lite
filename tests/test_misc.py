from importlib.metadata import version
import cartoreader_lite

def test_version_consistency():
    installed_version = version("cartoreader-lite")
    assert installed_version == cartoreader_lite.__version__
