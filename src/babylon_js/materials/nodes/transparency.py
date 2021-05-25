from .abstract import AbstractBJSNode, OPACITY_TEX

#===============================================================================
class TransparentBJSNode(AbstractBJSNode):
    bpyType = 'ShaderNodeBsdfTransparent'

    def __init__(self, bpyNode, socketName, overloadChannels):
        super().__init__(bpyNode, socketName, overloadChannels)

        input = self.findInput('Color')
        defaultColor = self.findTexture(input, OPACITY_TEX)
        if defaultColor is not None:
            self.diffuseAlpha = defaultColor[3]

        self.mustBakeOpacity = input.mustBake if isinstance(input, AbstractBJSNode) else False