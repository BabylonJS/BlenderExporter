from .abstract import AbstractBJSNode, ROUGHNESS_TEX, SPECULAR_TEX

from mathutils import Color

#===============================================================================
class GlossyBJSNode(AbstractBJSNode):
    bpyType = 'ShaderNodeBsdfGlossy'

    def __init__(self, bpyNode, socketName):
        super().__init__(bpyNode, socketName)

        input = self.findInput('Color')
        defaultColor = self.findTexture(input, SPECULAR_TEX)
        if defaultColor is not None:
            self.specularColor = Color((defaultColor[0], defaultColor[1], defaultColor[2]))
            
        self.mustBakeSpecular = input.mustBake if isinstance(input, AbstractBJSNode) else False
        # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
        input = self.findInput('Roughness')
        defaultRoughness = self.findTexture(input, ROUGHNESS_TEX)
        if defaultRoughness is not None:
            self.roughness = defaultRoughness

        self.mustBakeRoughness = input.mustBake if isinstance(input, AbstractBJSNode) else False
