from .abstract  import AbstractBJSNode, EMMISIVE_TEX

from mathutils import Color

#===============================================================================
class EmissionBJSNode(AbstractBJSNode):
    bpyType = 'ShaderNodeEmission'

    def __init__(self, bpyNode, socketName, overloadChannels):
        super().__init__(bpyNode, socketName, overloadChannels)

        input = self.findInput('Color')
        defaultColor = self.findTexture(input, EMMISIVE_TEX)

        # when defaultColor is None, a texture was found;
        # get color when returned by findTexture, or also when overloading
        if defaultColor is not None or overloadChannels:
            defaultColor = self.getDefault('Color')
            self.emissiveColor = Color((defaultColor[0], defaultColor[1], defaultColor[2]))

        self.emissiveIntensity = self.findInput('Strength')
        self.mustBakeEmissive = input.mustBake if isinstance(input, AbstractBJSNode) else False
