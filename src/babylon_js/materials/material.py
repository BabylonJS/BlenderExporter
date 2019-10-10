from ..logging import *
from ..package_level import *

from .nodes.abstract import *
from .texture import BakedTexture

import bpy

PBRMATERIAL_OPAQUE = '0'
PBRMATERIAL_ALPHATEST = '1'
PBRMATERIAL_ALPHABLEND = '2'
PBRMATERIAL_ALPHATESTANDBLEND  = '3'

#===============================================================================
class MultiMaterial:
    def __init__(self, material_slots, idx, nameSpace):
        self.name = nameSpace + '.' + 'Multimaterial#' + str(idx)
        Logger.log('processing begun of multimaterial:  ' + self.name, 2)
        self.material_slots = material_slots
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    def to_json_file(self, file_handler):
        file_handler.write('{')
        write_string(file_handler, 'name', self.name, True)
        write_string(file_handler, 'id', self.name)

        file_handler.write(',"materials":[')
        first = True
        for material in self.material_slots:
            if first != True:
                file_handler.write(',')
            file_handler.write('"' + material.name +'"')
            first = False
        file_handler.write(']')
        file_handler.write('}')
#===============================================================================
class BJSMaterial:
    # mat can either be a blender material, or a previously instanced BJSMaterial, & now baking
    def __init__(self, mat, exporter):
        # initialize; appended to either in processImageTextures() or bakeChannel()
        self.textures = {}

        self.isPBR = exporter.settings.usePBRMaterials
        self.textureFullPathDir = exporter.textureFullPathDir
        self.textureDir = exporter.settings.textureDir

        # transfer from either the Blender or previous BJSMaterial
        self.checkReadyOnlyOnce = mat.checkReadyOnlyOnce
        self.maxSimultaneousLights = mat.maxSimultaneousLights
        self.backFaceCulling = mat.backFaceCulling
        self.use_nodes = mat.use_nodes
        self.transparencyMode = mat.transparencyMode
        self.alphaCutOff = mat.alphaCutOff
        self.intensityOverride = mat.intensityOverride
        self.environmentIntensity = mat.environmentIntensity if mat.intensityOverride else exporter.settings.environmentIntensity

        if not isinstance(mat, BJSMaterial):
            bpyMaterial = mat
            self.name = bpyMaterial.name
            Logger.log('processing begun of material:  ' +  self.name, 2)

            if self.use_nodes:
                self.bjsNodeTree = AbstractBJSNode.readMaterialNodeTree(bpyMaterial.node_tree)
            else:
                self.diffuseColor = bpyMaterial.diffuse_color
                self.specularColor = bpyMaterial.specular_intensity * bpyMaterial.specular_color
                self.metallic = bpyMaterial.metallic
        else:
            self.name = mat.name
            self.bjsNodeTree = mat.bjsNodeTree
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    # broken out, so can be done later, after it is known baking is not going to be required
    # called by Mesh constructor, return whether material has textures or not
    def processImageTextures(self, bpyMesh):
        if not self.use_nodes: return False

        for texType, tex in self.bjsNodeTree.bjsTextures.items():
            self.textures[texType] = tex
            tex.process(self, True, bpyMesh)

        return len(self.textures.items()) > 0
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    def bake(self, bpyMesh, recipe):
        from time import time
        start_time = time()

        # texture is baked from selected mesh(es), need to insure this mesh is only one selected
        bpy.ops.object.select_all(action='DESELECT')
        bpyMesh.select_set(True)

        # transfer from Mesh custom properties
        bakeSize    = bpyMesh.data.bakeSize
        bakeQuality = bpyMesh.data.bakeQuality # for lossy compression formats
        forceBaking = bpyMesh.data.forceBaking
        usePNG      = bpyMesh.data.usePNG

        # store setting to restore; always bake using CYCLES, GPU, and performance improvements of tile size & samples
        # does not fail when no GPU
        scene = bpy.context.scene
        render = scene.render

        deviceHold = scene.cycles.device
        scene.cycles.device = 'GPU'

        engineHold = render.engine
        render.engine = 'CYCLES'

        tileXHold = render.tile_x
        tileYHold = render.tile_y
        render.tile_x = bakeSize
        render.tile_y = bakeSize

        usePassIndirectHold = render.bake.use_pass_indirect
        usePassDirectHold   = render.bake.use_pass_direct
        print('usePassDirectHold  ' + str(usePassDirectHold))
        render.bake.use_pass_indirect = False
        render.bake.use_pass_direct   = False

        samplesHold = scene.cycles.samples
        scene.cycles.samples = 16

        # mode_set's only work when there is an active object
        bpy.context.view_layer.objects.active = bpyMesh

        # UV unwrap operates on mesh in only edit mode, procedurals can also give error of 'no images to be found' when not done
        # select all verticies of mesh, since smart_project works only with selected verticies
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')

        # you need UV on a mesh in order to bake image.  This is not reqd for procedural textures, so may not exist
        # need to look if it might already be created, if so use the first one
        uv = bpyMesh.data.uv_layers[0] if len(bpyMesh.data.uv_layers) > 0 else None

        if uv == None or recipe.isMultiMaterial:
            uv = bpyMesh.data.uv_layers.new(name='BakingUV')
            uv.active = True
            uv.active_render = not forceBaking # want the other uv's for the source when combining

            bpy.ops.uv.smart_project(angle_limit = 66.0, island_margin = 0.0, user_area_weight = 1.0, use_aspect = True, stretch_to_bounds = True)

            # syntax for using unwrap enstead of smart project
