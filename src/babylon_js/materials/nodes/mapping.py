from .abstract import AbstractBJSNode

import bpy
#===============================================================================
class MappingBJSNode(AbstractBJSNode):
    bpyType = 'ShaderNodeMapping'

    def __init__(self, bpyNode, socketName, overloadChannels):
        super().__init__(bpyNode, socketName, overloadChannels)

        # in 2.81 section were changed to possible inputs
        if bpy.app.version < (2, 80, 1):
            self.offset = bpyNode.translation
            self.ang    = bpyNode.rotation
            self.scale  = bpyNode.scale
        else:
            self.offset = self.findInput('Location')
            self.ang    = self.findInput('Rotation')
            self.scale  = self.findInput('Scale')
