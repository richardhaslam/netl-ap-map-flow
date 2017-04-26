"""
Automatically imports several modules.
#
Written By: Matthew Stadelman
Date Written: 2016/02/26
Last Modifed: 2017/04/15
#
"""
#
import logging.config as _logging_config
import os as _os
import sys as _sys
import PIL as _pil
from .ap_map_flow import DataField, FractureImageStack
from .ap_map_flow import _get_logger, set_main_logger_level
from .ap_map_flow import files_from_directory, load_infile_list
from .ap_map_flow import calc_percentile, calc_percentile_num, get_data_vect
from . import data_processing
from . import run_model
from . import openfoam


__version__ = '0.1.0'
DEFAULT_MODEL_PATH = _os.path.realpath(_os.path.split(__file__)[0])
DEFAULT_MODEL_NAME = 'apm-lcl-model.exe'


# reading logging config
_config_file = _os.path.join(_os.path.dirname(__file__), 'logging.conf')
_logging_config.fileConfig(_config_file)
