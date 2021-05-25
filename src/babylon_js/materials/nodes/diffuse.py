from .abstract import AbstractBJSNode, DIFFUSE_TEX, DEF_DIFFUSE_COLOR
from babylon_js.package_level import same_color

from mathutils import Color

#===============================================================================
class DiffuseBJSNode(AbstractBJSNode):
    bpyType = 'ShaderNodeBsdfDiffuse'

    def __init__(self, bpyNode, socketName, overloadChannels):
        super().__init__(bpyNode, socketName, overloadChannels)

        input = self.findInput('Color')
        defaultColor = self.findTexture(input, DIFFUSE_TEX)
        
        # when defaultColor is None, a texture was found;
        # get color when returned by findTexture, or also when overloading
        if defaultColor is not None or overloadChannels:
            defaultColor = self.getDefault('Color')
            self.diffuseColor = Color((defaultColor[0], defaultColor[1], defaultColor[2]))
            self.diffuseAlpha = defaultDiffuse[3]

        self.mustBakeDiffuse = input.mustBake if isinstance(input, AbstractBJSNode) else False
