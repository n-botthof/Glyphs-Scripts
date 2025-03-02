#MenuTitle: Add Missing Brace Layers
# -*- coding: utf-8 -*-
from __future__ import division, print_function, unicode_literals
__doc__="""
Complete the rectangular setup necessary for OTVAR exports.
"""

from itertools import product
from copy import copy as copy

def addMissingHeightWidth(g):
	f = g.parent
	currentSpots = []
	layerDict = {}
	for l in g.layers:
		if l.attributes and l.attributes["coordinates"]:
			coords = l.attributes["coordinates"]
			key = l.associatedMasterId
			if key in layerDict.keys():
				layerDict[key].append(coords)
			else:
				layerDict[key] = [coords]
			if not coords in currentSpots:
				currentSpots.append(coords)
	for spot in currentSpots:
		for m in f.masters:
			mID = m.id
			if mID in layerDict.keys() and spot in layerDict[mID]:
				continue
			braceLayer = copy(g.layers[mID])
			braceLayer.attributes["coordinates"] = spot
			braceLayer.associatedMasterId = mID
			g.layers.append(braceLayer)
			
			print(f"🔤 {g.name}: added height={spot['hght']} width={spot['wdth']} for {m.name}")

def addMissingBraceLayers(g):
	f = g.parent
	currentSpots = []
	for l in g.layers:
		if l.isMasterLayer:
			currentSpots.append(tuple(l.master.axes))
		elif l.isSpecialLayer and l.attributes["coordinates"]:
			coords = dict(l.attributes["coordinates"])
			axisValues = tuple([float(coords[m.id]) for m in f.axes])
			currentSpots.append(axisValues)

	allCoordsPerAxis = []
	for i in range(len(f.axes)):
		axisList = []
		for spot in currentSpots:
			axisList.append(spot[i])
		allCoordsPerAxis.append(set(axisList))

	missingSpots = [l for l in product(*allCoordsPerAxis) if not l in currentSpots]
	for missingSpot in missingSpots:
		braceLayer = GSLayer()
		g.layers.append(braceLayer)
		axisIDs = [a.id for a in f.axes]
		braceLayer.attributes["coordinates"] = {}
		for axisID, axisValue in zip(axisIDs, missingSpot):
			braceLayer.attributes["coordinates"][axisID] = axisValue
		braceLayer.reinterpolate()
		print(f"🔤 {g.name}: added brace layer at {', '.join([str(int(s)) for s in missingSpot])}")

thisFont = Glyphs.font # frontmost font
selectedLayers = thisFont.selectedLayers # active layers of selected glyphs
Glyphs.clearLog() # clears log in Macro window

print("Adding missing brace layers...")
for i, axis in enumerate(thisFont.axes):
	print(f"Axis {i+1}: {axis.axisTag}, {axis.name}")
print()

thisFont.disableUpdateInterface() # suppresses UI updates in Font View
try:
	for thisLayer in selectedLayers:
		thisGlyph = thisLayer.parent
		thisGlyph.beginUndo() # begin undo grouping
		if thisGlyph.category == "Corner":
			addMissingHeightWidth(thisGlyph)
		else:
			addMissingBraceLayers(thisGlyph)
		print()
		thisGlyph.endUndo()   # end undo grouping
except Exception as e:
	Glyphs.showMacroWindow()
	print("\n⚠️ Error in script: Add Missing Brace Layers\n")
	import traceback
	print(traceback.format_exc())
	print()
	raise e
finally:
	print("Done.")
	thisFont.enableUpdateInterface() # re-enables UI updates in Font View
