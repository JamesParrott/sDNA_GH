import os
import sys
import subprocess
import pathlib

# https://discuss.python.org/t/custom-build-steps-moving-bokeh-off-setup-py/16128/3
from hatchling.builders.hooks.plugin.interface import BuildHookInterface

REPO_DIR = pathlib.Path(__file__).parent

BUILDER_GH = REPO_DIR / 'dev' / 'sDNA_build_components.gh'

if not BUILDER_GH.is_file():
    raise FilePathError(f'Builder file not found at: {BUILDER_GH=}')

class CustomHook(BuildHookInterface):
    def initialize(self, version, build_data):
        env = os.environ.copy()
        env['SDNA_GH_BUILD_DEPS'] = sys.path[-1]
        if self.target_name in ('wheel', 'bdist'):
            subprocess.run(
                rf'"C:\Program Files\Rhino 8\System\Rhino.exe" /nosplash /runscript="-_grasshopper _editor _load _document _open {BUILDER_GH} _enter _exit _enterend'
               ,shell=True
               ,env = env
               )
    
    def finalize(self, version, build_data, artifact_path):
        src_components_dir = (REPO_DIR / 'src' 
                                       / 'sDNA_GH' 
                                       / 'components'
                                       / 'automatically_built'
                             )
        for path in src_components_dir.glob('*.ghuser'):
            path.unlink()
        