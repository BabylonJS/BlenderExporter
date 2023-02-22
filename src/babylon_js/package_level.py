from sys import modules
from math import floor
from mathutils import Euler, Matrix

import bpy
from bpy import app
from time import strftime
FLOAT_PRECISION_DEFAULT = 4
VERTEX_OUTPUT_PER_LINE = 50
STRIP_LEADING_ZEROS_DEFAULT = False # false for .babylon
#===============================================================================
#  module level formatting methods, called from multiple classes
#===============================================================================
def get_title():
    bl_info = get_bl_info()
    return bl_info['name'] + ' ver ' + format_exporter_version(bl_info)
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def format_exporter_version(bl_info = None):
    if bl_info is None:
        bl_info = get_bl_info()
    exporterVersion = bl_info['version']
    if exporterVersion[2] >= 0:
        return str(exporterVersion[0]) + '.' + str(exporterVersion[1]) +  '.' + str(exporterVersion[2])
    elif exporterVersion[2] == -1:
        return str(exporterVersion[0]) + '.' + str(exporterVersion[1]) +  '-alpha'
    else:
        return str(exporterVersion[0]) + '.' + str(exporterVersion[1]) +  '-beta ' + str(abs(exporterVersion[2]) - 1)
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def verify_min_blender_version():
    # required version string in addon changed format in 2.83
    reqd = get_bl_info()['blender']

    # reqd in form of '(2, 80, 0)' since 2.80
    return bpy.app.version >= reqd

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def getNameSpace(filepathMinusExtension):
    # assign nameSpace, based on OS
    if filepathMinusExtension.find('\\') != -1:
        return legal_js_identifier(filepathMinusExtension.rpartition('\\')[2])
    else:
        return legal_js_identifier(filepathMinusExtension.rpartition('/')[2])
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# a class for getting the module name, exporter version, & reqd blender version in get_bl_info()
class dummy: pass
def get_bl_info():
    # .__module__ is the 'name of package.module', so strip after dot
    packageName = dummy.__module__.partition('.')[0]
    return modules.get(packageName).bl_info
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def legal_js_identifier(input):
    out = ''
    prefix = ''
    for char in input:
        if len(out) == 0:
            if char in '0123456789':
                # cannot take the chance that leading numbers being chopped of cause name conflicts, e.g (01.R & 02.R)
                prefix += char
                continue
            elif char.upper() not in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
                continue

        legal = char if char.upper() in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_' else '_'
        out += legal

    if len(prefix) > 0:
        out += '_' + prefix
    return out
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def format_f(num, precision = FLOAT_PRECISION_DEFAULT, stripLeadingZero = STRIP_LEADING_ZEROS_DEFAULT):
    return format_float(num, '%.' + str(precision) + 'f', stripLeadingZero)
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def format_float(num, fmt, stripLeadingZero = STRIP_LEADING_ZEROS_DEFAULT):
    s = fmt % num  # rounds to N decimal places
    s = s.rstrip('0') # strip trailing zeroes
    s = s.rstrip('.') # strip trailing .
    s = '0' if s == '-0' else s # nuke -0

    if stripLeadingZero:
        asNum = float(s)
        if asNum != 0 and asNum > -1 and asNum < 1:
            if asNum < 0:
                s = '-' + s[2:]
            else:
                s = s[1:]

    return s
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def format_matrix4(matrix, precision = FLOAT_PRECISION_DEFAULT):
    tempMatrix = matrix.copy()
    tempMatrix.transpose()

    ret = ''
    first = True
    fmt = '%.' + str(precision) + 'f'
    for vect in tempMatrix:
        if (first != True):
            ret +=','
        first = False;

        ret += format_float(vect[0], fmt) + ',' + format_float(vect[1], fmt) + ',' + format_float(vect[2], fmt) + ',' + format_float(vect[3], fmt)

    return ret
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def format_array3(array, precision = FLOAT_PRECISION_DEFAULT):
    fmt = '%.' + str(precision) + 'f'
    return format_float(array[0], fmt) + ',' + format_float(array[1], fmt) + ',' + format_float(array[2], fmt)
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def format_array(array, precision, indent = '', beginIdx = 0, firstNotIncludedIdx = -1):
    ret = ''
    first = True
    nOnLine = 0

    fmt = '%.' + str(precision) + 'f'
    endIdx = len(array) if firstNotIncludedIdx == -1 else firstNotIncludedIdx
    for idx in range(beginIdx, endIdx):
        if (first != True):
            ret +=','
        first = False;

        ret += format_float(array[idx], fmt)
        nOnLine += 1

        if nOnLine >= VERTEX_OUTPUT_PER_LINE:
            ret += '\n' + indent
            nOnLine = 0

    return ret
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def format_indice_array(array, precision, indent = '', beginIdx = 0, firstNotIncludedIdx = -1):
    ret = ''
    first = True
    nOnLine = 0

    fmt = '%.' + str(precision) + 'f'
    endIdx = len(array) if firstNotIncludedIdx == -1 else firstNotIncludedIdx
    for idx in range(beginIdx, endIdx, 3):
        if (first != True):
            ret +=','
        first = False;

        if bpy.context.scene.world.preserveZUpRight == True :
            ret += format_float(array[idx + 2], fmt)
            ret +=','
            ret += format_float(array[idx + 1], fmt)
            ret +=','
            ret += format_float(array[idx    ], fmt)
        else :
            ret += format_float(array[idx    ], fmt)
            ret +=','
            ret += format_float(array[idx + 1], fmt)
            ret +=','
            ret += format_float(array[idx + 2], fmt)

        nOnLine += 3

        if nOnLine >= VERTEX_OUTPUT_PER_LINE:
            ret += '\n' + indent
            nOnLine = 0

    return ret
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def format_color(color, precision = FLOAT_PRECISION_DEFAULT):
    fmt = '%.' + str(precision) + 'f'
    # reference by [], since converted materials to 2.80 cannot be addressed by .r, .g, or .b
    return format_float(color[0], fmt) + ',' + format_float(color[1], fmt) + ',' + format_float(color[2], fmt)
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def format_vector(vector, precision = FLOAT_PRECISION_DEFAULT):
    fmt = '%.' + str(precision) + 'f'
    if bpy.context.scene.world.preserveZUpRight == True :
        return format_float(vector.x, fmt) + ',' + format_float(vector.y, fmt) + ',' + format_float(vector.z, fmt)
    else :
        return format_float(vector.x, fmt) + ',' + format_float(vector.z, fmt) + ',' + format_float(vector.y, fmt)
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def format_vector_array(vectorArray, precision = FLOAT_PRECISION_DEFAULT, indent = ''):
    ret = ''
    first = True
    nOnLine = 0
    for vector in vectorArray:
        if (first != True):
            ret +=','
        first = False;

        ret += format_vector(vector, precision)
        nOnLine += 3

        if nOnLine >= VERTEX_OUTPUT_PER_LINE:
            ret += '\n' + indent
            nOnLine = 0

    return ret
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def format_quaternion(quaternion, precision = FLOAT_PRECISION_DEFAULT):
    fmt = '%.' + str(precision) + 'f'
    if bpy.context.scene.world.preserveZUpRight == True :
        return format_float(quaternion.x, fmt) + ',' + format_float(quaternion.y, fmt) + ',' + format_float(quaternion.z, fmt) + ',' + format_float(quaternion.w, fmt)
    else :
        return format_float(quaternion.x, fmt) + ',' + format_float(quaternion.z, fmt) + ',' + format_float(quaternion.y, fmt) + ',' + format_float(-quaternion.w, fmt)
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def format_int(int):
    candidate = str(int) # when int string of an int
    if '.' in candidate:
        return format_f(floor(int)) # format_f removes un-neccessary precision
    else:
        return candidate
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def format_bool(bool):
    if bool:
        return 'true'
    else:
        return 'false'
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def post_rotate_quaternion(quat, angle):
    post = Euler((angle, 0.0, 0.0)).to_matrix()
    mqtn = quat.to_matrix()
    quat = (mqtn*post).to_quaternion()
    return quat
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def scale_vector(vector, mult, xOffset = 0):
    ret = vector.copy()
    ret.x *= mult
    ret.x += xOffset
    ret.z *= mult
    ret.y *= mult
    return ret
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def same_matrix4(matA, matB, precision = FLOAT_PRECISION_DEFAULT):
    if(matA is None or matB is None): return False
    if (len(matA) != len(matB)): return False
    fmt = '%.' + str(precision) + 'f'
    for i in range(len(matA)):
        if (format_float(matA[i][0], fmt) != format_float(matB[i][0], fmt) or
            format_float(matA[i][1], fmt) != format_float(matB[i][1], fmt) or
            format_float(matA[i][2], fmt) != format_float(matB[i][2], fmt) or
            format_float(matA[i][3], fmt) != format_float(matB[i][3], fmt) ):
            return False
    return True
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def same_vertex(vertA, vertB, precision = FLOAT_PRECISION_DEFAULT):
    if vertA is None or vertB is None: return False

    fmt = '%.' + str(precision) + 'f'
    if (format_float(vertA.x, fmt) != format_float(vertB.x, fmt) or
        format_float(vertA.y, fmt) != format_float(vertB.y, fmt) or
        format_float(vertA.z, fmt) != format_float(vertB.z, fmt) ):
        return False
    return True
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def same_quaternion(quatA, quatB, precision = FLOAT_PRECISION_DEFAULT):
    if quatA is None or quatB is None: return False

    fmt = '%.' + str(precision) + 'f'
    if (format_float(quatA.x, fmt) != format_float(quatB.x, fmt) or
        format_float(quatA.y, fmt) != format_float(quatB.y, fmt) or
        format_float(quatA.z, fmt) != format_float(quatB.z, fmt) or
        format_float(quatA.w, fmt) != format_float(quatB.w, fmt) ):
        return False
    return True
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def same_color(colorA, colorB, precision = FLOAT_PRECISION_DEFAULT):
    if colorA is None or colorB is None: return False

    fmt = '%.' + str(precision) + 'f'
    if (format_float(colorA.r, fmt) != format_float(colorB.r, fmt) or
        format_float(colorA.g, fmt) != format_float(colorB.g, fmt) or
        format_float(colorA.b, fmt) != format_float(colorB.b, fmt) ):
        return False

    return True
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def same_array(arrayA, arrayB, precision = FLOAT_PRECISION_DEFAULT):
    if(arrayA is None or arrayB is None): return False
    if len(arrayA) != len(arrayB): return False
    fmt = '%.' + str(precision) + 'f'
    for i in range(len(arrayA)):
        if format_float(arrayA[i], fmt) != format_float(arrayB[i], fmt) : return False

    return True
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def same_number(numberA, numberB, precision = FLOAT_PRECISION_DEFAULT):
    if numberA is None or numberB is None: return False

    fmt = '%.' + str(precision) + 'f'
    return format_float(numberA, fmt) == format_float(numberB, fmt)
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def shouldBeCulled(object):
    collectionName = object.users_collection[0].name
    return collectionExcluded(bpy.context.window.view_layer.layer_collection, collectionName)

