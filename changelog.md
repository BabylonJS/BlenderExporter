# Blender2Babylon add-on changelog

## Blender 2.93.4 ##
* 17 August 2022

* Added check box to Export Dialog box to only export the current selection.  Stated use case is to export objects in individual files via script. From @ghempton.

## Blender 2.93.3 ##
* 23 July 2022

* When converting a local matrix into a rotation, change the order from 'XYZ' to 'YXZ'

## Blender 2.93.2 ##
* 14 July 2022

* Fixed exception when there are shapekeys, but no animation

## Blender 2.93.1 ##
* 14 June 2022

* Fixed a typo in Diffuse Node
* Problem baking without a UV


## Blender 2.93.0 ##
* 31 May 2022

* Changes for API changes in Blender 2.93
* Shape Key animation added
* Switched the default of pickable to False for meshes
* For Shadows, added Cascaded type, autoZBounds & min & max

* For Materials:
    * Allow for having a value for Albedo / diffuse or emission when there is also a texture for same
    * The emission color is never defaulted on nor explicitly black, when there is an emissive texture
    * Added a custom overload property, where a color AND a texture can be specified for Albedo & emissive with the same fields
    * Added custom properties of 2 Sided lighting, disable lights, invert X or Y normals, & Object Space Normal mapping
    * Support for Parallax and it's scale bias, & occlusion
    * Added PBR specific custom properties for Horizon Occlusion, Radiance Occlusion, Irradiance In Fragment, Radiance Over Alpha, Normals Forward, & Specular Anti-Aliasing
    * Added custom property to allow mixing STD materials in a PBR export via a STD material override
    * Discontinued Check Only Once custom property

## Blender 2.80.1 ##
* 18 January 2021

Preserving of vertex groups by https://github.com/mvanacker, see PR https://github.com/BabylonJS/BlenderExporter/pull/44.

## Blender 2.80.0 ##
* 29 December 2020

Renaming of Blender build zip to now be in `Blender2Babylon-2.80x` format, where the
version of Blender it was made for is now in the name.  This is the exact same
as version 6.46 for the current file.  The deprecated files are renamed as follows:

- `Blender2Babylon-5.6` is now `Blender2Babylon-2.79x`
- `io_export_babylon.py` is now `Blender2Babylon-2.75x`

## Blender 6.4.6 ##
* 08 December 2020

* Increase maximum # of decimals of precision to 8.

## Blender 6.4.5 ##
* 10 October 2020

* Fix Problem in Armature introduced in 6.4.2

## Blender 6.4.4 ##
* 08 September 2020

* Allow exported Arcrotate camera to be panned (Right click / drag).

## Blender 6.4.3 ##
* 08 July 2020

* Fixed exporting of the Blender HDR texture being used as the enviromnent.

## Blender 6.4.2 ##
* 02 July 2020

* The original animation assigned to an armature is return once animation has completed, by https://github.com/ghempton, see PR https://github.com/BabylonJS/BlenderExporter/pull/25.

## Blender 6.4.1 ##
* 09 June 2020

* Changed with how Blender 2.83.0 now reports versions.  Exporter now works both ways.

## Blender 6.4.0 ##
* 01 June 2020

* Fixed exception when an empty material slot, just ignored now.
* Fixed non-sharing of materials when part of a multi-material.
* Added optional .csv file for mesh exporting statistics (turned on in World properties).
* Changed logging of the # of indexes to the more meaningful # of triangle exported.

## Blender 6.3.1 ##
* 11 March 2020

* Fixed 'This collection Only' option for lights, when empties are also in the scene.

## Blender 6.3.0 ##
* 10 February 2020

* Add the option 'preserve Z-up and right-handed' in the world tab.

## Blender 6.2.4 ##
* 05 January 2020

* Fixed material when not using Nodes
* Changed how Location, Rotation, & Scale are implemented for Blender 2.81.  Inputs can now be other nodes.  Still works for Blender 2.80, but the as other inputs part.

## Blender 6.2.1 ##
* 24 September 2019

* added direction onto tangents when doing split normals
* changed only exporting currently assigned animation to be the default
* fixed Glossy node from erroring when an unsupported node is assigned as input to Roughness

## Blender Exporter 6.2.0 ##
* 21 July 2019

* bug fix for meshes with armatures
* added lights for specific collections
* added pbr transparency mode & alpha cut off
* (florianfelix) removed deprecated messages from console

## Blender Exporter Version 6.1.1
* 12 May 2019

* Support for exporting to either BJS 4.0 or 4.1 regarding names of properties, which changed names
* Make PBR materials the default

## Blender Exporter Version 6.1.0
* 11 May 2019
* Added support for Subsurface, Anisotropic, Clear Coat, & sheen from Principled node for PBR
* Added tangents when also using custom split normals
* Added several generic .env files for when PBR is output
* Made changes reflecting the final API for Blender 2.80

## Blender Exporter Version 6.0.0
*24 January 2019

* Supports Blender 2.80 redesign
* Removed Internal render materials support
* Relocated Game Engine render properties used
* Moved all exporter level custom properties from scene tab to world tab
* Changes to world tab:
	* Added properties from scene tab
	* Added Sky Box / Environment Textures section
	* Added `Use PBR` checkbox
