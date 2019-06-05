import bpy

if "bpy" in locals():
    import imp
    if 'support' in locals():
        imp.reload(support)