def collectionExcluded(viewLayer, collectionName):
    if collectionName == viewLayer.name:
        return viewLayer.exclude

    for childViewLayers in viewLayer.children:
        result = collectionExcluded(childViewLayers, collectionName)
        if result is not None:
            return result

    return None
#===============================================================================
# module level methods for writing JSON (.babylon) files
#===============================================================================
def write_matrix4(file_handler, name, matrix, precision = FLOAT_PRECISION_DEFAULT):
    file_handler.write(',"' + name + '":[' + format_matrix4(matrix, precision) + ']')

def write_array(file_handler, name, array, precision = FLOAT_PRECISION_DEFAULT):
    file_handler.write('\n,"' + name + '":[' + format_array(array, precision) + ']')

def write_indice_array(file_handler, name, array, precision = FLOAT_PRECISION_DEFAULT):
    file_handler.write('\n,"' + name + '":[' + format_indice_array(array, precision) + ']')

def write_array3(file_handler, name, array, precision = FLOAT_PRECISION_DEFAULT):
    file_handler.write(',"' + name + '":[' + format_array3(array, precision) + ']')

def write_color(file_handler, name, color, precision = FLOAT_PRECISION_DEFAULT):
    file_handler.write(',"' + name + '":[' + format_color(color, precision) + ']')

