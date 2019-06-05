import bpy

USE_BLENDER_FOR_ENV = 'use_blender'
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def getAddonEnvTexturePath():
    import os
    return os.path.dirname(os.path.realpath(__file__))

bpy.types.World.evtTexture = bpy.props.EnumProperty(
    name='Env Textures',
    description='Environment texture for PBR materials.  No meaning,\nexcept as a sybox, when exporting as STD materials.',
    items = (
             (USE_BLENDER_FOR_ENV         , 'Blender World Node or None', 'Use the file assigned to the Color input of Background node of world.\nNone when is not assigned'),
             ('studio_256.env'            , 'Studio, 256px / face'      , 'Soft Box & 2 Umbrellas for that photo studio look, lower detail'),
             ('studio_512.env'            , 'Studio, 512px / face'      , 'Soft Box & 2 Umbrellas for that photo studio look, higher detail'),
             ('lysGenerated_afternoon.env', 'Sunny Morning / Afternoon' , 'A simulated sunny day with the sun positioned for morning or afternoon'),
             ('lysGenerated_noon.env'     , 'Sunny at Noon'             , 'A simulated sunny day with the sun positioned for noon'),
             ('lysGenerated_sunset.env'   , 'Sunny SunRise / SunSet'    , 'A simulated sunny day with the sun positioned for sunrise or sunset'),
             ('environment.env'           , 'Urban Environment'         , 'Hollywood walk of fame, near Grauman''s Chinese Theatre'),
             ('flowerRoad_256.env'        , 'Flower Road'               , 'Road lined with flowers')
            ),
    default = USE_BLENDER_FOR_ENV
)