from ..logging import *
from ..package_level import *

from .nodes.abstract import UV_ACTIVE_TEXTURE
from .nodes.mapping import MappingBJSNode

import bpy

from base64 import b64encode
from os import path, remove
from shutil import copy
from sys import exc_info # for writing errors to log file

# used externally by TextureImageBJSNode, defined in BABYLON.Texture
CLAMP_ADDRESSMODE = 0 # default
WRAP_ADDRESSMODE = 1
#MIRROR_ADDRESSMODE = 2

# used externally by TextureImageBJSNode, defined in BABYLON.Texture
EXPLICIT_MODE = 0 # default
#SPHERICAL_MODE = 1
#PLANAR_MODE = 2
CUBIC_MODE = 3
#PROJECTION_MODE = 4
#SKYBOX_MODE = 5

NON_ALPHA_FORMATS = {'BMP', 'JPEG'}

# defaults
U_OFFSET = 0
V_OFFSET = 0
U_SCALE  = 1
V_SCALE  = 1
U_ANG    = 0
V_ANG    = 0
W_ANG    = 0
#===============================================================================
class Texture:
    # called in constructor for BakeTexture, but for BJSImageTexture, called in Mesh, after ruling out will be baked
    # An environment texture cannot be base64, & does not supply a mesh argument
    def process(self, exporter, canBeBase64 = True, bpyMesh = None):
        settings = bpy.context.scene.world
        inlineTextures = canBeBase64 and settings.inlineTextures

        filePath = self.image.filepath
        sourceFilepath = path.normpath(bpy.path.abspath(filePath))
        self.fileNoPath = path.basename(sourceFilepath)

        # name of the texture without the extension, made into a legal js name, so load function can be written
        self.name = legal_js_identifier(self.fileNoPath.rpartition('.')[0])

        # always write the file out, since base64 encoding is easiest from a file
        try:
            Logger.log('processing texture ' + self.name, 3)

            # when coming from either a packed image or a baked image, then save_render
            if self.isInternalImage:
                if inlineTextures:
                    textureFile = path.join(exporter.textureFullPathDir, self.fileNoPath + 'temp')
                else:
                    textureFile = path.join(exporter.textureFullPathDir, self.fileNoPath)
                self.image.save_render(textureFile)

            # when backed by an actual file, copy to target dir, unless inlining
            else:
                textureFile = bpy.path.abspath(filePath)
                if not inlineTextures:
                    copy(textureFile, exporter.textureFullPathDir)
        except:
            ex = exc_info()
            msg = str(ex[1])
            if 'are the same file' not in msg:
                Logger.warn('Exception during copy:\n\t\t\t\t\t'+ msg, 4)

        if inlineTextures:
            # base64 is easiest from a file, so sometimes a temp file was made above;  need to delete those
            with open(textureFile, "rb") as image_file:
                asString = b64encode(image_file.read()).decode()
            self.encoded_URI = 'data:image/' + self.image.file_format + ';base64,' + asString

            if self.isInternalImage:
                remove(textureFile)

        else:
            # adjust name to reflect path
            relPath = exporter.settings.textureDir
            if len(relPath) > 0:
                if not relPath.endswith('/'): relPath += '/'
                self.fileNoPath = relPath + self.fileNoPath

        if bpyMesh:
            if not self.uvMapName or self.uvMapName == UV_ACTIVE_TEXTURE:  # only for image based & no node specifying
                self.uvMapName = bpyMesh.data.uv_layers.active.name

            if bpyMesh.data.uv_layers[0].name == self.uvMapName:
                self.coordinatesIndex = 0
            elif bpyMesh.data.uv_layers[1].name == self.uvMapName:
                self.coordinatesIndex = 1
            else:
                Logger.warn('Texture is not mapped as UV or UV2, assigned 1', 5)
                self.coordinatesIndex = 0
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    def to_json_file(self, file_handler):
        file_handler.write(', \n"' + self.textureType + '":{')
        write_string(file_handler, 'name', self.fileNoPath, True)

        write_bool(file_handler, 'hasAlpha', self.hasAlpha)
        write_float(file_handler, 'level', self.level)

        write_int(file_handler, 'coordinatesMode', self.coordinatesMode)
        write_int(file_handler, 'coordinatesIndex', self.coordinatesIndex)

        if not same_number(self.uOffset, U_OFFSET): write_float(file_handler, 'uOffset', self.uOffset)
        if not same_number(self.vOffset, V_OFFSET): write_float(file_handler, 'vOffset', self.vOffset)
        if not same_number(self.uScale , U_SCALE ): write_float(file_handler, 'uScale', self.uScale)
        if not same_number(self.vScale , V_SCALE ): write_float(file_handler, 'vScale', self.vScale)
        if not same_number(self.uAng   , U_ANG   ): write_float(file_handler, 'uAng', self.uAng)
        if not same_number(self.vAng   , V_ANG   ): write_float(file_handler, 'vAng', self.vAng)
        if not same_number(self.wAng   , W_ANG   ): write_float(file_handler, 'wAng', self.wAng)

        if not same_number(self.wrapU, CLAMP_ADDRESSMODE): write_int(file_handler, 'wrapU', self.wrapU)
        if not same_number(self.wrapV, CLAMP_ADDRESSMODE): write_int(file_handler, 'wrapV', self.wrapV)
        
        if hasattr(self,'encoded_URI'):
            write_string(file_handler, 'base64String', self.encoded_URI)
        file_handler.write('}')
