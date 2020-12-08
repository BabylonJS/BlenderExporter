from .logging import *
from .package_level import *

from .materials.nodes.abstract import *
from .materials.env_textures.support import *

import bpy
from os import path
from shutil import copy
from sys import exc_info # for writing errors to log file

SCOPE_ALL = 'ALL'
SCOPE_SELECTED = 'SELECTED'
SCOPE_VISIBLE = 'VISIBLE'

# used in World constructor, defined in BABYLON.Scene; must be strings to be in EnumProperty
FOGMODE_NONE = "0"
FOGMODE_EXP = "1"
FOGMODE_EXP2 = "2"
FOGMODE_LINEAR = "3"

ENV_SZ_1 = "128"
ENV_SZ_2 = "256"
ENV_SZ_3 = "512"

#===============================================================================
class World:
    def __init__(self, scene, exporter):
        self.autoClear = True
        world = scene.world
        self.clear_color = world.color

        self.gravity = scene.gravity
        self.writeManifestFile = world.writeManifestFile
        self.writeCsvFile = world.writeCsvFile
        self.preserveZUpRight = world.preserveZUpRight

        self.fogMode = int(world.fogMode)
        if self.fogMode > 0:
            self.fogColor = world.color
            self.fogStart = world.mist_settings.start
            self.fogEnd = world.mist_settings.depth
            self.fogDensity = world.fogDensity

        # ensure all UI vars assigned & as well as envExported
        self.envTexture = world.evtTexture
        self.envTexRotationY = world.envTexRotationY
        self.skyBox = world.skyBox
        self.boxBlur = world.boxBlur
        self.envExported = False

        # no sense exporting an environment unless either using PBR or a skybox
        if self.skyBox or world.usePBRMaterials:
            if self.envTexture == USE_BLENDER_FOR_ENV:
                self.environmentTextureSize = world.environmentTextureSize
                if world.use_nodes:
                    worldNode = AbstractBJSNode.readWorldNodeTree(world.node_tree)
                    if worldNode is not None and ENVIRON_TEX in worldNode.bjsTextures:
                        bjsTexture = worldNode.bjsTextures[ENVIRON_TEX]
                        bjsTexture.process(exporter, False) # An environment texture cannot be base64
                        self.envFileNoPath = bjsTexture.fileNoPath
                        self.envExported = True
            else:
                self.envFileNoPath = self.envTexture
                self.envExported = True
                try:
                    Logger.log('processing env texture ' + self.envFileNoPath, 3)
                    copy(path.join(getAddonEnvTexturePath(), self.envFileNoPath), exporter.textureFullPathDir)
                except:
                    ex = exc_info()
                    msg = str(ex[1])
                    if 'are the same file' not in msg:
                        Logger.warn('Exception during copy:\n\t\t\t\t\t'+ msg, 4)

        Logger.log('Python World class constructor completed')
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    def to_json_file(self, file_handler, exporter):
        write_bool(file_handler, 'autoClear', self.autoClear, True)
        write_color(file_handler, 'clearColor', self.clear_color)
        write_vector(file_handler, 'gravity', self.gravity)

        if exporter.needPhysics:
            write_bool(file_handler, 'physicsEnabled', True)

        if self.fogMode > 0:
            write_int(file_handler, 'fogMode', self.fogMode)
            write_color(file_handler, 'fogColor', self.fogColor)
            write_float(file_handler, 'fogStart', self.fogStart)
            write_float(file_handler, 'fogEnd', self.fogEnd)
            write_float(file_handler, 'fogDensity', self.fogDensity)

        if self.envExported:
            write_string(file_handler, 'environmentTexture', self.envFileNoPath)
            if self.envTexture == USE_BLENDER_FOR_ENV:
                write_string(file_handler, 'environmentTextureType', 'BABYLON.HDRCubeTexture')
                write_int(file_handler, 'environmentTextureSize', self.environmentTextureSize)
            write_bool(file_handler, 'isPBR', exporter.settings.usePBRMaterials)
            write_float(file_handler, 'environmentTextureRotationY', self.envTexRotationY * 0.0174533)
            # also attempt to create a sky box when environment texture exported
            if self.skyBox:
                write_bool(file_handler, 'createDefaultSkybox', True)
                write_float(file_handler, 'skyboxBlurLevel ', self.boxBlur)
