from .logging import *
from .package_level import *

from .f_curve_animatable import *

import bpy
from mathutils import Color, Vector

# used in Light constructor, never formally defined in Babylon, but used in babylonFileLoader
POINT_LIGHT = 0
DIRECTIONAL_LIGHT = 1
SPOT_LIGHT = 2
HEMI_LIGHT = 3

#used in ShadowGenerators
NO_SHADOWS = 'NONE'
STD_SHADOWS = 'STD'
POISSON_SHADOWS = 'POISSON'
ESM_SHADOWS = 'ESM'
BLUR_ESM_SHADOWS = 'BLUR_ESM'
CASCADED_SHADOWS = 'CASCADED'

AUTOMATIC_MODE = '0';
POWER_MODE = '1';
LUMINOUS_INTENSITY_MODE = '2';
ILLUMINANCE_MODE = '3';
LUMINANCE_MODE = '4';

DEF_SHADOW_BIAS = 0.00005
DEF_SHADOW_DARKNESS = 0
DEF_SHADOW_BLUR_SCALE = 2
DEF_SHADOW_BLUR_BOX_OFFSET = 1
DEF_AUTO_SHADOW_BOUNDS = False
DEF_SHADOW_MIN_Z = 0
DEF_SHADOW_MAX_Z = 1000000
DEF_SHADOW_LAMBDA = 0.5
#===============================================================================
class Light(FCurveAnimatable):
    def __init__(self, bpyLight, exporter, usePBRMaterials):

        exportedParent = exporter.getExportedParent(bpyLight)
        if exportedParent and exportedParent.type != 'ARMATURE':
            self.parentId = exportedParent.name

        self.name = bpyLight.name
        self.define_animations(bpyLight, False, True, False)

        light_type_items = {'POINT': POINT_LIGHT, 'SUN': DIRECTIONAL_LIGHT, 'SPOT': SPOT_LIGHT, 'AREA': HEMI_LIGHT}
        self.light_type = light_type_items[bpyLight.data.type]
        Logger.log('processing begun of light (' + ('POINT', 'DIRECTIONAL', 'SPOT', 'HEMI FROM AREA')[self.light_type] + '):  ' + self.name)

        if self.light_type == POINT_LIGHT:
            self.position = bpyLight.location
            self.range = bpyLight.data.cutoff_distance
            self.radius = bpyLight.data.shadow_soft_size

        elif self.light_type == DIRECTIONAL_LIGHT:
            self.position = bpyLight.location
            self.direction = Light.get_direction(bpyLight.matrix_local)
            self.radius = bpyLight.data.shadow_soft_size

        elif self.light_type == SPOT_LIGHT:
            self.position = bpyLight.location
            self.direction = Light.get_direction(bpyLight.matrix_local)
            self.angle = bpyLight.data.spot_size
            self.exponent = bpyLight.data.spot_blend * 2
            self.range = bpyLight.data.cutoff_distance
            self.radius = bpyLight.data.shadow_soft_size

        else:
            # Hemi discontinued for Blender 2.80, so using area
            self.range = bpyLight.data.cutoff_distance
            matrix_local = bpyLight.matrix_local.copy()
            matrix_local.translation = Vector((0, 0, 0))
            self.direction = (Vector((0, 0, -1)) @ matrix_local)
            self.direction = scale_vector(self.direction, -1)
            self.groundColor = Color((0, 0, 0))
            self.radius = bpyLight.data.size

        self.intensityMode = bpyLight.data.pbrIntensityMode if usePBRMaterials else AUTOMATIC_MODE
        self.intensity = min(bpyLight.data.energy / 10.0, 1.0) if self.intensityMode == AUTOMATIC_MODE else bpyLight.data.energy
        self.diffuse   = bpyLight.data.color
        self.specular  = bpyLight.data.color * bpyLight.data.specular_factor

        # changes to the light when there is a shadow map
        self.usingShadows = bpyLight.data.shadowMap != NO_SHADOWS
        self.autoCalcShadowZBounds = bpyLight.data.autoCalcShadowZBounds
        self.shadowMinZ = bpyLight.data.shadowMinZ
        self.shadowMaxZ = bpyLight.data.shadowMaxZ

       # inclusion section (lights run last, so all meshes already processed)
        if bpyLight.data.useOwnCollection:
            lightCollection = bpyLight.users_collection[0].name
            self.includedOnlyMeshesIds = []
            for mesh in exporter.meshesAndNodes:
                # nodes do not have a collectionName recorded, so hasattr eliminates them
                if hasattr(mesh, 'collectionName') and mesh.collectionName == lightCollection:
                    self.includedOnlyMeshesIds.append(mesh.name)
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    @staticmethod
    def get_direction(matrix):
        return (matrix.to_3x3() @ Vector((0.0, 0.0, -1.0))).normalized()
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    def to_json_file(self, file_handler):
        file_handler.write('{')
        write_string(file_handler, 'name', self.name, True)
        write_string(file_handler, 'id', self.name)
        write_float(file_handler, 'type', self.light_type)

        if hasattr(self, 'parentId'   ): write_string(file_handler, 'parentId'   , self.parentId   )
        if hasattr(self, 'position'   ): write_vector(file_handler, 'position'   , self.position   )
        if hasattr(self, 'direction'  ): write_vector(file_handler, 'direction'  , self.direction  )
        if hasattr(self, 'angle'      ): write_float (file_handler, 'angle'      , self.angle      )
        if hasattr(self, 'exponent'   ): write_float (file_handler, 'exponent'   , self.exponent   )
        if hasattr(self, 'groundColor'): write_color (file_handler, 'groundColor', self.groundColor)
        if hasattr(self, 'range'      ): write_float (file_handler, 'range'      , self.range      )

        write_int(file_handler, 'intensityMode', self.intensityMode)
        write_float(file_handler, 'intensity', self.intensity)
        write_color(file_handler, 'diffuse', self.diffuse)
        write_color(file_handler, 'specular', self.specular)
        write_float(file_handler, 'radius', self.radius)

        # changes actually being made to the associated shadow map
        if self.usingShadows:
            if self.autoCalcShadowZBounds: # default is false
                write_bool(file_handler, 'autoCalcShadowZBounds', True)
            else:
                if format_f(self.shadowMinZ) != format_f(DEF_SHADOW_MIN_Z): write_float(file_handler, 'shadowMinZ', self.shadowMinZ)
                if format_f(self.shadowMaxZ) != format_f(DEF_SHADOW_MAX_Z): write_float(file_handler, 'shadowMaxZ', self.shadowMaxZ)

        if hasattr(self, 'includedOnlyMeshesIds'):
            file_handler.write(',"includedOnlyMeshesIds":[')
            first = True
            for meshId in self.includedOnlyMeshesIds:
                if first != True:
                    file_handler.write(',')
                first = False

                file_handler.write('"' + meshId + '"')

            file_handler.write(']')

        super().to_json_file(file_handler) # Animations
        file_handler.write('}')
