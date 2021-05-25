from .animation import *
from .logging import *
from .package_level import *

import bpy
#===============================================================================
# extract data in Mesh order; mapped into a copy of position
#
class RawShapeKey:
    def __init__(self, keyBlock, state, keyOrderMap, precision, currentAction, meshNameForAnim):
        self.state = state
        self.morphTargetId = meshNameForAnim + '-' + state
        self.precision = precision
        self.influence = keyBlock.value
        self.vertices = []

        retSz = len(keyOrderMap)
        for i in range(retSz):
            self.vertices.append(None)

        for i in range(retSz):
            pair = keyOrderMap[i]
            value = keyBlock.data[pair[0]].co
            self.vertices[pair[1]] = value

        Logger.log(state + ' added', 3)
        if currentAction is not None:
            self.processActions(keyBlock, currentAction)
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    def processActions(self, keyBlock, currentAction):
        currentActionOnly = bpy.context.scene.world.currentActionOnly
        self.animations = []
        for action in bpy.data.actions:

            if currentActionOnly and currentAction.name != action.name:
                continue

            if not self.partOfAction(action) :
                continue

            frame_start = int(action.frame_range[0])
            frame_end   = int(action.frame_range[1])
            frames = range(frame_start, frame_end + 1) # range is not inclusive with 2nd arg

            previousInfluence = -1
            Logger.log('processing action ' + action.name, 4)
            animation = Animation(ANIMATIONTYPE_FLOAT, ANIMATIONLOOPMODE_CYCLE, action.name, 'influence')

            for idx in range(len(frames)):
                frame = frames[idx]
                bpy.context.scene.frame_set(frame)

                # always write the first frame
                if (format_f(previousInfluence) != format_f(keyBlock.value)):
                    animation.frames.append(frame)
                    animation.values.append(keyBlock.value)
                    previousInfluence = keyBlock.value

            self.animations.append(animation)

    def partOfAction(self, action):
        actionTest = 'key_blocks["' + self.state + '"].value'
        for fcurve in action.fcurves:
            if actionTest == fcurve.data_path: return True

        return False
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    def to_json_file(self, file_handler):
        file_handler.write('{\n')
        write_string(file_handler, 'name', self.state, True)
        write_string(file_handler, 'id', self.morphTargetId)
        write_int(file_handler, 'influence', self.influence)
        write_vector_array(file_handler, 'positions', self.vertices, self.precision)
        file_handler.write('}')
#===============================================================================