#===============================================================================
###      Skybox environment      ###
bpy.types.World.environmentTextureSize = bpy.props.EnumProperty(
    name='Texture Size',
    description='This the size of the cube texture in px / face.  Only used for .hdr files.',
    items = ((ENV_SZ_1, ENV_SZ_1, ''),
             (ENV_SZ_2, ENV_SZ_2, ''),
             (ENV_SZ_3, ENV_SZ_3, '')
            ),
    default = ENV_SZ_1
)
bpy.types.World.envTexRotationY = bpy.props.FloatProperty(
    name='Y Rotation',
    description='The degrees to rotate the environment texture / sky box',
    default = 0, min = 0, max = 360
)
bpy.types.World.skyBox = bpy.props.BoolProperty(
    name='Sky Box from Environment Tex',
    description='When checked Create a sky box.  A background surface node with an Environment Texture input is also required.',
    default = False
)
bpy.types.World.boxBlur = bpy.props.FloatProperty(
    name='Box Blur',
    description='How much blur should be applied to the sky box',
    default = 0, min = 0, max = 1.0
)

###      Fog     ###
bpy.types.World.fogMode = bpy.props.EnumProperty(
    name='Mode',
    description='Babylon JS fog mode',
    items = ((FOGMODE_NONE  , 'None'               , 'No Fog'),
             (FOGMODE_LINEAR, 'Linear'             , 'Linear Fog'),
             (FOGMODE_EXP   , 'Exponential'        , 'Exponential Fog'),
             (FOGMODE_EXP2  , 'Exponential Squared', 'Exponential Squared Fog')
            ),
    default = FOGMODE_NONE
)
bpy.types.World.fogDensity = bpy.props.FloatProperty(
    name='Density',
    description='How dense the fog should be',
    default = 0.3, min = 0, max = 1.0
)

###     Max Decimal Precision     ###
bpy.types.World.positionsPrecision = bpy.props.IntProperty(
    name='Positions / Shape Keys:',
    description='Max number of digits for positions / shape keys.  Reducing useful to reduce\nfile size when units of meshes already small, .e.g inches',
    default = 4, min = 0, max = 8
)
bpy.types.World.normalsPrecision = bpy.props.IntProperty(
    name='Normals:',
    description='Max number of digits for normals',
    default = 3, min = 1, max = 8
)
bpy.types.World.UVsPrecision = bpy.props.IntProperty(
    name='UVs:',
    description='Max number of digits for UVs',
    default = 3, min = 1, max = 8
)
bpy.types.World.vColorsPrecision = bpy.props.IntProperty(
    name='Vertex Colors:',
    description='Number of digits for colors',
    default = 3, min = 1, max = 8
)
bpy.types.World.mWeightsPrecision = bpy.props.IntProperty(
    name='Matrix Weights:',
    description='Max number of digits for armature weights',
    default = 2, min = 1, max = 8
)

###     Textures / Materials     ###
bpy.types.World.inlineTextures = bpy.props.BoolProperty(
    name='inline',
    description='Turn textures into encoded strings, for direct inclusion into source code.\nDoes not apply to environment texture.',
    default = False
)
bpy.types.World.textureDir = bpy.props.StringProperty(
    name='Sub-directory',
    description='The path below the output directory to write texture files (any separators OS dependent)',
    default = ''
)
bpy.types.World.usePBRMaterials = bpy.props.BoolProperty(
    name='Use PBR Materials',
    description="Export as a PBR materials, when checked",
    default = True,
)
bpy.types.World.environmentIntensity = bpy.props.FloatProperty(
    name='Environment Intensity',
    description='This is the intensity of the environment to be applied to materials.\nNo meaning unless exporting PBR materials.',
    default = 1.0, min = 0, max = 1.0
)
###     Sound     ###
bpy.types.World.attachedSound = bpy.props.StringProperty(
    name='Sound',
    description='',
    default = ''
)
bpy.types.World.autoPlaySound = bpy.props.BoolProperty(
    name='Auto play sound',
    description='',
    default = True
)
bpy.types.World.loopSound = bpy.props.BoolProperty(
    name='Loop sound',
    description='',
    default = True
)

