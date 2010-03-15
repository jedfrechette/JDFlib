#!BPY
"""
Name: 'JRC Reconstructor Camera (.cal)'
Blender: 249
Group: 'Import'
Tooltip: 'Import a camera defined in a JRC Reconstructor .cal file'
"""

from lxml import etree
from numpy import asmatrix, fromstring, identity

import Blender
from Blender import Camera, Mathutils, Object, Window, Scene

def load_camera(infile='/tmp/IMG_3843-ice2_task121_section1_1_sub1.cal'):
    """Load camera parameters from a JRC Reconstructor calibration file."""
    try:
        cam_etree = etree.parse(infile)
    except:
        raise IOError('Invalid input file')


    if cam_etree.docinfo.doctype == '<!DOCTYPE CameraCalibration>':
        return cam_etree
    else:
        raise IOError('Invalid input file')

def create_camera(cam_etree):
    """Create a camera and set its internal parameters based on a CameraCalibration XML etree.

    The camera is created at the origin pointing towards -z with the top of the
    frame towards +y.
    """

    camera = Camera.New('persp')
    camera.name = cam_etree.getroot().get('Image')
    camera.angle = float(cam_etree.getroot().get('FOVX'))
       
    return camera

def pose_camera(cam, cam_etree):
    """Pose camera based on external parameters in a CameraCalibration XML etree.
    
    The following transforms are performed:
    
    1. Perform a 180 degree rotation of the camera about the y axis.

    2. Apply the inverse of the transform defined by Model2CameraMatrix to the
    camera. Use the inverse because we are moving the camera not the model.

    3. Apply the transform defined by /Model/Pose."""
    #TODO: All of the matrix operations could be switched to Matutils to remove
    #      numpy dependency.

    y_rot = asmatrix(identity(4))
    y_rot[0, 0] = -1
    y_rot[2, 2] = -1
    
    m2c = cam_etree.find('Model2CameraMatrix').find('Matrix4x4').get('RowOrder')
    m2c = asmatrix(fromstring(m2c, sep=' ').reshape(4, 4))

    m = cam_etree.find('Model').find('Pose').find('Matrix4x4').get('RowOrder')
    m = asmatrix(fromstring(m, sep=' ').reshape(4, 4))
    
    # We have been working with row-order matrices so they need to be
    # transposed before composition.
    pose = y_rot.T * m2c.T.I * m.T
    pose = pose.tolist()
    pose = Mathutils.Matrix(*pose)
    
    cam.setMatrix(pose)
    
def main(param_file):
    Window.WaitCursor(1)
    
    camera_parameters = load_camera(param_file)

    emode = int(Window.EditMode())
    if emode: Window.EditMode(0)

    scene = Scene.GetCurrent()
    camera_data = create_camera(camera_parameters)
    scene.objects.new(camera_data)
    camera = Object.Get(camera_data.name)
    pose_camera(camera,  camera_parameters)
    scene.objects.camera = camera
    
    context = scene.getRenderingContext()
    context.imageSizeX(int(camera_parameters.getroot().get('Width')))
    context.imageSizeY(int(camera_parameters.getroot().get('Height')))

    scene.update()
    Window.RedrawAll()

    if emode: Window.EditMode(1)

    Window.WaitCursor(0)

Window.FileSelector(main, 'Load Calibration')