#===============================================================================
class ShadowGenerator:
    def __init__(self, lamp, meshesAndNodes, scene):
        Logger.log('processing begun of shadows for light:  ' + lamp.name)
        self.lightId = lamp.name
        self.mapSize = lamp.data.shadowMapSize
        self.shadowBias = lamp.data.shadowBias
        self.shadowDarkness = lamp.data.shadowDarkness

        self.useExponentialShadowMap = lamp.data.shadowMap == ESM_SHADOWS
        self.usePoissonSampling = lamp.data.shadowMap == POISSON_SHADOWS
        self.useBlurExponentialShadowMap = lamp.data.shadowMap == BLUR_ESM_SHADOWS
        self.useCascadedShadowMap = lamp.data.shadowMap == CASCADED_SHADOWS

        if self.useBlurExponentialShadowMap:
            self.shadowBlurScale = lamp.data.shadowBlurScale
            self.shadowBlurBoxOffset = lamp.data.shadowBlurBoxOffset

        if self.useCascadedShadowMap:
            if lamp.data.type == 'POINT':
                Logger.warn('Point light type incompatible with cascaded shadows. Shadows cancelled.')
                self.cancelled = True
                return

            self.shadowLambda = lamp.data.shadowLambda

        # .babylon specific section
        self.shadowCasters = []
        for mesh in meshesAndNodes:
            if (hasattr(mesh, 'castShadows') and mesh.castShadows):
                self.shadowCasters.append(mesh.name)
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    def to_json_file(self, file_handler):
        # implement cancelled
        if hasattr(self, 'cancelled') : return
        file_handler.write('{')
        write_int(file_handler, 'mapSize', self.mapSize, True)
        write_string(file_handler, 'lightId', self.lightId)
        write_float(file_handler, 'bias', self.shadowBias, precision = 5)
        write_float(file_handler, 'darkness', self.shadowDarkness)

        if self.useExponentialShadowMap:
            write_bool(file_handler, 'useExponentialShadowMap', self.useExponentialShadowMap)
        elif self.usePoissonSampling:
            write_bool(file_handler, 'usePoissonSampling', self.usePoissonSampling)
        elif self.useBlurExponentialShadowMap:
            write_bool(file_handler, 'useBlurExponentialShadowMap', self.useBlurExponentialShadowMap)
            if format_f(self.shadowBlurScale) != format_f(DEF_SHADOW_BLUR_SCALE)         : write_int(file_handler, 'blurScale', self.shadowBlurScale)
            if format_f(self.shadowBlurBoxOffset) != format_f(DEF_SHADOW_BLUR_BOX_OFFSET): write_int(file_handler, 'blurBoxOffset', self.shadowBlurBoxOffset)
        elif self.useCascadedShadowMap:
            write_string(file_handler, 'className', 'CascadedShadowGenerator')
            if format_f(self.shadowLambda) != format_f(DEF_SHADOW_LAMBDA): write_float (file_handler, 'lambda', self.shadowLambda)

        file_handler.write(',"renderList":[')
        first = True
        for caster in self.shadowCasters:
            if first != True:
                file_handler.write(',')
            first = False

            file_handler.write('"' + caster + '"')

        file_handler.write(']')
        file_handler.write('}')
