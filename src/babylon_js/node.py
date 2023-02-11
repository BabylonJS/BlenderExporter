from .logging import *
from .f_curve_animatable import *

DEF_DISABLED = False

class Node(FCurveAnimatable):
    def __init__(self, node):
        Logger.log('processing begun of node:  ' + node.name)
        self.define_animations(node, True, True, True)  #Should animations be done when forcedParent
        self.name = node.name

        if node.parent and node.parent.type != 'ARMATURE':
            self.parentId = node.parent.name

        loc, rot, scale = node.matrix_local.decompose()

        self.position = loc
        if node.rotation_mode == 'QUATERNION':
            self.rotationQuaternion = rot
        else:
            self.rotation = scale_vector(rot.to_euler('YXZ'), -1)
        self.scaling = scale
        self.isVisible = False
        self.isEnabled = not DEF_DISABLED
        self.customProperties = node.items()

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    def to_json_file(self, file_handler):
        file_handler.write('{')
        write_string(file_handler, 'name', self.name, True)
        write_string(file_handler, 'id', self.name)
        if hasattr(self, 'parentId'): write_string(file_handler, 'parentId', self.parentId)

        write_vector(file_handler, 'position', self.position)
        if hasattr(self, "rotationQuaternion"):
            write_quaternion(file_handler, "rotationQuaternion", self.rotationQuaternion)
        else:
            write_vector(file_handler, 'rotation', self.rotation)
        write_vector(file_handler, 'scaling', self.scaling)
        write_bool(file_handler, 'isVisible', self.isVisible)
        write_bool(file_handler, 'isEnabled', self.isEnabled)

        if self.customProperties:
            self.writeCustomProperties(file_handler)

        super().to_json_file(file_handler) # Animations
        file_handler.write('}')

    def writeCustomProperties(self, file_handler):
        file_handler.write(',"metadata": {')
        noComma = True
        for k, v in self.customProperties:
            print('writing custom prop:', k, v)
            if type(v) == str: write_string(file_handler, k, v, noComma)
            elif type(v) == float: write_float(file_handler, k, v, noComma)
            elif type(v) == int: write_int(file_handler, k, v, noComma)
            noComma = False
        file_handler.write('}')
