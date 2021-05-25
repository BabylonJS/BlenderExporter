from .abstract import AbstractBJSNode

#===============================================================================
class PassThruBJSNode(AbstractBJSNode):
    PASS_THRU_SHADERS = 'ShaderNodeMixShader ShaderNodeSeparateRGB'

    def __init__(self, bpyNode, socketName, overloadChannels):
        super().__init__(bpyNode, socketName, overloadChannels)