#===============================================================================
bpy.types.Light.autoAnimate = bpy.props.BoolProperty(
    name='Auto launch animations',
    description='',
    default = False
)

bpy.types.Light.useOwnCollection = bpy.props.BoolProperty(
    name='This collection Only',
    description='Restrict this light to only shining on meshes also in this collection',
    default = False
)

bpy.types.Light.pbrIntensityMode = bpy.props.EnumProperty(
    name='', # use a row heading for label to reduce dropdown width
    description='No Meaning for STD Materials',
    items = ((AUTOMATIC_MODE         , 'Automatic'          , ''),
             (POWER_MODE             , 'Luminous Power'    , 'Lumen (lm)'),
             (LUMINOUS_INTENSITY_MODE, 'Luminous Intensity', 'Candela (lm/sr)'),
             (ILLUMINANCE_MODE       , 'Illuminance'       , 'Lux (lm/m^2)'),
             (LUMINANCE_MODE         , 'Luminance'         , 'Nit (cd/m^2')
            ),
    default = AUTOMATIC_MODE
)

bpy.types.Light.shadowMap = bpy.props.EnumProperty(
    name='Shadow Map',
    description='For Dynamic shadows.  Not available for Area lights,\nwhich convert to HemisphericLight',
    items = ((NO_SHADOWS           , 'None'         , 'No Shadow Maps'),
             (STD_SHADOWS          , 'Standard'     , 'Use Standard Shadow Maps'),
             (POISSON_SHADOWS      , 'Poisson'      , 'Use Poisson Sampling'),
             (ESM_SHADOWS          , 'ESM'          , 'Use Exponential Shadow Maps'),
             (BLUR_ESM_SHADOWS     , 'Blur ESM'     , 'Use Blur Exponential Shadow Maps'),
             (CASCADED_SHADOWS     , 'Cascaded'     , 'Use Cascaded Shadow Maps; NOT valid with a Point light')
            ),
    default = NO_SHADOWS
)