###     Animation     ###
bpy.types.World.currentActionOnly = bpy.props.BoolProperty(
    name='Only Currently Assigned Actions',
    description="When true, only the currently assigned action is exported.",
    default = True,
)
bpy.types.World.autoAnimate = bpy.props.BoolProperty(
    name='Auto launch non-skeleton animations',
    description='Start all animations, except for bones.',
    default = False
)
bpy.types.World.ignoreIKBones = bpy.props.BoolProperty(
    name='Ignore IK Bones',
    description="Do not export bones with either '.ik' or 'ik.'(not case sensitive) in the name",
    default = False,
)

bpy.types.World.writeCsvFile = bpy.props.BoolProperty(
    name='Write .csv file',
    description="Write mesh statistics into a spreadsheet file for analysis",
    default = False,
)

###    JSON Specific     ###
bpy.types.World.writeManifestFile = bpy.props.BoolProperty(
    name='Write .manifest file',
    description="Automatically create or update [filename].babylon.manifest for this file",
    default = True,
)

###    Preserve Z-up and right-handed coordinate     ###
bpy.types.World.preserveZUpRight = bpy.props.BoolProperty(
    name='Preserve Z-up right-handed coordinate (EXPERIMENTAL)',
    description="By default, Y and Z are flipped by the exporter. This setting prevent that",
    default = False,
)
#===============================================================================
class BJS_PT_WorldPanel(bpy.types.Panel):
    bl_label = get_title()
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'world'

    @classmethod
    def poll(cls, context):
        ob = context.world
        return ob is not None and isinstance(ob, bpy.types.World)

    def draw(self, context):
        layout = self.layout

        world = context.world

        box = layout.box()
        box.label(text='Sky Box / Environment Texture:')
        box.prop(world, 'evtTexture')
        box.prop(world, 'envTexRotationY')

        row = box.row()
        row.enabled = world.evtTexture == USE_BLENDER_FOR_ENV
        row.prop(world, 'environmentTextureSize')

        row = box.row()
        row.prop(world, 'skyBox')
        row.prop(world, 'boxBlur')

        box = layout.box()
        box.label(text='Fog:')
        row = box.row()
        row.prop(world, 'fogMode')
        row.prop(world, 'fogDensity')

        box = layout.box()
        box.label(text='Max Decimal Precision:')
        box.prop(world, 'positionsPrecision')
        box.prop(world, 'normalsPrecision')
        box.prop(world, 'UVsPrecision')
        box.prop(world, 'vColorsPrecision')
        box.prop(world, 'mWeightsPrecision')

        box = layout.box()
        box.label(text='Textures / Materials:')
        box.prop(world, 'inlineTextures')
        row = box.row()
        row.enabled = not world.inlineTextures
        row.prop(world, 'textureDir')
        box.prop(world, 'usePBRMaterials')
        row = box.row()
        row.enabled = world.usePBRMaterials
        row.prop(world, 'environmentIntensity')

        box = layout.box()
        box.prop(world, 'attachedSound')
        row = box.row()
        row.prop(world, 'autoPlaySound')
        row.prop(world, 'loopSound')

        box = layout.box()
        box.label(text='Animation:')
        box.prop(world, 'currentActionOnly')
        box.prop(world, 'autoAnimate')
        box.prop(world, 'ignoreIKBones')

        layout.prop(world, 'writeCsvFile')

        layout.prop(world, 'writeManifestFile')
        layout.prop(world, 'preserveZUpRight')

