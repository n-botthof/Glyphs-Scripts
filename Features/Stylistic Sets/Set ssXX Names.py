#MenuTitle: Set ssXX Names
# -*- coding: utf-8 -*-
from __future__ import division, print_function, unicode_literals
__doc__ = """
Prefills names for ssXX features with ‘Alternate’ or another chosen text, plus the name of the first substituted glyph, e.g., ‘Alternate a’.
"""

import vanilla

def featureHasName(feature):
	if Glyphs.versionNumber >= 3:
		# GLYPHS 3
		return bool(feature.labels)
	else:
		# GLYPHS 2
		return feature.notes and feature.notes.startswith("Name:")

def addNameToFeature(feature, featureName):
	if Glyphs.versionNumber >= 3:
		# GLYPHS 3
		featureLabel = GSFontInfoValue()
		featureLabel.languageTag = "dflt"
		featureLabel.value = featureName
		feature.labels = [featureLabel]
	else:
		# GLYPHS 2
		feature.notes = f"Name: {featureName}"
	
class SetSSXXNames(object):
	defaultName = "Alternate"
	prefID = "com.mekkablue.SetSSXXNames"
	prefDict = {
		# "prefName": defaultValue,
		"alternate": defaultName,
		"overwrite": 0,
	}

	def __init__(self):
		# Window 'self.w':
		windowWidth = 270
		windowHeight = 145
		windowWidthResize = 200 # user can resize width by this value
		windowHeightResize = 0 # user can resize height by this value
		self.w = vanilla.FloatingWindow(
			(windowWidth, windowHeight), # default window size
			"Set SSXX Names", # window title
			minSize = (windowWidth, windowHeight), # minimum size (for resizing)
			maxSize = (windowWidth + windowWidthResize, windowHeight + windowHeightResize), # maximum size (for resizing)
			autosaveName = self.domain("mainwindow") # stores last window position and size
		)

		# UI elements:
		linePos, inset, lineHeight = 12, 12, 22
		self.w.descriptionText = vanilla.TextBox(
			(inset, linePos + 2, -inset, 30), "Prefill human-readable names for Stylistic Set features ss01-ss20 with a default phrase:", sizeStyle='small', selectable=True
			)
		linePos += int(lineHeight * 1.8)

		self.w.alternateText = vanilla.TextBox((inset, linePos + 2, 85, 14), "Default Name:", sizeStyle='small', selectable=True)
		self.w.alternate = vanilla.EditText((inset + 85, linePos - 1, -inset - 25, 19), self.defaultName, callback=self.SavePreferences, sizeStyle='small')
		self.w.alternate.getNSTextField().setToolTip_(
			"The script will look for the first substituted glyph in every ssXX, e.g., ‘a’, and construct a Stylistic Set name with this Default Name plus the name of the first substituted glyph, e.g., ‘Alternate a’."
			)
		self.w.alternateUpdateButton = vanilla.SquareButton((-inset - 20, linePos, -inset, 18), "↺", sizeStyle='small', callback=self.SavePreferences)
		self.w.alternateUpdateButton.getNSButton().setToolTip_(f"Will reset default name to ‘{self.defaultName}’.")
		linePos += lineHeight

		self.w.overwrite = vanilla.CheckBox((inset, linePos - 1, -inset, 20), "Overwrite existing names", value=False, callback=self.SavePreferences, sizeStyle='small')
		self.w.overwrite.getNSButton(
		).setToolTip_("If set, will skip ssXX features that already have a ‘Name:’ entry in their feature notes. If unset, will reset all ssXX names.")
		linePos += lineHeight

		# Run Button:
		self.w.runButton = vanilla.Button((-120 - inset, -20 - inset, -inset, -inset), "Fill Names", sizeStyle='regular', callback=self.SetSSXXNamesMain)
		self.w.setDefaultButton(self.w.runButton)

		# Load Settings:
		if not self.LoadPreferences():
			print("Note: 'Set ssXX Names' could not load preferences. Will resort to defaults")

		# Open window and focus on it:
		self.w.open()
		self.w.makeKey()

	def domain(self, prefName):
		prefName = prefName.strip().strip(".")
		return self.prefID + "." + prefName.strip()
	
	def pref(self, prefName):
		prefDomain = self.domain(prefName)
		return Glyphs.defaults[prefDomain]
	
	def SavePreferences(self, sender=None):
		try:
			# reset name field:
			if sender == self.w.alternateUpdateButton:
				self.w.alternate.set(self.defaultName)
			
			# write current settings into prefs:
			for prefName in self.prefDict.keys():
				Glyphs.defaults[self.domain(prefName)] = getattr(self.w, prefName).get()
			return True
		except:
			import traceback
			print(traceback.format_exc())
			return False

	def LoadPreferences(self):
		try:
			for prefName in self.prefDict.keys():
				# register defaults:
				Glyphs.registerDefault(self.domain(prefName), self.prefDict[prefName])
				# load previously written prefs:
				getattr(self.w, prefName).set(self.pref(prefName))
			return True
		except:
			import traceback
			print(traceback.format_exc())
			return False

	def SetSSXXNamesMain(self, sender=None):
		try:
			# brings macro window to front and clears its log:
			Glyphs.clearLog()
			Glyphs.showMacroWindow()
			
			# update settings to the latest user input:
			if not self.SavePreferences(self):
				print("Note: 'Set ssXX Names' could not write preferences.")

			thisFont = Glyphs.font # frontmost font

			# query user settings:
			alternate = self.pref("alternate")
			overwrite = self.pref("overwrite")

			print(f"Setting ssXX Names for {thisFont.familyName}")
			if thisFont.filepath:
				print(thisFont.filepath)

			ssXXtags = tuple(f"ss{i+1:02}" for i in range(20))
			for thisFeature in thisFont.features:
				if thisFeature.name in ssXXtags:
					if overwrite or not featureHasName(thisFeature):
						codeLines = [l.strip() for l in thisFeature.code.strip().split(";") if " by " in l and not l.strip().startswith("#")]
						if codeLines:
							replacedLetter = codeLines[0].split("by")[0].split("sub")[1].strip()
							if replacedLetter:
								newName = f"{alternate} {replacedLetter}"
								print(f"  {thisFeature.name}: {newName}")
								addNameToFeature(thisFeature, newName)

			self.w.close() # delete if you want window to stay open
		except Exception as e:
			# brings macro window to front and reports error:
			Glyphs.showMacroWindow()
			print(f"Set ssXX Names Error: {e}")
			import traceback
			print(traceback.format_exc())

SetSSXXNames()