#===============================================================================
class BakedTexture(Texture):
    def __init__(self, textureType, bakedMaterial, bpyMesh, exporter):
        self.textureType = textureType

        # super class does not have a constructor
        self.image = bakedMaterial.image
        self.isInternalImage = True
        self.hasAlpha = bakedMaterial.image.file_format not in NON_ALPHA_FORMATS
        self.level = 1
        self.coordinatesMode = EXPLICIT_MODE

        self.uOffset = U_OFFSET
        self.vOffset = V_OFFSET
        self.uScale  = U_SCALE
        self.vScale  = V_SCALE
        self.uAng    = U_ANG
        self.vAng    = V_ANG
        self.wAng    = W_ANG

        self.wrapU = CLAMP_ADDRESSMODE
        self.wrapV = CLAMP_ADDRESSMODE

        self.uvMapName = bakedMaterial.uvMapName
        self.process(exporter, True, bpyMesh)
#===============================================================================
class BJSImageTexture(Texture):
    def __init__(self, bjsImageNode, isForEnvironment = False):
        # super class does not have a constructor
        if bjsImageNode.image is None:
            Logger.error('Node has no image.  This should be being filtered upstream.  Bad programmer.')
            return

        self.image = bjsImageNode.image
        self.isInternalImage = self.image.packed_file

        # do not need anything else when an environment texture
        if isForEnvironment: return

        self.level = 1
        self.hasAlpha = bjsImageNode.alpha
        self.coordinatesMode = bjsImageNode.coordinatesMode
        self.wrapU = bjsImageNode.wrap
        self.wrapV = bjsImageNode.wrap
        self.uvMapName = bjsImageNode.uvMapName # bubbled up, or None

        # probably should not be expecting a mapping node for world, as it would not work, but working in Blender is not critical
        mappingNode = bjsImageNode.findInput('Vector', MappingBJSNode.bpyType)
        if mappingNode is not None:
            self.uOffset = mappingNode.offset.x
            self.vOffset = mappingNode.offset.y
            self.uScale  = mappingNode.scale.x
            self.vScale  = mappingNode.scale.y
            self.uAng    = mappingNode.ang.x
            self.vAng    = mappingNode.ang.y
            self.wAng    = mappingNode.ang.z
        else:
            self.uOffset = U_OFFSET
            self.vOffset = V_OFFSET
            self.uScale  = U_SCALE
            self.vScale  = V_SCALE
            self.uAng    = U_ANG
            self.vAng    = V_ANG
            self.wAng    = W_ANG
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    # The type is determined later by the node that has the output of the node passed in the constructor
    def assignChannel(self, textureType):
        self.textureType = textureType