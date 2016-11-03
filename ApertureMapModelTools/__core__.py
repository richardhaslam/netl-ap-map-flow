"""
This stores the basic class and function dependencies of the
ApertureMapModelTools module.
#
Written By: Matthew Stadelman
Date Written: 2016/02/26
Last Modifed: 2016/08/10
#
"""
#
########################################################################
#
import logging
import os
import re
import subprocess
import scipy as sp
from scipy import sparse as sprs
#
########################################################################
#  Basic classes
########################################################################


class DataField(object):
    r"""
    Base class to store raw data from a 2-D field data file and
    the output data generated by the different processing routines
    """
    VTK_HEADER = r"""# vtk DataFile Version 3.0
vtk output
ASCII
DATASET STRUCTURED_GRID
DIMENSIONS {nx:d} 2 {nz:d}
POINTS {npts:d} float
"""

    def __init__(self, infile, **kwargs):
        super().__init__()
        self.infile = infile
        self.outfile = ''
        self.nx = 0
        self.nz = 0
        self._raw_data = None
        self.data_map = None
        self.data_vector = None
        self.point_data = None
        self._cell_interfaces = None
        self.output_data = dict()
        self.field_name = kwargs.get('field_name', 'data')
        #
        if infile is not None:
            self.parse_data_file(**kwargs)

    def clone(self):
        r"""
        Creates a fully qualified DataField object from the existing one.
        """
        # instantiating class and adding attributes
        clone = DataField(None)
        #
        self.copy_data(clone)
        clone._raw_data = sp.copy(self._raw_data)
        clone._cell_interfaces = sp.copy(self._cell_interfaces)
        #
        return clone

    def copy_data(self, obj):
        r"""
        Copies data properites of the field onto another object created
        """
        obj.nx = self.nx
        obj.nz = self.nz
        obj.data_map = sp.copy(self.data_map)
        obj.data_vector = sp.copy(self.data_vector)
        obj.point_data = sp.copy(self.point_data)

    def parse_data_file(self, delim='auto', **kwargs):
        r"""
        Reads the field's infile data and then populates the data_map array
        and sets the fields nx and nz properties.
        """
        #
        if delim == 'auto':
            with open(self.infile, 'r') as file:
                line = file.readline()
                #
                pat = r'[-0-9.+eE]+([^-0-9.+eE]+)[-0-9.+eE]+'
                match = re.search(pat, line)
                delim = match.group(1).strip()
                delim = None if not delim else delim
        #
        self.data_map = sp.loadtxt(self.infile, delimiter=delim)
        self._raw_data = sp.copy(self.data_map)
        self.data_vector = sp.ravel(self.data_map)
        self.nz, self.nx = self.data_map.shape
        #
        # defining cell interfaces used in adjacency matrix
        self._define_cell_interfaces()

    def _define_cell_interfaces(self):
        r"""
        Populates the cell_interfaces array
        """
        # covering right column
        self._cell_interfaces = []
        for iz in range(self.nx-1, (self.nz-1)*self.nx, self.nx):
            self._cell_interfaces.append([iz, iz+self.nx])
        # covering interior cells
        for iz in range(0, self.nz-1):
            for ix in range(0, self.nx-1):
                ib = iz*self.nx + ix
                self._cell_interfaces.append([ib, ib+1])
                self._cell_interfaces.append([ib, ib+self.nx])
        # covering top row
        for ix in range((self.nz-1)*self.nx, self.nz*self.nx-1):
            self._cell_interfaces.append([ix, ix+1])
        #
        self._cell_interfaces = sp.array(self._cell_interfaces,
                                         ndmin=2,
                                         dtype=int)

    def create_adjacency_matrix(self, data=None):
        r"""
        Returns a weighted adjacency matrix, in CSR format based on the
        product of weight values sharing an interface.
        """
        #
        if data is None:
            data = self.data_vector
        #
        weights = data[self._cell_interfaces[:, 0]]
        weights = 2*weights * data[self._cell_interfaces[:, 1]]
        #
        # clearing any zero-weighted connections
        indices = weights > 0
        interfaces = self._cell_interfaces[indices]
        weights = weights[indices]
        #
        # getting cell connectivity info
        row = interfaces[:, 0]
        col = interfaces[:, 1]
        #
        # append row & col to each other, and weights to itself
        row = sp.append(row, interfaces[:, 1])
        col = sp.append(col, interfaces[:, 0])
        weights = sp.append(weights, weights)
        #
        # Generate sparse adjacency matrix in 'coo' format and convert to csr
        num_blks = self.nx*self.nz
        matrix = sprs.coo_matrix((weights, (row, col)), (num_blks, num_blks))
        #
        return matrix.tocsr()

    def create_point_data(self):
        r"""
        The data_map attribute stores the cell data read in from file.
        """
        #
        self.point_data = DataField._cell_to_point_data(self.data_map,
                                                        self.nx,
                                                        self.nz)

    @staticmethod
    def _cell_to_point_data(data_map, nx, nz):
        r"""
        This function takes a cell data map and calculates average values
        at the corners to make a point data map. The Created array is 3-D with
        the final index corresponding to corners.
        Index Locations: 0 = BLC, 1 = BRC, 2 = TRC, 3 = TLC
        """
        #
        point_data = sp.zeros((nz+1, nx+1, 4))
        #
        # setting corners of map first
        point_data[0, 0, 0] = data_map[0, 0]
        point_data[0, -1, 1] = data_map[0, -1]
        point_data[-1, -1, 2] = data_map[-1, -1]
        point_data[-1, 0, 3] = data_map[-1, 0]
        #
        # calculating point values for the map interior
        for iz in range(nz):
            for ix in range(nx):
                val = sp.average(data_map[iz:iz+2, ix:ix+2])
                point_data[iz, ix, 2] = val
                point_data[iz+1, ix+1, 0] = val
                point_data[iz+1, ix, 1] = val
                point_data[iz, ix+1, 3] = val
        #
        # handling left and right edges
        for iz in range(nz):
            val = sp.average(data_map[iz:iz+2, 0])
            point_data[iz, 0, 3] = val
            point_data[iz+1, 0, 0] = val
            #
            val = sp.average(data_map[iz:iz+2, -1])
            point_data[iz, -1, 2] = val
            point_data[iz+1, -1, 1] = val
        #
        # handling top and bottom edges
        for ix in range(nx):
            val = sp.average(data_map[0, ix:ix+2])
            point_data[0, ix, 1] = val
            point_data[0, ix+1, 0] = val
            #
            val = sp.average(data_map[-1, ix:ix+2])
            point_data[-1, ix, 2] = val
            point_data[-1, ix+1, 3] = val
        #
        return point_data[0:nz, 0:nx, :]

    def threshold_data(self, min_value=None, max_value=None, repl=sp.nan):
        r"""
        Thresholds the data map based on the supplied minimum and
        maximum values. Values outside of the range are replaced by
        the repl argument which defaults to sp.nan.
        """
        #
        if min_value is not None:
            self.data_map[self.data_map <= min_value] = repl
        if max_value is not None:
            self.data_map[self.data_map >= max_value] = repl
        #
        # updating linked attributes
        self.data_vector = sp.ravel(self.data_map)

    def export_vtk(self,
                   filename=None,
                   y_values=None,
                   y_offsets=None,
                   voxel_size=1.0,
                   avg_fact=1.0,
                   cell_data=None,
                   overwrite=False):
        r"""
        Exports an ASCII legacy format VTK file to be read by ParaView.
        The X and Z coordinates are inferred from the data map dimensions.
        Values for the y coordinate if not supplied default to DataField's
        own data map. All ndarray inputs need to have the appropriate size
        and shape to match the DataField data. All coordinates are multiplied
        by the voxel_size.

        Arguments
        ---------
        filename : string, name of the vtk file to output (optional)
        y_values : 2-D ndarray, data map to use as the y-coordinate (optional)
        y_offsets : 2-D ndarray, data map to shift y-values by (optional)
        voxel_size : float, voxel size of a cell in desired units (optional)
        avg_fact : float, X and Z axis scaling factor
        cell_data : list, a list of tuples to add as cell data to the VTK
            file of the form [('name', 1-D ndarray), ...].
        overwrite : bool, allows the method to replace an existing file.
        """
        #
        # processing arguments
        if filename is None:
            filename = os.path.splitext(self.infile)[0] + '.vtk'
        #
        y_values = self.data_map if y_values is None else y_values
        cell_data = [] if cell_data is None else cell_data
        #
        if y_offsets is None:
            y_offsets = y_values/-2.0
        #
        # checking if file exists
        if not overwrite and os.path.exists(filename):
            msg = 'There is already a file at {},'
            msg += ' specify "overwrite=True" to replace it.'
            raise FileExistsError(msg.format(filename))
        #
        # initializing contents
        npts = (self.nx + 1) * (self.nz + 1) * 2
        content = self.VTK_HEADER.format(nx=self.nx+1, nz=self.nz+1, npts=npts)
        #
        # setting up y coordinate map
        y_coords = self._cell_to_point_data(y_values, self.nx, self.nz)
        y_coords = y_coords * voxel_size
        y_offsets = self._cell_to_point_data(y_offsets, self.nx, self.nz)
        y_offsets = y_offsets * voxel_size
        #
        # writing points to VTK file
        fmt = '{:14.6E} {:14.6E} {:14.6E}\n'
        for iz in range(self.nz):
            # lower face
            z = iz * voxel_size * avg_fact
            content += fmt.format(0.0, y_offsets[iz, 0, 0], z)
            for ix in range(self.nx):
                x = ix * voxel_size * avg_fact
                content += fmt.format(x, y_offsets[iz, ix, 1], z)
            # upper face
            y = y_offsets[iz, 0, 0] + y_coords[iz, 0, 0]
            content += fmt.format(0.0, y, z)
            for ix in range(self.nx):
                x = ix * voxel_size * avg_fact
                y = y_offsets[iz, ix, 1] + y_coords[iz, ix, 1]
                content += fmt.format(x, y, z)
        # final top lower edge of map
        z = self.nz * voxel_size * avg_fact
        content += fmt.format(0.0, y_offsets[-1, 0, 3], z)
        for ix in range(self.nx):
            x = ix * voxel_size * avg_fact
            content += fmt.format(x, y_offsets[-1, ix, 2], z)
        # upper edge
        y = y_offsets[-1, 0, 3] + y_coords[-1, 0, 3]
        content += fmt.format(0.0, y, z)
        for ix in range(self.nx):
            x = ix * voxel_size * avg_fact
            y = y_offsets[-1, ix, 2] + y_coords[-1, ix, 2]
            content += fmt.format(x, y, z)
        #
        # writing cell data to file
        content += '\nCELL_DATA {:d}\n'.format(self.nx * self.nz)
        cell_data.insert(0, (self.field_name, self.data_vector))
        #
        for (name, data) in cell_data:
            content = self._output_vtk_data_vector(content, name, data)
        #
        # writing VTK file to disk
        with open(filename, 'w')as file:
            file.write(content)

    def _output_vtk_data_vector(self, content, data_name, data_vector):
        r"""
        appends a data vector to the VTK file
        """
        content += '\n'
        content += 'SCALARS {} float\n'.format(data_name)
        content += 'LOOKUP_TABLE default\n'
        for value in data_vector:
            content += '{:14.6e}\n'.format(value)
        #
        return content