bpy.types.Light.shadowMapSize = bpy.props.IntProperty(
    name='Shadow Map Size',
    description='',
    default = 512
)
bpy.types.Light.shadowBias = bpy.props.FloatProperty(
    name='Shadow Bias',
    description='',
    default = DEF_SHADOW_BIAS
)

bpy.types.Light.autoCalcShadowZBounds = bpy.props.BoolProperty(
    name='Auto Calculate Shadow Z Bounds',
    description='',
    default = DEF_AUTO_SHADOW_BOUNDS
)
bpy.types.Light.shadowMinZ = bpy.props.FloatProperty(
    name='Min Z',
    description='The minimum distance a caster may be from the light.\nMust be < max',
    default = DEF_SHADOW_MIN_Z,
    min = 0,
    max = DEF_SHADOW_MAX_Z - 1
)
bpy.types.Light.shadowMaxZ = bpy.props.FloatProperty(
    name='Max Z',
    description='The maximum distance a caster may be from the light.\nMust be > min',
    default = DEF_SHADOW_MAX_Z,
    min = 0,
    max = DEF_SHADOW_MAX_Z
)

bpy.types.Light.shadowBlurScale = bpy.props.IntProperty(
    name='Blur Scale',
    description='Setting when using a Blur Variance shadow map',
    default = DEF_SHADOW_BLUR_SCALE
)

bpy.types.Light.shadowBlurBoxOffset = bpy.props.IntProperty(
    name='Blur Box Offset',
    description='Setting when using a Blur Variance shadow map',
    default = DEF_SHADOW_BLUR_BOX_OFFSET
)
bpy.types.Light.shadowDarkness = bpy.props.FloatProperty(
    name='Shadow Darkness',
    description='Shadow Darkness',
    default = DEF_SHADOW_DARKNESS,
    min = 0,
    max = 1
)

bpy.types.Light.shadowLambda = bpy.props.FloatProperty(
    name='Shadow Lambda',
    description='',
    default=DEF_SHADOW_LAMBDA
)
#===============================================================================
class BJS_PT_LightPanel(bpy.types.Panel):
    bl_label = get_title()
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'data'

    @classmethod
    def poll(cls, context):
        ob = context.object
        return ob is not None and isinstance(ob.data, bpy.types.Light)

    def draw(self, context):
        ob = context.object
        layout = self.layout
        row = layout.row(heading='PBR Intensity Mode')
        row.prop(ob.data, 'pbrIntensityMode')

        layout.prop(ob.data, 'useOwnCollection')
        layout.prop(ob.data, 'shadowMap')

        usingShadows = ob.data.shadowMap != NO_SHADOWS
        row = layout.row()
        row.enabled = usingShadows
        row.prop(ob.data, 'shadowMapSize')

        row = layout.row()
        row.enabled = usingShadows
        row.prop(ob.data, 'shadowBias')

        row = layout.row()
        row.enabled = usingShadows
        row.prop(ob.data, 'shadowDarkness')

        box = layout.box()
        row = box.row()
        row.enabled = usingShadows
        row.prop(ob.data, 'autoCalcShadowZBounds')
        row = box.row()
        row.enabled = usingShadows and not ob.data.autoCalcShadowZBounds
        row.prop(ob.data, 'shadowMinZ')
        row.prop(ob.data, 'shadowMaxZ')

        box = layout.box()
        box.label(text="Blur ESM Shadows")
        usingBlur = ob.data.shadowMap == BLUR_ESM_SHADOWS
        row = box.row()
        row.enabled = usingBlur
        row.prop(ob.data, 'shadowBlurScale')
        row = box.row()
        row.enabled = usingBlur
        row.prop(ob.data, 'shadowBlurBoxOffset')

        box = layout.box()
        box.label(text="Cascaded Shadows")
        cascading = ob.data.shadowMap == CASCADED_SHADOWS
        row = box.row()
        row.enabled = cascading
        row.prop(ob.data, 'shadowLambda')

        layout.prop(ob.data, 'autoAnimate')
