from .abstract import *
from babylon_js.package_level import *

from mathutils import Color
DEFAULT_SURFACE_TINT = Color((0.7, 0.1, 0.1))

#===============================================================================
class PrincipledBJSNode(AbstractBJSNode):
    bpyType = 'ShaderNodeBsdfPrincipled'

    def __init__(self, bpyNode, socketName):
        super().__init__(bpyNode, socketName)

        input = self.findInput('Base Color')
        defaultDiffuse = self.findTexture(input, DIFFUSE_TEX)
        if defaultDiffuse is not None:
            self.diffuseColor = Color((defaultDiffuse[0], defaultDiffuse[1], defaultDiffuse[2]))
            self.diffuseAlpha = defaultDiffuse[3]

        self.mustBakeDiffuse = input.mustBake if isinstance(input, AbstractBJSNode) else False
        # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
        input = self.findInput('Subsurface')
        # ignoring texture surfaces & must be greater than 0
        if (not isinstance(input, AbstractBJSNode) and input > 0):
            input = self.findInput('Subsurface Color')
            # ignoring texture surfaces & must not be the default red to detect it is wanted
            if (not isinstance(input, AbstractBJSNode)):
                subSurface = Color((input[0], input[1], input[2]))
                if not same_color(subSurface, DEFAULT_SURFACE_TINT):
                    self.subSurfaceTintColor = subSurface
        # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
        input = self.findInput('Metallic')
        defaultMetallic = self.findTexture(input, METAL_TEX)
        if defaultMetallic is not None:
            self.metallic = defaultMetallic

        self.mustBakeMetal = input.mustBake if isinstance(input, AbstractBJSNode) else False
       # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
        input = self.findInput('Specular')
        defaultSpecular = self.findTexture(input, SPECULAR_TEX)
        if defaultSpecular is not None:
            self.specularColor = Color((defaultSpecular, defaultSpecular, defaultSpecular))

        self.mustBakeSpecular = input.mustBake if isinstance(input, AbstractBJSNode) else False
        # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
        input = self.findInput('Roughness')
        defaultRoughness = self.findTexture(input, ROUGHNESS_TEX)
        if defaultRoughness is not None:
            self.roughness = defaultRoughness

        self.mustBakeRoughness = input.mustBake if isinstance(input, AbstractBJSNode) else False
        # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
        input = self.findInput('Clearcoat')
        defaultClearCoatIntensity = self.findTexture(input, CLEARCOAT_TEX)
        self.mustBakeClearCoat = input.mustBake if isinstance(input, AbstractBJSNode) else False
        
        input = self.findInput('Clearcoat Roughness')
        defaultClearCoatRoughness = self.findTexture(input, CLEARCOAT_TEX)
        self.mustBakeClearCoat = input.mustBake if isinstance(input, AbstractBJSNode) else False
        
        # only want scalars, when no texture on either input & intensity > 0
        if CLEARCOAT_TEX not in self.bjsTextures and defaultClearCoatIntensity is not None and defaultClearCoatIntensity > 0:
            self.clearCoatIntensity = defaultClearCoatIntensity
            self.clearCoatRoughness = defaultClearCoatRoughness
        # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
        input = self.findInput('Sheen')
        defaultSheenIntensity = self.findTexture(input, SHEEN_TEX)
        self.mustBakeSheen = input.mustBake if isinstance(input, AbstractBJSNode) else False
        
        input = self.findInput('Sheen Tint')
        defaultSheenColor = self.findTexture(input, SHEEN_TEX)
        self.mustBakeSheen = input.mustBake if isinstance(input, AbstractBJSNode) else False
        
        # only want scalars, when no texture on either input & intensity > 0
        if SHEEN_TEX not in self.bjsTextures and defaultSheenIntensity is not None and defaultSheenIntensity > 0:
            self.sheenIntensity = defaultSheenIntensity
            self.sheenColor = Color((defaultSheenColor, defaultSheenColor, defaultSheenColor))
        # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
        input = self.findInput('Anisotropic')
        # ignoring texture surfaces & must be greater than 0
        if (not isinstance(input, AbstractBJSNode) and input > 0):
            self.anisotropicIntensity = input
        # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
        input = self.findInput('IOR')
        defaultIOR = self.findTexture(input, REFRACTION_TEX)
        if defaultIOR is not None:
            self.indexOfRefraction = defaultIOR

        self.mustBakeRefraction = input.mustBake if isinstance(input, AbstractBJSNode) else False
        # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
        input = self.findInput('Normal')
        self.findTexture(input, BUMP_TEX)
        self.mustBakeNormal = input.mustBake if isinstance(input, AbstractBJSNode) else False
        # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
        input = self.findInput('Clearcoat Normal')
        self.findTexture(input, CLEARCOAT_BUMP_TEX)
        self.mustBakeNormal = input.mustBake if isinstance(input, AbstractBJSNode) else False