class StatFile(dict):
    r"""
    Parses and stores information from a simulation statisitics file. This
    class helps facilitate data mining of simulation results.
    """

    def __init__(self, infile):
        super().__init__()
        self.infile = infile
        self.map_file = ''
        self.pvt_file = ''
        self.parse_stat_file()

    def parse_stat_file(self, stat_file=None):
        r"""
        Parses either the supplied infile or the class's infile and
        uses the data to populate the data_dict.
        """
        self.infile = (stat_file if stat_file else self.infile)
        #
        with open(self.infile, 'r') as stat_file:
            content = stat_file.read()
            content_arr = content.split('\n')
            content_arr = [re.sub(r', *$', '', l).strip() for l in content_arr]
            content_arr = [re.sub(r'^#.*', '', l) for l in content_arr]
            content_arr = [l for l in content_arr if l]
        #
        # pulling out aperture map and pvt file key-value pairs
        map_line = content_arr.pop(0).split(',')
        pvt_line = content_arr.pop(0).split(',')
        self.map_file = map_line[1].strip()
        self.pvt_file = pvt_line[1].strip()
        self[map_line[0].replace(':', '').strip()] = self.map_file
        self[pvt_line[0].replace(':', '').strip()] = self.pvt_file
        #
        # stepping through pairs of lines to get key -> values
        for i in range(0, len(content_arr), 2):
            key_list = re.split(r',', content_arr[i])
            key_list = [k.strip() for k in key_list]
            val_list = re.split(r',', content_arr[i + 1])
            val_list = [float(v) for v in val_list]
            #
            for key, val in zip(key_list, val_list):
                m = re.search(r'\[(.*?)\]$', key)
                unit = (m.group(1) if m else '-')
                key = re.sub(r'\[.*?\]$', '', key).strip()
                self[key] = [val, unit]
        #
        # modifiying NX and NZ keys to just be an integer instead of list
        self['NX'] = self['NX'][0]
        self['NZ'] = self['NZ'][0]