#            bpy.ops.uv.unwrap(margin = 1.0) # defaulting on all
            self.uvMapName = 'BakingUV'  # issues with cycles when not done this way
        else:
            self.uvMapName = uv.name

        format = 'PNG' if usePNG else 'JPEG'

        # create a temporary image & link it to the UV/Image Editor so bake_image works
        self.image = bpy.data.images.new(name = bpyMesh.name + '_BJS_BAKE', width = bakeSize, height = bakeSize, alpha = usePNG, float_buffer = False)
        self.image.file_format = format
    #    self.image.mapping = 'UV' # default value

        image_settings = render.image_settings
        image_settings.file_format = format
        image_settings.color_mode = 'RGBA' if usePNG else 'RGB'
        image_settings.quality = bakeQuality # for lossy compression formats
        image_settings.compression = bakeQuality  # Amount of time to determine best compression: 0 = no compression with fast file output, 100 = maximum lossless compression with slow file output

        # now go thru all the textures that need to be baked
        if recipe.diffuseChannel:
            self.bakeChannel(DIFFUSE_TEX , 'DIFFUSE', usePNG, recipe.node_trees, bpyMesh)

        if recipe.ambientChannel:
            self.bakeChannel(AMBIENT_TEX , 'AO'     , usePNG, recipe.node_trees, bpyMesh)

        if recipe.emissiveChannel:
            self.bakeChannel(EMMISIVE_TEX, 'EMIT'   , usePNG, recipe.node_trees, bpyMesh)

        if recipe.specularChannel:
            self.bakeChannel(SPECULAR_TEX, 'GLOSSY' , usePNG, recipe.node_trees, bpyMesh)

        if recipe.bumpChannel:
            self.bakeChannel(BUMP_TEX    , 'NORMAL' , usePNG, recipe.node_trees, bpyMesh)

        # Toggle vertex selection & mode, if setting changed their value
        bpy.ops.mesh.select_all(action='TOGGLE')  # still in edit mode toggle select back to previous
        bpy.ops.object.mode_set(toggle=True)      # change back to Object

        bpy.ops.object.select_all(action='TOGGLE') # change scene selection back, not seeming to work

        # restore settings
        scene.cycles.device = deviceHold
        render.engine = engineHold
        render.tile_x = tileXHold
        render.tile_y = tileYHold
        render.bake.use_pass_indirect = usePassIndirectHold
        render.bake.use_pass_direct   = usePassDirectHold
        render.bake.use_pass_indirect = False
        render.bake.use_pass_direct   = False
        scene.cycles.samples = samplesHold

        elapsed_time = time() - start_time
        minutes = floor(elapsed_time / 60)
        seconds = elapsed_time - (minutes * 60)
        Logger.log('bake time:  ' + str(minutes) + ' min, ' + format_f(seconds) + ' secs', 3)
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    def bakeChannel(self, bjs_type, bake_type, usePNG, node_trees, bpyMesh):
        Logger.log('Baking texture, type: ' + bake_type + ', mapped using: ' + self.uvMapName, 3)
        legalName = legal_js_identifier(self.name)
        self.image.filepath = legalName + '_' + bake_type + ('.png' if usePNG else '.jpg')

        # create an unlinked temporary node to bake to for each material
        for tree in node_trees:
            bakeNode = tree.nodes.new(type='ShaderNodeTexImage')
            bakeNode.image = self.image
            bakeNode.select = True
            tree.nodes.active = bakeNode

        bpy.ops.object.bake(type = bake_type, use_clear = True, margin = 5, use_selected_to_active = False)

        for tree in node_trees:
            tree.nodes.remove(tree.nodes.active)

        self.textures[bjs_type] = BakedTexture(bjs_type, self, bpyMesh)
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    def to_json_file(self, file_handler):
        file_handler.write('{')
        write_string(file_handler, 'name', self.name, True)
        write_string(file_handler, 'id', self.name)
        write_string(file_handler, 'customType', 'BABYLON.PBRMaterial' if self.isPBR else 'BABYLON.StandardMaterial')

        # properties from UI
        write_bool(file_handler, 'backFaceCulling', self.backFaceCulling)
        write_bool(file_handler, 'checkReadyOnlyOnce', self.checkReadyOnlyOnce)
        write_int(file_handler, 'maxSimultaneousLights', self.maxSimultaneousLights)
        if self.isPBR: write_float(file_handler, 'environmentIntensity', self.environmentIntensity)

        if not self.use_nodes:
            propName = 'albedoColor' if self.isPBR else 'diffuseColor'
            write_color(file_handler, propName, self.diffuseColor)

            propName = 'reflectivityColor' if self.isPBR else 'specularColor'
            write_color(file_handler, propName, self.specularColor)

            if self.isPBR:
                write_float(file_handler, 'metallic', self.metallic)

            file_handler.write('}')
            return

        #--- scalar properties, when not also a texture ----

        # sources diffuse & principled nodes
        if self.bjsNodeTree.diffuseColor is not None and DIFFUSE_TEX not in self.textures:
            propName = 'albedo' if self.isPBR else 'diffuse'
            write_color(file_handler, propName, self.bjsNodeTree.diffuseColor)

        # source ambientOcclusion node
        if self.bjsNodeTree.ambientColor is not None:
            write_color(file_handler, 'ambient', self.bjsNodeTree.ambientColor)

        # source emissive node
        if self.bjsNodeTree.emissiveColor is not None:
            write_color(file_handler, 'emissive', self.bjsNodeTree.emissiveColor)

        # sources glossy & principled nodes
        if self.bjsNodeTree.specularColor is not None and SPECULAR_TEX not in self.textures:
            propName = 'reflectivity' if self.isPBR else 'specular'
            write_color(file_handler, propName, self.bjsNodeTree.specularColor)

        # sources glossy & principled nodes, always write
        if self.bjsNodeTree.roughness is not None or ROUGHNESS_TEX in self.textures:
            roughness = 1.0 if ROUGHNESS_TEX in self.textures else self.bjsNodeTree.roughness
        else:
            roughness = 0.2 # 0.2 is the Blender default for glossy Node

        value = roughness if self.isPBR else 128 - (roughness * 128)
        propName = 'roughness' if self.isPBR else 'specularPower'
        write_float(file_handler, propName, value)

        # sources diffuse, transparency & principled nodes
        alpha = self.bjsNodeTree.diffuseAlpha if self.bjsNodeTree.diffuseAlpha is not None else 1.0
        write_float(file_handler, 'alpha', alpha)

        # properties specific to PBR
        if self.isPBR:
            write_int(file_handler, 'transparencyMode', self.transparencyMode)
            write_float(file_handler, 'alphaCutOff', self.alphaCutOff)
            # source principle node
            if self.bjsNodeTree.metallic is not None or METAL_TEX in self.textures:
                write_float(file_handler, 'metallic', 1.0 if METAL_TEX in self.textures else self.bjsNodeTree.metallic)

            # source emissive node
            if self.bjsNodeTree.emissiveIntensity is not None:
                write_float(file_handler, 'emissiveIntensity', self.bjsNodeTree.emissiveIntensity)

            # source principled node
            if self.bjsNodeTree.subsurfaceTranslucencyIntensity is not None:
                file_handler.write(',"subSurface":{')
                write_bool(file_handler, 'isTranslucencyEnabled', True, True)
                write_bool(file_handler, '_isTranslucencyEnabled', True, False) # for BJS 4.0, delete eventually
                write_float(file_handler, 'translucencyIntensity', self.bjsNodeTree.subsurfaceTranslucencyIntensity)
                write_color(file_handler, 'tintColor', self.bjsNodeTree.subSurfaceTintColor)
                if self.bjsNodeTree.indexOfRefraction is not None:
                    write_float(file_handler, 'indexOfRefraction', self.bjsNodeTree.indexOfRefraction)
                file_handler.write('}')

            # source principled node
            if self.bjsNodeTree.anisotropicIntensity is not None:
                file_handler.write(',"anisotropy":{')
                write_bool(file_handler, 'isEnabled', True, True)
                write_bool(file_handler, '_isEnabled', True, False) # for BJS 4.0, delete eventually
                write_float(file_handler, 'intensity', self.bjsNodeTree.anisotropicIntensity)
                file_handler.write('}')

            # source principled node (need to do this texture inside this section)
            if self.bjsNodeTree.sheenIntensity is not None or self.bjsNodeTree.sheenColor is not None or SHEEN_TEX in self.textures:
                file_handler.write(',"sheen":{')
                write_bool(file_handler, 'isEnabled', True, True)
                write_bool(file_handler, '_isEnabled', True, False) # for BJS 4.0, delete eventually

                if SHEEN_TEX in self.textures:
                    self.textures[SHEEN_TEX[0:-1]].to_json_file(file_handler) # all but last character
                else:
                    write_float(file_handler, 'intensity', self.bjsNodeTree.sheenIntensity)
                    write_color(file_handler, 'color', self.bjsNodeTree.sheenColor)

                file_handler.write('}')

            # source principled node (need to do this texture inside this section)
            if self.bjsNodeTree.clearCoatIntensity is not None or self.bjsNodeTree.clearCoatRoughness is not None or CLEARCOAT_TEX in self.textures:
                file_handler.write(',"clearCoat":{')
                write_bool(file_handler, 'isEnabled', True, True)
                write_bool(file_handler, '_isEnabled', True, False) # for BJS 4.0, delete eventually
                if self.bjsNodeTree.indexOfRefraction is not None:
                    write_float(file_handler, '_indiceOfRefraction', self.bjsNodeTree.indexOfRefraction) # for BJS 4.0, delete eventually
                    write_float(file_handler, 'indexOfRefraction', self.bjsNodeTree.indexOfRefraction)

                if CLEARCOAT_TEX in self.textures:
                    self.textures[CLEARCOAT_TEX[0:-1]].to_json_file(file_handler) # all but last character
                else:
                    write_float(file_handler, 'intensity', self.bjsNodeTree.clearCoatIntensity)
                    write_float(file_handler, 'roughness', self.bjsNodeTree.clearCoatRoughness)

                if CLEARCOAT_BUMP_TEX in self.textures:
                    self.textures[CLEARCOAT_BUMP_TEX].to_json_file(file_handler)

                file_handler.write('}')

        # properties specific to STD
        else:
            # sources refraction & principled nodes
            if self.bjsNodeTree.indexOfRefraction is not None and REFRACTION_TEX not in self.textures:
                write_float(file_handler, 'indexOfRefraction', 1 / self.bjsNodeTree.indexOfRefraction)

        # ---- add textures ----

        # sources diffuse & principled nodes
        if DIFFUSE_TEX in self.textures:
            tex = self.textures[DIFFUSE_TEX]
            texType = ALBEDO_TEX if self.isPBR else DIFFUSE_TEX
            self.textures[DIFFUSE_TEX].textureType = texType
            tex.to_json_file(file_handler)

            if self.isPBR:
                write_bool(file_handler, 'useAlphaFromAlbedoTexture', tex.hasAlpha)

        # source ambientOcclusion node
        if AMBIENT_TEX in self.textures and not self.isPBR:
            self.textures[AMBIENT_TEX].to_json_file(file_handler)

        # source transparency node
        if OPACITY_TEX in self.textures:
            self.textures[OPACITY_TEX].to_json_file(file_handler)

        # source emissive node
        if EMMISIVE_TEX in self.textures:
            self.textures[EMMISIVE_TEX].to_json_file(file_handler)

        # sources glossy & principled nodes
        if SPECULAR_TEX in self.textures:
            texType = REFLECTION_TEX if self.isPBR else SPECULAR_TEX
            self.textures[SPECULAR_TEX].textureType = texType
            self.textures[SPECULAR_TEX].to_json_file(file_handler)

        # sources normal_map & principled nodes
        if BUMP_TEX in self.textures:
            self.textures[BUMP_TEX].to_json_file(file_handler)

        # sources refraction & principled nodes
        if REFRACTION_TEX in self.textures:
            self.textures[REFRACTION_TEX].to_json_file(file_handler)

        if self.isPBR:
            if METAL_TEX in self.textures or ROUGHNESS_TEX in self.textures or AMBIENT_TEX in self.textures:
                # there is really only ever one texture, but could be in dictionary in multiple places
                if METAL_TEX in self.textures: # source principled node
                    self.textures[METAL_TEX].to_json_file(file_handler)
                elif ROUGHNESS_TEX in self.textures: # source principled node
                    self.textures[ROUGHNESS_TEX].textureType = METAL_TEX
                    self.textures[ROUGHNESS_TEX].to_json_file(file_handler)
                elif AMBIENT_TEX in self.textures: # source ambientOcclusion node
                    self.textures[AMBIENT_TEX].textureType = METAL_TEX
                    self.textures[AMBIENT_TEX].to_json_file(file_handler)

                write_bool(file_handler, 'useMetallnessFromMetallicTextureBlue', METAL_TEX in self.textures)
                write_bool(file_handler, 'useRoughnessFromMetallicTextureGreen', ROUGHNESS_TEX in self.textures)
                write_bool(file_handler, 'useAmbientOcclusionFromMetallicTextureRed', AMBIENT_TEX in self.textures)

        else:
            if METAL_TEX in self.textures or ROUGHNESS_TEX in self.textures:
                Logger.warn('Metal / roughness texture detected, but no meaning outside of PBR, ignored', 3)
        file_handler.write('}')
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    @staticmethod
    def meshBakingClean(mesh):
        for uvMap in mesh.data.uv_layers:
            if uvMap.name == 'BakingUV':
                mesh.data.uv_layers.remove(uvMap)
                break

        # remove an image if it was baked
        for image in bpy.data.images:
            if image.name == mesh.name + '_BJS_BAKE':
                image.user_clear() # cannot remove image unless 0 references
                bpy.data.images.remove(image)
                break
