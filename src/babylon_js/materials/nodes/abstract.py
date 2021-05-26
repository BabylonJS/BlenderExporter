# not importing subclasses at the module level, to avoid abstract importing them & they importing abstract
# done as needed in various methods
from babylon_js.logging import *

from mathutils import Color
# various texture types, value contains the BJS name when needed to be written in output
ENVIRON_TEX    = 'value not meaningful 1'

DIFFUSE_TEX    = 'diffuseTexture'
AMBIENT_TEX    = 'ambientTexture'
OPACITY_TEX    = 'opacityTexture'
EMMISIVE_TEX   = 'emissiveTexture'
SPECULAR_TEX   = 'specularTexture'
REFRACTION_TEX = 'refractionTexture'
BUMP_TEX       = 'bumpTexture'

# PBR specific textures
ALBEDO_TEX     = 'albedoTexture'       # PBR equivalent of a diffuse texture
METAL_TEX      = 'metallicTexture'
REFLECTION_TEX = 'reflectivityTexture' # PBR equivalent of a specular texture
ROUGHNESS_TEX  = 'value not meaningful 2'
SHEEN_TEX      = '_textureS'           # need 'S' to be unique in the bjsTextures dictionary, drop when writing
CLEARCOAT_TEX  = '_textureC'           # need 'C' to be unique in the bjsTextures dictionary, drop when writing
CLEARCOAT_BUMP_TEX = '_bumpTexture'

UV_ACTIVE_TEXTURE = 'value not meaningful 3'

DEF_DIFFUSE_COLOR = Color((.8, .8, .8))
#===============================================================================
class AbstractBJSNode:

    def __init__(self, bpyNode, socketName, overloadChannels = False):
        self.socketName = socketName
        self.bpyType = bpyNode.bl_idname

        isTopLevel = socketName == 'ShaderNodeOutputWorld' or socketName == 'ShaderNodeOutputLamp' or socketName == 'ShaderNodeOutputMaterial'

        # scalar bubbled up channel values for Std Material
        self.diffuseColor  = None  # same as albedoColor
        self.diffuseAlpha = None
        self.ambientColor  = None
        self.emissiveColor = None
        self.emissiveIntensity = None
        self.specularColor = None
        self.roughness = None

        # scalar bubbled up channel values for Pbr Material
        self.metallic = None
        self.indexOfRefraction = None
        self.subsurfaceTranslucencyIntensity = None
        self.subSurfaceTintColor = None
        self.anisotropicIntensity = None
        self.sheenIntensity = None
        self.sheenColor = None
        self.clearCoatIntensity = None
        self.clearCoatRoughness = None

        # intialize texture dictionary verses an array, since multiple channels can be output multiple times
        self.bjsTextures = {}
        self.unAssignedBjsTexture = None  # allow a texture to bubble up through a pass thru a node before being assigned
        self.uvMapName = None

        # baking broken out by channel, so channels which are fine just go as normal
        self.mustBake = False # whether baking ultimately going to be required
        self.mustBakeDiffuse    = False
        self.mustBakeAmbient    = False
        self.mustBakeOpacity    = False # not curently bakeable
        self.mustBakeEmissive   = False
        self.mustBakeSpecular   = False
        self.mustBakeNormal     = False
        self.mustBakeMetal      = False # not currently bakeable
        self.mustBakeRoughness  = False # not currently bakeable
        self.mustBakeSheen      = False # not currently bakeable
        self.mustBakeClearCoat  = False # not currently bakeable
        self.mustBakeRefraction = False # not currently bakeable

        # evaluate each of the inputs; either add the current / default value, linked Node, or None
        self.bjsSubNodes = {}
        self.defaults = {}
        for nodeSocket in bpyNode.inputs:
            # there are a maximum of 1 inputs per socket
            if len(nodeSocket.links) == 1:
                # recursive instancing of inputs with their matching wrapper sub-class
                bjsWrapperNode = AbstractBJSNode.GetBJSWrapperNode(nodeSocket.links[0].from_node, nodeSocket.name, overloadChannels)
                self.bubbleUp(bjsWrapperNode)
                self.bjsSubNodes[nodeSocket.name] = bjsWrapperNode
