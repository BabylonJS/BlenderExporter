from .abstract import AbstractBJSNode

#===============================================================================
class FresnelBJSNode(AbstractBJSNode):
    bpyType = 'ShaderNodeFresnel'

    def __init__(self, bpyNode, socketName, overloadChannels):
        super().__init__(bpyNode, socketName, overloadChannels)

        self.indexOfRefraction = self.findInput('IOR')