* Changes to mesh tab / proccesing:
	* Relocated Billboard Mode from Game Engine to here
	* Relocated most of material section to new panel in Materials tab
	* Remaining materials stuff now in 'Baking Settings' section.  Added `Force Baking` checkbox to avoid multi-materials.
    * Blender's mixed flat / smooth shading now supported, or custom split normals if used.
    * Custom properties `Picking` & `Disabled` are now using Outliner Icons instead.
    * Alpha now supported in vertex colors
* Changes for lights tab / proccessing:
    * Added `PBR intensity mode` custom property.  When `Automatic` or not PBR, `intensity` scaled 0-1 from Blender's `Energy`, where 10 is 1.  Otherwise `Energy` passed, unmodified.
    * `Range` property now supported using Blender property `Radius`
    * Hemi light type is no longer supported.  To get a BJS hemi light use area type, & specify `Size X` for `range`.
* Added new custom properties panel for Materials:
	* Relocated `Back Face Culling` checkbox from Game Engine to here
	* Relocated `Check Ready Only` Once checkbox from Mesh tab to here
	* Relocated `Max Simultaneous Lights` from Mesh tab to here
	* Relocated Name Space from Mesh tab to here (might be in TOB only, since JSON files cannot share materials)
* Mesh baking can be reduced to only the texture channels required, keeping other image texture based channels (not for multi-material meshes)
* Nodes based renders (Cycles & eevee) not always just baked.  See chart for properties / textures & where values are from.  Properties are only assigned when no texture input to socket.

|  STD Property / Tex | PBR Property / Tex | From Nodes-Socket
| --- | --- | --- |
| diffuseColor / diffuseTexture | albedoColor / albedoTexture |Diffuse BSDF - Color, Principled BSDF - Base Color |
| ambientColor / ambientTexture | ambientColor / useAmbientOcclusionFromMetallicTextureRed  | Ambient Occlusion - Color |
| emissiveColor / emissiveTexture | emissiveColor / emissiveTexture | Emission - Color |
| specularColor / specularTexture | reflectivityColor / reflectivityTexture | Glossy BSDF - Color, Principled BSDF - Specular |
| specularPower (inverted & 0 - 128) | roughness / useRoughnessFromMetallicTextureGreen | Glossy BSDF - Roughness, Principled BSDF - Roughness |
| indexOfRefraction / refractionTexture | indexOfRefraction / refractionTexture | Refraction BSDF - IOR, Frensel - IOR, Principled BSDF - IOR / Refraction BSDF - Color, Principled BSDF - IOR|
| -- | metallic / metallicTexture | Principled - Specular |
| -- | emissiveIntensity | Emission - Strength|
| alpha / opacityTexture | alpha / opacityTexture |Diffuse BSDF - Color, Transparency BSDF - Color, Principled BSDF - Base Color |
| bumpTexture | bumpTexture | Normal Map - Color, Principled BSDF - Normal |

* Certain nodes are allowed, and are either ignored or just passed thru
	* Mix Shader, used mostly for non-principled trees
	* Separate RGB, for metallic textures wt roughness / AO
	* Frensel, when not PBR
* glTF legacy nodes (glTF Metallic Roughness or glTF Specular Glossiness) produce an error saying to switch to standard Blender nodes or use glTF exporter
* Texture / UV parameters are optional Nodes, when input to a texture node (ignored when must be baked, baking uses them though)
	* Mapping node for (translation to offset), (rotation to ang), (scale to scale)
	* Texture Coordinate & UVMap nodes for coordinatesIndex
* When a material channel cannot really be represented by mapping, then it will be baked.  Examples:
	* A Noise or other procedureal texture to Principled BSDF - Normal, then a bump texture will be baked
	* Any node which is not explicitly supported or ignored

## Blender Exporter Version 5.6.4

*17 July 2018

* Fix typo for exporting only visible layers

* Copy tags also to instances

## Blender Exporter Version 5.6.3

*01 June 2018

* Fix exporter settings panel (in Properties > Scene tab)

* Remove active layers export, replace with 3 options (All, Selected objects, and visible Layers)

* Show message in exporter settings panel to redirect user to Scene tab

* Fix bl_idname to allow setting of a shortcut

## Blender Exporter Version 5.6.2

*23 March 2018

The custom property, textureDir, originally for [Tower of Babel](https://github.com/BabylonJS/Extensions/tree/master/QueuedInterpolation/Blender) to
indicate the directory to write images, is now joined into the name
field of the texture in the *.babylon* file.

If the field does not end with `/`, then one will be added between the
directory & file name.

The field is relative to the *.babylon* file.  For this to work probably
implies that the *.babylon* is in the same directory as the html file.
Still it now allows images to be in a separate directory.

Have not tested where the the *.babylon* is in a different directory from
html file.

## Blender Exporter Version 5.6.1

*07 March 2018

- zip file now has manifest option code

## Blender Exporter Version 5.6

*02 March 2018

Essentially, this is an obsolete feature dump.  This in preparation for Blender 2.80 which could cause many changes.  Things removed:
-  Remove the checking for, and splitting up of meshes with more than 64k vertices.
-  Flat shading both for the mesh and the entire scene.  This can be replaced with a Split Edges modifier.
-  Generate ES6 instead of ES3 (Tower of Babel variant).

There were a few additions:
-  Separate scene level controls for the # of decimals of (Default):
    - positions / shape keys (4)
    - normals (3)
    - UVS (3)
    - vertex colors (3)
    - matrix weights (2)
-  Pickable property for meshes
-  Redesign of checking for un-applied transforms on meshes with armatures

Due to arguments changes to some functions, you will need to restart Blender if you had a prior version.