#                print ('found link for ' + nodeSocket.name + ' @ ' + str(nodeSocket.links[0]))
            else:
                self.bjsSubNodes[nodeSocket.name] = None

            if hasattr(nodeSocket, 'default_value'):
#                print('\t' + nodeSocket.name + ': ' + str(nodeSocket.default_value))
                self.defaults[nodeSocket.name] = nodeSocket.default_value
            else:
#                print('\t' + nodeSocket.name + ': no VALUE')
                self.defaults[nodeSocket.name] = None

            # when top level, ignore Volume & Displacement; if unsupported nodes, will bake un-necessarily
            if isTopLevel: break

        # End of super class constructor, sub-class constructor now runs.
        # Sub-class can expect all inputs to be already be loaded as wrappers, &
        # is responsible for setting all values & textures to be bubbled up.
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    def bubbleUp(self, bjsWrapperNode):
        self.mustBake |= bjsWrapperNode.mustBake
        self.mustBakeDiffuse    |= bjsWrapperNode.mustBakeDiffuse
        self.mustBakeAmbient    |= bjsWrapperNode.mustBakeAmbient
        self.mustBakeOpacity    |= bjsWrapperNode.mustBakeAmbient
        self.mustBakeEmissive   |= bjsWrapperNode.mustBakeEmissive
        self.mustBakeSpecular   |= bjsWrapperNode.mustBakeSpecular
        self.mustBakeNormal     |= bjsWrapperNode.mustBakeNormal
        self.mustBakeMetal      |= bjsWrapperNode.mustBakeMetal
        self.mustBakeRoughness  |= bjsWrapperNode.mustBakeRoughness
        self.mustBakeSheen      |= bjsWrapperNode.mustBakeSheen
        self.mustBakeClearCoat  |= bjsWrapperNode.mustBakeClearCoat
        self.mustBakeRefraction |= bjsWrapperNode.mustBakeRefraction

        # bubble up any scalars (defaults) which may have been set, allow multiples for principled.
        if bjsWrapperNode.diffuseColor is not None:
            self.diffuseColor = bjsWrapperNode.diffuseColor

        # diffuseAlpha broken out from color, since is can be provided by either the diffuse or transparency node
        if bjsWrapperNode.diffuseAlpha is not None:
            self.diffuseAlpha = bjsWrapperNode.diffuseAlpha

        if bjsWrapperNode.ambientColor is not None:
            self.ambientColor = bjsWrapperNode.ambientColor

        if bjsWrapperNode.emissiveColor is not None:
            self.emissiveColor = bjsWrapperNode.emissiveColor
            self.emissiveIntensity = bjsWrapperNode.emissiveIntensity

        if bjsWrapperNode.specularColor is not None:
            self.specularColor = bjsWrapperNode.specularColor

        if bjsWrapperNode.subsurfaceTranslucencyIntensity is not None:
            self.subsurfaceTranslucencyIntensity = bjsWrapperNode.subsurfaceTranslucencyIntensity

        if bjsWrapperNode.subSurfaceTintColor is not None:
            self.subSurfaceTintColor = bjsWrapperNode.subSurfaceTintColor

        if bjsWrapperNode.metallic is not None:
            self.metallic = bjsWrapperNode.metallic

        if bjsWrapperNode.roughness is not None:
            self.roughness = bjsWrapperNode.roughness

        if bjsWrapperNode.anisotropicIntensity is not None:
            self.anisotropicIntensity = bjsWrapperNode.anisotropicIntensity

        if bjsWrapperNode.sheenIntensity is not None:
            self.sheenIntensity = bjsWrapperNode.sheenIntensity

        if bjsWrapperNode.sheenColor is not None:
            self.sheenColor = bjsWrapperNode.sheenColor

        if bjsWrapperNode.clearCoatIntensity is not None:
            self.clearCoatIntensity = bjsWrapperNode.clearCoatIntensity

        if bjsWrapperNode.clearCoatRoughness is not None:
            self.clearCoatRoughness = bjsWrapperNode.clearCoatRoughness

        if bjsWrapperNode.indexOfRefraction is not None:
            self.indexOfRefraction = bjsWrapperNode.indexOfRefraction

        if bjsWrapperNode.unAssignedBjsTexture is not None:
            self.unAssignedBjsTexture = bjsWrapperNode.unAssignedBjsTexture

        if bjsWrapperNode.uvMapName is not None:
            self.uvMapName = bjsWrapperNode.uvMapName

        # bubble up any textures into the dictionary.
        # can assign over another, last wins, but they were probably duplicate.
        for texType, tex in bjsWrapperNode.bjsTextures.items():
            self.bjsTextures[texType] = tex
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
#     Methods called by BakingRecipe to figure out what to bake, if required
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    def usesDiffuseChannel(self):
        return self.diffuseColor is not None or DIFFUSE_TEX in self.bjsTextures

    def usesAmbientChannel(self):
        return self.ambientColor is not None or AMBIENT_TEX in self.bjsTextures

    def usesEmissiveChannel(self):
        return self.emissiveColor is not None or EMMISIVE_TEX in self.bjsTextures

    def usesSpecularChannel(self):
        return self.specularColor is not None or SPECULAR_TEX in self.bjsTextures

    def usesMetalChannel(self):
        return self.metallic is not None or METAL_TEX in self.bjsTextures

    def usesRoughnessChannel(self):
        return self.roughness is not None or ROUGHNESS_TEX in self.bjsTextures

    def usesSheenChannel(self):
        return self.sheenIntensity is not None or self.sheenColor or SHEEN_TEX in self.bjsTextures

    def usesClearCoatChannel(self):
        return self.clearCoatIntensity is not None or self.clearCoatRoughness is not None or CLEARCOAT_TEX in self.bjsTextures

    def usesRefractionChannel(self):
        return self.indexOfRefraction is not None or REFRACTION_TEX in self.bjsTextures

    def usesOpacityChannel(self):
        return OPACITY_TEX in self.bjsTextures

    def usesBumpChannel(self):
        return BUMP_TEX in self.bjsTextures

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
#     Methods for finding inputs to this node
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    def getDefault(self, socketName):
        return self.defaults[socketName]

    # leave out bpyType when value can either be a default value or another node
    def findInput(self, socketName, bpyTypeReqd = None):
        value = self.bjsSubNodes[socketName]
        if bpyTypeReqd is not None:
            if not hasattr(value, 'bpyType') or value.bpyType != bpyTypeReqd:
                return None
            
        if value is not None: return value
        return self.defaults[socketName]

    # called by many sub-classes, when just a color, return the default value to caller
    def findTexture(self, input, textureType):
        # looking for a Image Texture, Environment, or a Normal Map Node
        if isinstance(input, AbstractBJSNode):
            if input.unAssignedBjsTexture is not None:
                bjsImageTexture = input.unAssignedBjsTexture
                bjsImageTexture.assignChannel(textureType) # add channel directly to texture, so it also knows what type it is

                # add texture to nodes dictionary, for bubbling up which reduces multiples
                self.bjsTextures[textureType] = bjsImageTexture
                return None

            # when a link of an un-expected type was assigned, need to bake (probably bubbled up already)
            else:
                self.mustBake = True
                # unsupported types already logged warning, but not counting on some other thing, technically supported, but wrong not being there
                if not hasattr(input, 'loggedWarning'):
                    Logger.error('un-excepted node type(' + input.bpyType +').  Cannot continue.')
                return None

        # assign a color when no image texture node assigned
        else:
            return input

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    @staticmethod
    def readWorldNodeTree(node_tree):
        return AbstractBJSNode.readNodeTree(node_tree, 'ShaderNodeOutputWorld')

    @staticmethod
    def readLampNodeTree(node_tree):
        return AbstractBJSNode.readNodeTree(node_tree, 'ShaderNodeOutputLamp')

    @staticmethod
    def readMaterialNodeTree(node_tree, overloadChannels):
        return AbstractBJSNode.readNodeTree(node_tree, 'ShaderNodeOutputMaterial', overloadChannels)

    @staticmethod
    def readNodeTree(node_tree, topLevelId, overloadChannels = False):
        # https://blender.stackexchange.com/questions/30328/how-to-get-the-end-node-of-a-tree-in-python
        output = None
        for node in node_tree.nodes:
            if node.bl_idname == topLevelId and node.is_active_output:
                    output = node
                    break

        if output is None:
            for node in node_tree.nodes:
                if node.bl_idname == topLevelId:
                    output = node
                    break

        if output is None:
            return None

        return AbstractBJSNode(output, topLevelId, overloadChannels)
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    @staticmethod
    def GetBJSWrapperNode(bpyNode, socketName, overloadChannels):
        from .ambient_occlusion import AmbientOcclusionBJSNode
        from .background import BackgroundBJSNode
        from .diffuse import DiffuseBJSNode
        from .emission import EmissionBJSNode
        from .fresnel import FresnelBJSNode
        from .glossy import GlossyBJSNode
        from .mapping import MappingBJSNode
        from .normal_map import NormalMapBJSNode
        from .passthru import PassThruBJSNode
        from .principled import PrincipledBJSNode
        from .refraction import RefractionBJSNode
        from .tex_coord import TextureCoordBJSNode
        from .tex_environment import TextureEnvironmentBJSNode
        from .tex_image import TextureImageBJSNode
        from .transparency import TransparentBJSNode
        from .uv_map import UVMapBJSNode
        from .unsupported import UnsupportedNode

        if AmbientOcclusionBJSNode.bpyType == bpyNode.bl_idname:
            return AmbientOcclusionBJSNode(bpyNode, socketName, overloadChannels)

        elif BackgroundBJSNode.bpyType == bpyNode.bl_idname:
            return BackgroundBJSNode(bpyNode, socketName, overloadChannels)

        elif DiffuseBJSNode.bpyType == bpyNode.bl_idname:
            return DiffuseBJSNode(bpyNode, socketName, overloadChannels)

        elif EmissionBJSNode.bpyType == bpyNode.bl_idname:
            return EmissionBJSNode(bpyNode, socketName, overloadChannels)

        elif FresnelBJSNode.bpyType == bpyNode.bl_idname:
            return FresnelBJSNode(bpyNode, socketName, overloadChannels)

        elif GlossyBJSNode.bpyType == bpyNode.bl_idname:
            return GlossyBJSNode(bpyNode, socketName, overloadChannels)

        elif MappingBJSNode.bpyType == bpyNode.bl_idname:
            return MappingBJSNode(bpyNode, socketName, overloadChannels)

        elif NormalMapBJSNode.bpyType == bpyNode.bl_idname:
            return NormalMapBJSNode(bpyNode, socketName, overloadChannels)

        elif bpyNode.bl_idname in PassThruBJSNode.PASS_THRU_SHADERS:
            return PassThruBJSNode(bpyNode, socketName, overloadChannels)

        elif PrincipledBJSNode.bpyType == bpyNode.bl_idname:
            return PrincipledBJSNode(bpyNode, socketName, overloadChannels)

        elif RefractionBJSNode.bpyType == bpyNode.bl_idname:
            return RefractionBJSNode(bpyNode, socketName, overloadChannels)

        elif TextureCoordBJSNode.bpyType == bpyNode.bl_idname:
            return TextureCoordBJSNode(bpyNode, socketName, overloadChannels)

        elif TextureEnvironmentBJSNode.bpyType == bpyNode.bl_idname:
            return TextureEnvironmentBJSNode(bpyNode, socketName, overloadChannels)

        elif TextureImageBJSNode.bpyType == bpyNode.bl_idname:
            return TextureImageBJSNode(bpyNode, socketName, overloadChannels)

        elif TransparentBJSNode.bpyType == bpyNode.bl_idname:
            return TransparentBJSNode(bpyNode, socketName, overloadChannels)

        elif UVMapBJSNode.bpyType == bpyNode.bl_idname:
            return UVMapBJSNode(bpyNode, socketName, overloadChannels)

        else:
            return UnsupportedNode(bpyNode, socketName, overloadChannels)