def write_vector(file_handler, name, vector, precision = FLOAT_PRECISION_DEFAULT):
    file_handler.write(',"' + name + '":[' + format_vector(vector, precision) + ']')

def write_vector_array(file_handler, name, vectorArray, precision = FLOAT_PRECISION_DEFAULT):
    file_handler.write('\n,"' + name + '":[' + format_vector_array(vectorArray, precision, '') + ']')

def write_quaternion(file_handler, name, quaternion, precision = FLOAT_PRECISION_DEFAULT):
    file_handler.write(',"' + name  +'":[' + format_quaternion(quaternion, precision) + ']')

def write_string(file_handler, name, string, noComma = False):
    if noComma == False:
        file_handler.write(',')
    file_handler.write('"' + name + '":"' + string + '"')

def write_float(file_handler, name, float, precision = FLOAT_PRECISION_DEFAULT, noComma = False):
    if noComma == False:
        file_handler.write(',')
    file_handler.write('"' + name + '":' + format_f(float, precision = precision))

def write_int(file_handler, name, int, noComma = False):
    if noComma == False:
        file_handler.write(',')
    file_handler.write('"' + name + '":' + format_int(int))

def write_bool(file_handler, name, bool, noComma = False):
    if noComma == False:
        file_handler.write(',')
    file_handler.write('"' + name + '":' + format_bool(bool))