#
########################################################################
#  Basic functions
########################################################################


def _get_logger(module_name):
    r"""
    Fetches a module level logger, setting AMT as the parent logger
    """
    #
    name = module_name.replace('ApertureMapModelTools', 'AMT')
    name = name.replace('_', '')
    #
    return logging.getLogger(name)


def set_main_logger_level(level_name):
    r"""
    Sets the logging level of the top level module logger by providing one
    of the predefined logger levels DEBUG, INFO, WARNING, ERROR, CRITICAL.
    If a number is passed in it is used directly
    """
    #
    main_logger = _get_logger(__name__.split('.')[0])
    try:
        level_name = level_name.upper()
        main_logger.setLevel(logging.getLevelName(level_name))
    except AttributeError:
        main_logger.setLevel(level_name)


def files_from_directory(directory='.', pattern='.', deep=True):
    r"""
    Allows the user to get a list of files in the supplied directory
    matching a regex pattern. If deep is set to True then any
    sub-directories found will also be searched. A pre-compiled pattern
    can be supplied instead of a string.
    """
    #
    # setting up pattern
    try:
        if pattern[0] == '*':
            pattern = re.sub(r'\.', r'\\.', pattern)
            pattern = '.'+pattern+'$'
            msg = 'Modifying glob pattern to proper regular expression: {}'
            logger.warn(msg.format(pattern))
        pattern = re.compile(pattern, flags=re.I)
    except (ValueError, TypeError):
        logger.info('Using user compiled pattern: {}'.format(pattern))
    #
    # initializing
    dirs = [directory]
    files = []
    while dirs:
        #
        directory = dirs.pop(0)
        cmd_arr = ['ls', directory]
        ls = subprocess.Popen(cmd_arr,
                              stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE,
                              universal_newlines=True)
        std_out, std_err = ls.communicate()
        content_arr = std_out.split('\n')
        content_arr = [c.strip() for c in content_arr if c.strip()]
        #
        for path in content_arr:
            pth = os.path.join(directory, path)
            pth = os.path.realpath(pth)
            if os.path.isdir(pth) and deep:
                dirs.append(str(pth))
            elif os.path.isfile(pth) and pattern.search(pth):
                files.append(pth)
    #
    return files