#===============================================================================
bpy.types.Material.backFaceCulling = bpy.props.BoolProperty(
    name='Back Face Culling',
    description='When checked, the faces on the inside of the mesh will not be drawn.',
    default = True
)
bpy.types.Material.checkReadyOnlyOnce = bpy.props.BoolProperty(
    name='Check Ready Only Once',
    description='When checked better CPU utilization.  Advanced user option.',
    default = False
)
bpy.types.Material.maxSimultaneousLights = bpy.props.IntProperty(
    name='Max Simultaneous Lights',
    description='BJS property set on each material.\nSet higher for more complex lighting.\nSet lower for armatures on mobile',
    default = 4, min = 0, max = 32
)
bpy.types.Material.transparencyMode = bpy.props.EnumProperty(
    name='Mode',
    description='How the alpha of this material is to be handled.  No meaning unless exporting PBR materials.',
    items = ((PBRMATERIAL_OPAQUE           , 'Opaque'            , 'Alpha channel is not used.'),
             (PBRMATERIAL_ALPHATEST        , 'Alpha Test'        , 'Pixels are discarded below a certain threshold defined by the alpha cutoff value.'),
             (PBRMATERIAL_ALPHABLEND       , 'Alpha Blend'       , 'Pixels are blended (according to the alpha mode) with\n the already drawn pixels in the current frame buffer.'),
             (PBRMATERIAL_ALPHATESTANDBLEND, 'Alpha Test & Blend', 'Pixels are blended after being higher than the cutoff threshold.')
            ),
    default = PBRMATERIAL_OPAQUE
)
bpy.types.Material.alphaCutOff = bpy.props.FloatProperty(
    name='Alpha Cutoff',
    description='The threshold used for Alpha Test and Alpha Test & Blend transparency modes .\nNo meaning unless exporting PBR materials.',
    default = 0.4, min = 0, max = 1.0
)
bpy.types.Material.intensityOverride = bpy.props.BoolProperty(
    name='Override World',
    description='When checked, use the intensity here, instead of the one in World.',
    default = False
)
bpy.types.Material.environmentIntensity = bpy.props.FloatProperty(
    name='Env. Intensity',
    description='This is the intensity of the environment to be applied to this material.\nNo meaning unless exporting PBR materials.',
    default = 1.0, min = 0, max = 1.0
)
#===============================================================================
class BJS_PT_MaterialsPanel(bpy.types.Panel):
    bl_label = get_title()
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'material'

    def draw(self, context):
        layout = self.layout

        mesh = context.object
        index = mesh.active_material_index

        if  len(mesh.material_slots) >= 1:
            material = mesh.material_slots[index].material
            if material:
                layout.prop(material, 'backFaceCulling')
                layout.prop(material, 'checkReadyOnlyOnce')
                layout.prop(material, 'maxSimultaneousLights')

                box = layout.box()
                box.label(text='PBR Transparency:')
                box.prop(material, 'transparencyMode')
                row = box.row()
                row.enabled = material.transparencyMode == PBRMATERIAL_ALPHATEST or material.transparencyMode == PBRMATERIAL_ALPHATESTANDBLEND
                row.prop(material, 'alphaCutOff')

                box = layout.box()
                box.label(text='PBR Environment Intensity:')
                box.prop(material, 'intensityOverride')
                row = box.row()
                row.enabled = material.intensityOverride
                row.prop(material, 'environmentIntensity')