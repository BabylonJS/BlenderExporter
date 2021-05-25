from .abstract import AbstractBJSNode, ENVIRON_TEX

#===============================================================================
class BackgroundBJSNode(AbstractBJSNode):
    bpyType = 'ShaderNodeBackground'

    def __init__(self, bpyNode, socketName, overloadChannels):
        super().__init__(bpyNode, socketName, overloadChannels)

        input = self.findInput('Color')
        self.findTexture(input, ENVIRON_TEX)