def load_infile_list(infile_list, delim='auto'):
    r"""
    Function to generate a list of DataField objects from a list of input files
    """
    field_list = []
    #
    # loading and parsing each input file
    for infile in infile_list:
        #
        # constructing object
        field = DataField(infile, delim=delim)
        logger.info('Finished reading file: '+field.infile)
        #
        field_list.append(field)
    #
    return field_list


def calc_percentile(perc, data, sort=True):
    r"""
    Calculates the desired percentile of a dataset.
    """
    tot_vals = float(len(data))
    num_vals = 0.0
    sorted_data = list(data)
    if sort:
        sorted_data.sort()
    #
    # stepping through list
    index = 0
    for i in range(len(sorted_data)):
        index = i
        if (num_vals/tot_vals*100.0) >= perc:
            break
        else:
            num_vals += 1
    #
    #
    return sorted_data[index]


def calc_percentile_num(num, data, last=False, sort=True):
    r"""
    Calculates the percentile of a provided number in the dataset.
    If last is set to true then the last occurance of the number
    is taken instead of the first.
    """
    tot_vals = float(len(data))
    num_vals = 0.0
    sorted_data = list(data)
    if sort:
        sorted_data.sort()
    #
    # stepping through list
    for i in range(len(sorted_data)):
        if last is True and data[i] > num:
            break
        elif last is False and data[i] >= num:
            break
        else:
            num_vals += 1
    #
    perc = num_vals/tot_vals
    #
    return perc


def get_data_vect(data_map, direction, start_id=1):
    r"""
    Returns either of a row or column of the data map as a single vector
    """
    #
    nz, nx = data_map.shape
    if direction.lower() == 'x':
        # getting row index
        if start_id >= nz:
            start_id = nz
        elif start_id <= 0:
            start_id = 1
        return data_map[start_id-1, :]

    elif direction.lower() == 'z':
        if start_id >= nx:
            start_id = nx
        elif start_id <= 0:
            start_id = 1
        #
        return data_map[:, start_id-1]
    else:
        msg = 'Error - invalid direction supplied, can only be x or z'
        raise ValueError(msg)

#
# setting up core logger
logger = _get_logger(__name__)
