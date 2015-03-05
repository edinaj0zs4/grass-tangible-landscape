#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      akratoc
#
# Created:     30/10/2013
# Copyright:   (c) akratoc 2013
# Licence:     <your licence>
#-------------------------------------------------------------------------------
import os
import sys
import atexit
import numpy as np
from tempfile import mkstemp, gettempdir

from grass.script import core as gcore
from grass.script import raster as grast
from grass.exceptions import CalledModuleError

from scan_processing import  get_environment, remove_temp_regions, read_from_ascii, \
    adjust_boundaries, remove_fuzzy_edges, calibrate_points, remove_table, scale_z_exag, \
    interpolate_surface, bin_surface, trim_edges_nsew, remove_vector
import current_analyses



def import_scan(input_file, real_elev, output_elev, mm_resolution, calib_matrix, trim_nsew, table_mm, zexag, interpolate, info_text):
    output_tmp1 = "output_scan_tmp1"

    fd, temp_path = mkstemp()
    os.close(fd)
    os.remove(temp_path)
    try:
        read_from_ascii(input_file=input_file, output_file=temp_path)
    except:
        return

    fh = open(temp_path, 'r')
    array = np.array([map(float, line.split()) for line in fh.readlines()])
    fh.close()

    # calibrate points by given matrix
    array = calibrate_points(array, calib_matrix).T

    # remove underlying table
    try:
        array = remove_table(array, table_mm)
    except StandardError, e:
        print e
        return

    # remove fuzzy edges
    try:
        array = remove_fuzzy_edges(array, resolution=mm_resolution, tolerance=0.3)
    except StandardError, e:
        print e
        return

    # scale Z to original and apply exaggeration
    raster_info = grast.raster_info(real_elev)
    try:
        array, scale = scale_z_exag(array, raster_info, zexag, info_text)
    except StandardError, e:
        print e
        return
    # trim edges
    array = trim_edges_nsew(array, trim_nsew)

    # save resulting array
    np.savetxt(temp_path, array, delimiter=" ")

    # import
    if array.shape[0] < 2000:
        return

    # create surface
    tmp_regions = []
    env = get_environment(tmp_regions, n=np.max(array[:, 1]), s=np.min(array[:, 1]), 
                          e=np.max(array[:, 0]), w=np.min(array[:, 0]), res=mm_resolution)
    if interpolate:
        interpolate_surface(input_file=temp_path, output_raster=output_elev,
                            temporary_vector=output_tmp1, env=env)
    else:
        bin_surface(input_file=temp_path, output_raster=output_elev, temporary_raster=output_tmp1, env=env)
    try:
        os.remove(temp_path)
    except:  # WindowsError
        gcore.warning("Failed to remove temporary file {path}".format(path=temp_path))

    info = grast.raster_info(output_elev)
    if info['min'] is None or info['max'] is None or np.isnan(info['min']) or np.isnan(info['max']):
        return

    adjust_boundaries(real_elev=real_elev, scanned_elev=output_elev, env=env)
    env = get_environment(tmp_regions, rast=output_elev)
    gcore.run_command('r.colors', map=output_elev, color='elevation', env=env)

########### export point cloud for Rhino ##############
#    output_xyz = os.path.join(os.path.realpath(gettempdir()), 'point_cloud.xyz') 
#    gcore.run_command('r.out.xyz', input=output_elev, output=output_xyz, separator='space', overwrite=True, env=env)
########################################################

    # run analyses
    functions = [func for func in dir(current_analyses) if func.startswith('run_') and func != 'run_command']
    for func in functions:
        exec('del current_analyses.' + func)
    try:
        reload(current_analyses)
    except:
        pass
    functions = [func for func in dir(current_analyses) if func.startswith('run_') and func != 'run_command']
    for func in functions:
        try:
            exec('current_analyses.' + func + '(real_elev=real_elev, scanned_elev=output_elev, info_text=info_text, scale=scale, zexag=zexag, env=env)')
        except CalledModuleError, e:
            print e

    # cleanup
    if interpolate:
        remove_vector(output_tmp1)
    else:
        gcore.run_command('g.remove', flags='f', type='raster', name=output_tmp1, env=env)

    remove_temp_regions(tmp_regions)


def main():
    import subprocess
#    gcore.use_temp_region()
    mesh_path = os.path.join(os.path.realpath(gettempdir()), 'kinect_scan.txt')

    kinect_app = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'kinect', 'scan_once', 'KinectFusionBasics-D2D.exe')
    subprocess.call([kinect_app, mesh_path, '40', '0.4', '1.2', '512', '384']) # last 2 parameters must be 128/384/512 (larger for bigger models)
    calib_matrix = np.load(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'calib_matrix.npy'))
    import_scan(input_file=mesh_path,
                real_elev='elevation',
                output_elev='scan',
                mm_resolution=0.001,
                calib_matrix=calib_matrix,
                table_mm=5, zexag=3,
                interpolate=False,
                trim_nsew=[0, 0, 0, 0],
                info_text=[])

def cleanup():
    pass


if __name__ == '__main__':
    atexit.register(cleanup)
    sys.exit(main())
