#MenuTitle: Vertical Metrics Manager
# -*- coding: utf-8 -*-
from __future__ import division, print_function, unicode_literals
try:
	from builtins import str
except Exception as e:
	print("Warning: 'future' module not installed. Run 'sudo pip install future' in Terminal.")
__doc__ = """
Manage and sync ascender, descender and linegap values for hhea, OS/2 sTypo and OS/2 usWin.
"""

import vanilla

def cleanInt(numberString):
	exportString = ""
	numberString = unicode(numberString)
	for char in numberString:
		if char in "1234567890+-":
			exportString += char
	floatNumber = float(exportString)
	floatNumber = round(floatNumber)
	return int(floatNumber)

def roundUpByValue(x, roundBy):
	if x == 0:
		# avoid division by zero
		return 0
	else:
		sign = x / abs(x) # +1 or -1
		factor = 0
		if x % roundBy:
			factor = 1
		return int((abs(x) // roundBy * roundBy + factor * roundBy) * sign)

class VerticalMetricsManager(object):
	prefID = "com.mekkablue.VerticalMetricsManager"
	prefDict = {
		# "prefName": defaultValue,
		"allOpenFonts": 0,
		"preferSelectedGlyphs": 0,
		"preferCategory": 0,
		"preferScript": 0,
		"ignoreNonExporting": 1,
		"includeAllMasters": 1,
		"respectMarkToBaseOffset": 0,
		"round": 1,
		"roundValue": 10,
		"useTypoMetrics": 1,
		"hheaGap": 0,
		"hheaDesc": 0,
		"hheaAsc": 0,
		"typoGap": 0,
		"typoDesc": 0,
		"typoAsc": 0,
		"winDesc": 0,
		"winAsc": 0,
	}

	def __init__(self):
		# Window 'self.w':
		windowWidth = 330
		windowHeight = 410
		windowWidthResize = 100 # user can resize width by this value
		windowHeightResize = 0 # user can resize height by this value
		self.w = vanilla.FloatingWindow(
			(windowWidth, windowHeight), # default window size
			"Vertical Metrics Manager", # window title
			minSize=(windowWidth, windowHeight), # minimum size (for resizing)
			maxSize=(windowWidth + windowWidthResize, windowHeight + windowHeightResize), # maximum size (for resizing)
			autosaveName="com.mekkablue.VerticalMetricsManager.mainwindow" # stores last window position and size
			)

		# UI elements:
		linePos, inset, lineHeight = 12, 15, 22

		self.w.descriptionText = vanilla.TextBox((inset, linePos + 2, -inset, 14), "Manage and sync hhea, typo and win values.", sizeStyle='small', selectable=True)
		linePos += lineHeight

		self.w.titleAscent = vanilla.TextBox((inset + 70, linePos + 4, 70, 14), "Ascender", sizeStyle='small', selectable=True)
		self.w.titleDescent = vanilla.TextBox((inset + 140, linePos + 4, 70, 14), "Descender", sizeStyle='small', selectable=True)
		self.w.titleLineGap = vanilla.TextBox((inset + 210, linePos + 4, 70, 14), "Line Gap", sizeStyle='small', selectable=True)
		linePos += lineHeight

		self.w.titleWin = vanilla.TextBox((inset, linePos + 3, 70, 14), "OS/2 usWin", sizeStyle='small', selectable=True)
		self.w.winAsc = vanilla.EditText((inset + 70, linePos, 65, 19), "", callback=self.SavePreferences, sizeStyle='small')
		self.w.winAsc.getNSTextField().setToolTip_("OS/2 usWinAscent. Should be the maximum height in your font. Expect clipping or rendering artefacts beyond this point.")
		self.w.winDesc = vanilla.EditText((inset + 140, linePos, 65, 19), "", callback=self.SavePreferences, sizeStyle='small')
		self.w.winDesc.getNSTextField().setToolTip_(
			"OS/2 usWinDescent (unsigned integer). Should be the maximum depth in your font, like the lowest descender you have. Expect clipping or rendering artefacts beyond this point."
			)
		self.w.winGap = vanilla.EditText((inset + 210, linePos, 65, 19), "", callback=None, sizeStyle='small', readOnly=True, placeholder="n/a")
		self.w.winGap.getNSTextField().setToolTip_("OS/2 usWinLineGap does not exist, hence greyed out here.")
		self.w.winUpdate = vanilla.SquareButton((inset + 280, linePos, 20, 19), "↺", sizeStyle='small', callback=self.update)
		self.w.winUpdate.getNSButton(
		).setToolTip_("Will recalculate the OS/2 usWin values in the fields to the left. Takes the measurement settings below into account, except for the Limit options.")
		linePos += lineHeight + 4

		self.w.parenTypo = vanilla.TextBox((inset - 12, linePos + 5, 15, 20), "┏", sizeStyle='small', selectable=False)
		self.w.titleTypo = vanilla.TextBox((inset, linePos + 3, 70, 14), "OS/2 sTypo", sizeStyle='small', selectable=True)
		self.w.typoAsc = vanilla.EditText((inset + 70, linePos, 65, 19), "", callback=self.SavePreferences, sizeStyle='small')
		self.w.typoAsc.getNSTextField().setToolTip_(
			"OS/2 sTypoAscender (positive value), should be the same as hheaAscender. Should be the maximum height of the glyphs relevant for horizontal text setting in your font, like the highest accented uppercase letter, typically Aring or Ohungarumlaut. Used for first baseline offset in DTP and office apps and together with the line gap value, also in browsers."
			)
		self.w.typoDesc = vanilla.EditText((inset + 140, linePos, 65, 19), "", callback=self.SavePreferences, sizeStyle='small')
		self.w.typoDesc.getNSTextField().setToolTip_(
			"OS/2 sTypoDescender (negative value), should be the same as hheaDescender. Should be the maximum depth of the glyphs relevant for horizontal text setting in your font, like the lowest descender or bottom accent, typically Gcommaccent, Ccedilla, or one of the lowercase descenders (gjpqy). Together with the line gap value, used for line distance calculation in office apps and browsers."
			)
		self.w.typoGap = vanilla.EditText((inset + 210, linePos, 65, 19), "", callback=self.SavePreferences, sizeStyle='small')
		self.w.typoGap.getNSTextField().setToolTip_(
			"OS/2 sTypoLineGap (positive value), should be the same as hheaLineGap. Should be either zero or a value for padding between lines that makes sense visually. Office apps insert this distance between the lines, browsers add half on top and half below each line, also for determining text object boundaries."
			)
		self.w.typoUpdate = vanilla.SquareButton((inset + 280, linePos, 20, 19), "↺", sizeStyle='small', callback=self.update)
		self.w.typoUpdate.getNSButton().setToolTip_("Will recalculate the OS/2 sTypo values in the fields to the left. Takes the measurement settings below into account.")
		linePos += lineHeight

		self.w.parenConnect = vanilla.TextBox((inset - 12, linePos - int(lineHeight / 2) + 4, 15, 20), "┃", sizeStyle='small', selectable=False)
		self.w.parenHhea = vanilla.TextBox((inset - 12, linePos + 3, 15, 20), "┗", sizeStyle='small', selectable=False)
		self.w.titleHhea = vanilla.TextBox((inset, linePos + 3, 70, 14), "hhea", sizeStyle='small', selectable=True)
		self.w.hheaAsc = vanilla.EditText((inset + 70, linePos, 65, 19), "", callback=self.SavePreferences, sizeStyle='small')
		self.w.hheaAsc.getNSTextField().setToolTip_(
			"hheaAscender (positive value), should be the same as OS/2 sTypoAscender. Should be the maximum height of the glyphs relevant for horizontal text setting in your font, like the highest accented uppercase letter, typically Aring or Ohungarumlaut. Used for first baseline offset in Mac office apps and together with the line gap value, also in Mac browsers."
			)
		self.w.hheaDesc = vanilla.EditText((inset + 140, linePos, 65, 19), "", callback=self.SavePreferences, sizeStyle='small')
		self.w.hheaDesc.getNSTextField().setToolTip_(
			"hheaDescender (negative value), should be the same as OS/2 sTypoDescender. Should be the maximum depth of the glyphs relevant for horizontal text setting in your font, like the lowest descender or bottom accent, typically Gcommaccent, Ccedilla, or one of the lowercase descenders (gjpqy). Together with the line gap value, used for line distance calculation in office apps and browsers."
			)
		self.w.hheaGap = vanilla.EditText((inset + 210, linePos, 65, 19), "", callback=self.SavePreferences, sizeStyle='small')
		self.w.hheaGap.getNSTextField().setToolTip_(
			"hheaLineGap (positive value), should be the same as OS/2 sTypoLineGap. Should be either zero or a value for padding between lines that makes sense visually. Mac office apps insert this distance between the lines, Mac browsers add half on top and half below each line, also for determining text object boundaries."
			)
		self.w.hheaUpdate = vanilla.SquareButton((inset + 280, linePos, 20, 19), "↺", sizeStyle='small', callback=self.update)
		self.w.hheaUpdate.getNSButton().setToolTip_("Will recalculate the hhea values in the fields to the left. Takes the measurement settings below into account.")
		linePos += lineHeight

		self.w.useTypoMetrics = vanilla.CheckBox(
			(inset + 70, linePos, -inset, 20), "Use Typo Metrics (fsSelection bit 7)", value=True, callback=self.SavePreferences, sizeStyle='small'
			)
		self.w.useTypoMetrics.getNSButton().setToolTip_(
			"Should ALWAYS BE ON. Only uncheck if you really know what you are doing. If unchecked, line behaviour will be not consistent between apps and browsers because some apps prefer win values to sTypo values for determining line distances."
			)
		self.w.useTypoMetricsUpdate = vanilla.SquareButton((inset + 280, linePos, 20, 19), "↺", sizeStyle='small', callback=self.update)
		self.w.useTypoMetricsUpdate.getNSButton().setToolTip_("Will reset the checkbox to the left to ON, because it should ALWAYS be on. Strongly recommended.")
		linePos += lineHeight * 1.5

		self.w.descriptionMeasurements = vanilla.TextBox((inset, linePos + 2, -inset, 14), "Taking Measurements (see tooltips for info):", sizeStyle='small', selectable=True)
		linePos += lineHeight

		self.w.round = vanilla.CheckBox((inset, linePos, 70, 20), "Round by:", value=True, callback=self.SavePreferences, sizeStyle='small')
		self.w.round.getNSButton().setToolTip_("Turn on if you want your values rounded. Recommended.")
		self.w.roundValue = vanilla.EditText((inset + 75, linePos, 60, 19), "10", callback=self.SavePreferences, sizeStyle='small')
		self.w.roundValue.getNSTextField().setToolTip_("All value calculations will be rounded up to the next multiple of this value. Recommended: 10.")
		linePos += lineHeight

		self.w.includeAllMasters = vanilla.CheckBox(
			(inset, linePos, -inset, 20), "Include all masters (otherwise current master only)", value=True, callback=self.SavePreferences, sizeStyle='small'
			)
		self.w.includeAllMasters.getNSButton().setToolTip_(
			"If checked, all masters will be measured. If unchecked, only the current master will be measured. Since vertical metrics should be the same throughout all masters, it also makes sense to measure on all masters."
			)
		linePos += lineHeight

		self.w.respectMarkToBaseOffset = vanilla.CheckBox(
			(inset, linePos, -inset, 20), "Include mark-to-base offset for OS/2 usWin", value=False, callback=self.SavePreferences, sizeStyle='small'
			)
		self.w.respectMarkToBaseOffset.getNSButton().setToolTip_(
			"If checked will calculate the maximum possible height that can be reached with top-anchored marks, and the lowest depth with bottom-anchored marks, and use those values for the OS/2 usWin values. Strongly recommended for making fonts work on Windows if they rely on mark-to-base positioning (e.g. Arabic). Respects the ‘Limit to Script’ setting."
			)
		linePos += lineHeight

		self.w.ignoreNonExporting = vanilla.CheckBox((inset, linePos, -inset, 20), "Ignore non-exporting glyphs", value=False, callback=self.SavePreferences, sizeStyle='small')
		self.w.ignoreNonExporting.getNSButton(
		).setToolTip_("If checked, glyphs that do not export will be excluded from measuring. Recommended. (Ignored for calculating the OS/2 usWin values.)")
		linePos += lineHeight

		self.w.preferSelectedGlyphs = vanilla.CheckBox((inset, linePos, -inset, 20), "Limit to selected glyphs", value=False, callback=self.SavePreferences, sizeStyle='small')
		self.w.preferSelectedGlyphs.getNSButton().setToolTip_(
			"If checked, only the current glyphs will be measured. Can be combined with the other Limit options. May make sense if you want your metrics to be e.g. Latin-CE-centric."
			)
		linePos += lineHeight

		self.w.preferScript = vanilla.CheckBox((inset, linePos, inset + 110, 20), "Limit to script:", value=False, callback=self.SavePreferences, sizeStyle='small')
		self.w.preferScript.getNSButton().setToolTip_(
			"If checked, only measures glyphs belonging to the selected writing system. Can be combined with the other Limit options. (Ignored for calculating the OS/2 usWin values, but respected for mark-to-base calculation.)"
			)
		self.w.preferScriptPopup = vanilla.PopUpButton((inset + 115, linePos + 1, -inset - 25, 17), ("latin", "greek"), sizeStyle='small', callback=self.SavePreferences)
		self.w.preferScriptPopup.getNSPopUpButton().setToolTip_(
			"Choose a writing system ('script') you want the measurements to be limited to. May make sense to ignore other scripts if the font is intended only for e.g. Cyrillic. Does not apply to OS/2 usWin"
			)
		self.w.preferScriptUpdate = vanilla.SquareButton((-inset - 20, linePos + 1, -inset, 18), "↺", sizeStyle='small', callback=self.update)
		self.w.preferScriptUpdate.getNSButton().setToolTip_("Update the script popup to the left with all scripts (writing systems) found in the current font.")
		linePos += lineHeight

		self.w.preferCategory = vanilla.CheckBox((inset, linePos, inset + 110, 20), "Limit to category:", value=False, callback=self.SavePreferences, sizeStyle='small')
		self.w.preferCategory.getNSButton().setToolTip_(
			"If checked, only measures glyphs belonging to the selected glyph category. Can be combined with the other Limit options. (Ignored for calculating the OS/2 usWin values.)"
			)
		self.w.preferCategoryPopup = vanilla.PopUpButton((inset + 115, linePos + 1, -inset - 25, 17), ("Letter", "Number"), sizeStyle='small', callback=self.SavePreferences)
		self.w.preferCategoryPopup.getNSPopUpButton().setToolTip_("Choose a glyph category you want the measurements to be limited to. It may make sense to limit only to Letter.")
		self.w.preferCategoryUpdate = vanilla.SquareButton((-inset - 20, linePos + 1, -inset, 18), "↺", sizeStyle='small', callback=self.update)
		self.w.preferCategoryUpdate.getNSButton().setToolTip_("Update the category popup to the left with all glyph categories found in the current font.")
		linePos += lineHeight

		self.w.allOpenFonts = vanilla.CheckBox(
			(inset, linePos - 1, -inset, 20), "⚠️ Read out and apply to ALL open fonts", value=False, callback=self.SavePreferences, sizeStyle='small'
			)
		self.w.allOpenFonts.getNSButton().setToolTip_(
			"If activated, does not only measure the frontmost font, but all open fonts. Careful: when you press the Apply button, will also apply it to all open fonts. Useful if you have all font files for a font family open."
			)
		linePos += lineHeight

		# Run Button:
		self.w.helpButton = vanilla.HelpButton((inset - 2, -20 - inset, 21, -inset + 2), callback=self.openURL)
		self.w.helpButton.getNSButton().setToolTip_("Opens the Vertical Metrics tutorial (highly recommended) in your web browser.")

		self.w.runButton = vanilla.Button((-120 - inset, -20 - inset, -inset, -inset), "Apply to Font", sizeStyle='regular', callback=self.VerticalMetricsManagerMain)
		self.w.runButton.getNSButton().setToolTip_(
			"Insert the OS/2, hhea and fsSelection values above as custom parameters in the font. The number values will be inserted into each master. Blank values will delete the respective parameters."
			)
		self.w.setDefaultButton(self.w.runButton)

		# Load Settings:
		if not self.LoadPreferences():
			print("Note: 'Vertical Metrics Manager' could not load preferences. Will resort to defaults")

		# Open window and focus on it:
		self.w.open()
		self.w.makeKey()

	def updateUI(self, sender=None):
		self.w.includeAllMasters.enable(not self.w.allOpenFonts.get())
		self.w.runButton.setTitle(f'Apply to Font{"s" if self.w.allOpenFonts.get() else ""}')
	
	def domain(self, prefName):
		prefName = prefName.strip().strip(".")
		return self.prefID + "." + prefName.strip()
	
	def pref(self, prefName):
		prefDomain = self.domain(prefName)
		return Glyphs.defaults[prefDomain]
	
	def SavePreferences(self, sender=None):
		try:
			# write current settings into prefs:
			for prefName in self.prefDict.keys():
				Glyphs.defaults[self.domain(prefName)] = getattr(self.w, prefName).get()
			self.updateUI()
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
			self.updateUI()
			return True
		except:
			import traceback
			print(traceback.format_exc())
			return False

	def openURL(self, sender):
		URL = None
		if sender == self.w.helpButton:
			URL = "https://glyphsapp.com/tutorials/vertical-metrics"
		if URL:
			import webbrowser
			webbrowser.open(URL)

	def update(self, sender=None):
		Glyphs.clearLog() # clears macro window log

		# update settings to the latest user input:
		if not self.SavePreferences(self):
			print("Note: 'Vertical Metrics Manager' could not write preferences.")

		frontmostFont = Glyphs.font
		allOpenFonts = self.pref("allOpenFonts")
		if allOpenFonts:
			theseFonts = Glyphs.fonts
		else:
			theseFonts = (frontmostFont, ) # iterable tuple of frontmost font only

		theseFamilyNames = [f.familyName for f in theseFonts]
		print("\nVertical Metrics Manager\nUpdating values for:\n")
		for i, thisFont in enumerate(theseFonts):
			print("%i. %s:" % (i + 1, thisFont.familyName))
			if thisFont.filepath:
				print(thisFont.filepath)
			else:
				print("⚠️ The font file has not been saved yet.")
			print()

		ignoreNonExporting = self.pref("ignoreNonExporting")
		includeAllMasters = self.pref("includeAllMasters")
		shouldRound = self.pref("round")
		roundValue = int(self.pref("roundValue"))
		respectMarkToBaseOffset = self.pref("respectMarkToBaseOffset")
		shouldLimitToScript = self.pref("preferScript")
		selectedScript = self.w.preferScriptPopup.getTitle()

		# win measurements:
		if sender == self.w.winUpdate:
			print("Determining OS/2 usWin values:\n")
			lowest, highest = 0.0, 0.0
			lowestGlyph, highestGlyph = None, None

			# respectMarkToBaseOffset:
			highestTopAnchor, lowestBottomAnchor = 0.0, 1.0
			highestTopAnchorGlyph, lowestBottomAnchorGlyph = None, None
			largestTopMark, largestBottomMark = 0.0, 0.0
			largestTopMarkGlyph, largestBottomMarkGlyph = None, None

			fontReport = ""
			for i, thisFont in enumerate(theseFonts):
				if allOpenFonts:
					fontReport = "%i. %s, " % (i + 1, thisFont.familyName)
				currentMaster = thisFont.selectedFontMaster
				for thisGlyph in thisFont.glyphs:
					if thisGlyph.export or not ignoreNonExporting:
						scriptCheckOK = not shouldLimitToScript or thisGlyph.script == selectedScript # needed for respectMarkToBaseOffset

						for thisLayer in thisGlyph.layers:
							belongsToCurrentMaster = thisLayer.associatedFontMaster() == currentMaster
							if belongsToCurrentMaster or includeAllMasters or allOpenFonts:
								if thisLayer.isSpecialLayer or thisLayer.isMasterLayer:
									lowestPointInLayer = thisLayer.bounds.origin.y
									highestPointInLayer = lowestPointInLayer + thisLayer.bounds.size.height
									if lowestPointInLayer < lowest:
										lowest = lowestPointInLayer
										lowestGlyph = f"{fontReport}{thisGlyph.name}, layer: {thisLayer.name}"
									if highestPointInLayer > highest:
										highest = highestPointInLayer
										highestGlyph = f"{fontReport}{thisGlyph.name}, layer: {thisLayer.name}"

									# respectMarkToBaseOffset:
									if respectMarkToBaseOffset and scriptCheckOK:
										allAnchors = thisLayer.anchorsTraversingComponents()
										if allAnchors:
											if thisGlyph.category == "Mark":
												topAnchors = [a for a in allAnchors if a.name == "_top"]
												if topAnchors:
													topAnchor = topAnchors[0]
													topSpan = highestPointInLayer - topAnchor.y
													if topSpan > largestTopMark:
														largestTopMark = topSpan
														largestTopMarkGlyph = f"{fontReport}{thisGlyph.name}, layer: {thisLayer.name}"
												bottomAnchors = [a for a in allAnchors if a.name == "_bottom"]
												if bottomAnchors:
													bottomAnchor = bottomAnchors[0]
													bottomSpan = abs(lowestPointInLayer - bottomAnchor.y)
													if bottomSpan > largestBottomMark:
														largestBottomMark = bottomSpan
														largestBottomMarkGlyph = f"{fontReport}{thisGlyph.name}, layer: {thisLayer.name}"
											else:
												topAnchors = [a for a in allAnchors if a.name == "top"]
												if topAnchors:
													topAnchor = topAnchors[0]
													if topAnchor.y > highestTopAnchor:
														highestTopAnchor = topAnchor.y
														highestTopAnchorGlyph = f"{fontReport}{thisGlyph.name}, layer: {thisLayer.name}"
												bottomAnchors = [a for a in allAnchors if a.name == "bottom"]
												if bottomAnchors:
													bottomAnchor = bottomAnchors[0]
													if bottomAnchor.y < lowestBottomAnchor:
														lowestBottomAnchor = bottomAnchor.y
														lowestBottomAnchorGlyph = f"{fontReport}{thisGlyph.name}, layer: {thisLayer.name}"
										

			print("Highest relevant glyph:")
			print(f"- {highestGlyph} (highest)")
			print()
			print("Lowest relevant glyph:")
			print(f"- {lowestGlyph} (lowest)")
			print()

			if respectMarkToBaseOffset:
				highestMarkToBase = highestTopAnchor + largestTopMark
				lowestMarkToBase = lowestBottomAnchor - largestBottomMark

				print("Highest top anchor:")
				print(f"- {highestTopAnchorGlyph} ({highestTopAnchor})")
				print("Largest top mark span (_top to top edge):")
				print(f"- {largestTopMarkGlyph} ({largestTopMark})")
				print(f"Highest possible mark-to-base: {highestTopAnchor} + {largestTopMark} = {highestMarkToBase}")
				print()
				print("Lowest bottom anchor:")
				print(f"- {lowestBottomAnchorGlyph} ({lowestBottomAnchor})")
				print("Largest bottom mark span (_bottom to bottom edge):")
				print(f"- {largestBottomMarkGlyph} ({largestBottomMark})")
				print(f"Lowest possible mark-to-base: {lowestBottomAnchor} - {largestBottomMark} = {lowestMarkToBase}")
				print()

				if lowestMarkToBase < lowest:
					lowest = lowestMarkToBase
				if highestMarkToBase > highest:
					highest = highestMarkToBase

			if shouldRound:
				highest = roundUpByValue(highest, roundValue)
				lowest = roundUpByValue(lowest, roundValue)

			winAsc = int(highest)
			winDesc = abs(int(lowest))

			print("Calculated values:")
			print("- usWinAscent: %s" % winAsc)
			print("- usWinDescent: %s" % winDesc)
			print()

			Glyphs.defaults["com.mekkablue.VerticalMetricsManager.winAsc"] = winAsc
			Glyphs.defaults["com.mekkablue.VerticalMetricsManager.winDesc"] = winDesc

		# Use Typo Metrics checkbox
		elif sender == self.w.useTypoMetricsUpdate:
			print("Use Typo Metrics (fsSelection bit 7) should always be YES.")
			Glyphs.defaults["com.mekkablue.VerticalMetricsManager.useTypoMetrics"] = 1

		# hhea and typo popups:
		elif sender in (self.w.hheaUpdate, self.w.typoUpdate):
			if sender == self.w.hheaUpdate:
				name = "hhea"
			else:
				name = "OS/2 sTypo"

			print("Determining %s values:\n" % name)
			lowest, highest = 0.0, 0.0
			lowestGlyph, highestGlyph = None, None

			shouldLimitToCategory = self.pref("preferCategory")
			shouldLimitToScript = self.pref("preferScript")
			shouldLimitToSelectedGlyphs = self.pref("preferSelectedGlyphs")
			selectedCategory = self.w.preferCategoryPopup.getTitle()
			selectedScript = self.w.preferScriptPopup.getTitle()

			if shouldLimitToSelectedGlyphs:
				selectedGlyphNames = [l.parent.name for l in frontmostFont.selectedLayers]
				if not selectedGlyphNames:
					print("⚠️ Ignoring limitation to selected glyphs because no glyphs are selected (in frontmost font).")
					shouldLimitToSelectedGlyphs = False
					Glyphs.defaults["com.mekkablue.VerticalMetricsManager.preferSelectedGlyphs"] = shouldLimitToSelectedGlyphs
					self.LoadPreferences()
			else:
				selectedGlyphNames = ()

			for i, thisFont in enumerate(theseFonts):
				if allOpenFonts:
					fontReport = f"{i+1}. {thisFont.familyName}, "
				else:
					fontReport = ""

				currentMaster = thisFont.selectedFontMaster

				# ascender & descender calculation:
				for thisGlyph in thisFont.glyphs:
					exportCheckOK = not ignoreNonExporting or thisGlyph.export
					categoryCheckOK = not shouldLimitToCategory or thisGlyph.category == selectedCategory
					scriptCheckOK = not shouldLimitToScript or thisGlyph.script == selectedScript
					selectedCheckOK = not shouldLimitToSelectedGlyphs or thisGlyph.name in selectedGlyphNames

					if exportCheckOK and categoryCheckOK and scriptCheckOK and selectedCheckOK:
						for thisLayer in thisGlyph.layers:
							belongsToCurrentMaster = thisLayer.associatedFontMaster() == currentMaster
							if belongsToCurrentMaster or includeAllMasters or allOpenFonts:
								if thisLayer.isSpecialLayer or thisLayer.isMasterLayer:
									lowestPointInLayer = thisLayer.bounds.origin.y
									highestPointInLayer = lowestPointInLayer + thisLayer.bounds.size.height
									if lowestPointInLayer < lowest:
										lowest = lowestPointInLayer
										lowestGlyph = f"{fontReport}{thisGlyph.name}, layer: {thisLayer.name}"
									if highestPointInLayer > highest:
										highest = highestPointInLayer
										highestGlyph = f"{fontReport}{thisGlyph.name}, layer: {thisLayer.name}"

			print("Highest relevant glyph:")
			print(f"- {highestGlyph} ({highest})\n")
			print("Lowest relevant glyph:")
			print(f"- {lowestGlyph} ({lowest})\n")

			if shouldRound:
				highest = roundUpByValue(highest, roundValue)
				lowest = roundUpByValue(lowest, roundValue)

			asc = int(highest)
			desc = int(lowest)

			# line gap calculation:
			xHeight = 0
			for thisFont in theseFonts:
				# determine highest x-height:
				for thisMaster in thisFont.masters:
					measuredX = thisMaster.xHeight
					if measuredX >= thisMaster.capHeight or measuredX > thisFont.upm * 5: # all caps font or NSNotFound
						measuredX = thisMaster.capHeight / 2
					if measuredX > xHeight:
						xHeight = thisMaster.xHeight
				if shouldRound:
					xHeight = roundUpByValue(xHeight, roundValue)

			# calculate linegap, based on highest x-height and calculated asc/desc values:
			#
			# TODO: verify
			# LineGap >= (yMax - yMin) - (Ascender - Descender
			# source: <https://learn.microsoft.com/en-us/typography/opentype/spec/recom#stypoascender-stypodescender-and-stypolinegap>
			# and <https://learn.microsoft.com/en-us/typography/opentype/spec/recom#baseline-to-baseline-distances>

			idealLineSpan = abs(xHeight * 2.8)
			if shouldRound:
				idealLineSpan = roundUpByValue(idealLineSpan, roundValue)
			actualLineSpan = abs(asc) + abs(desc)
			if idealLineSpan > actualLineSpan:
				gap = idealLineSpan - actualLineSpan
				if shouldRound:
					gap = roundUpByValue(gap, roundValue)
			else:
				gap = 0

			if gap > thisFont.upm * 5: # probably NSNotFound
				gap = 0

			print("Calculated values:")
			print(f"- {name} Ascender: {asc}")
			print(f"- {name} Descender: {desc}")
			print(f"- {name} LineGap: {gap}")
			print()

			if sender == self.w.hheaUpdate:
				Glyphs.defaults["com.mekkablue.VerticalMetricsManager.hheaAsc"] = asc
				Glyphs.defaults["com.mekkablue.VerticalMetricsManager.hheaDesc"] = desc
				Glyphs.defaults["com.mekkablue.VerticalMetricsManager.hheaGap"] = gap
			else:
				Glyphs.defaults["com.mekkablue.VerticalMetricsManager.typoAsc"] = asc
				Glyphs.defaults["com.mekkablue.VerticalMetricsManager.typoDesc"] = desc
				Glyphs.defaults["com.mekkablue.VerticalMetricsManager.typoGap"] = gap

		# Updating "Limit to Script" popup:
		elif sender == self.w.preferScriptUpdate:
			scripts = []
			shouldIgnoreNonExporting = self.pref("ignoreNonExporting")
			for thisGlyph in frontmostFont.glyphs:
				inclusionCheckOK = thisGlyph.export or not shouldIgnoreNonExporting
				if inclusionCheckOK and thisGlyph.script and not thisGlyph.script in scripts:
					scripts.append(thisGlyph.script)
			if scripts:
				self.w.preferScriptPopup.setItems(scripts)
				print("✅ Found scripts:\n%s" % ", ".join(scripts))
			else:
				msg = "Found no glyphs belonging to any script in the frontmost font. Please double check."
				print("⚠️ %s" % msg)
				Message(title="Error Determining Scripts", message="Cannot determine list of scripts. %s" % msg, OKButton=None)

		# Updating "Limit to Category" popup:
		elif sender == self.w.preferCategoryUpdate:
			categories = []
			shouldIgnoreNonExporting = self.pref("ignoreNonExporting")
			for thisGlyph in thisFont.glyphs:
				inclusionCheckOK = thisGlyph.export or not shouldIgnoreNonExporting
				if inclusionCheckOK and not thisGlyph.category in categories:
					categories.append(thisGlyph.category)
			if categories:
				self.w.preferCategoryPopup.setItems(categories)
				print("✅ Found categories:\n%s" % ", ".join(categories))
			else:
				msg = "Found no glyphs belonging to any category in the current font. Please double check."
				print("⚠️ %s" % msg)
				Message(title="Error Determining Categories", message="Cannot determine list of categories. %s" % msg, OKButton=None)

		self.LoadPreferences()

		print("hheaGap", self.pref("hheaGap"))
		print("hheaDesc", self.pref("hheaDesc"))
		print("hheaAsc", self.pref("hheaAsc"))
		print("typoGap", self.pref("typoGap"))
		print("typoDesc", self.pref("typoDesc"))
		print("typoAsc", self.pref("typoAsc"))
		print("winDesc", self.pref("winDesc"))
		print("winAsc", self.pref("winAsc"))

	def VerticalMetricsManagerMain(self, sender):
		try:
			Glyphs.clearLog() # clears macro window log
			print("Vertical Metrics Manager: setting parameters\n")

			# update settings to the latest user input:
			if not self.SavePreferences(self):
				print("Note: 'Vertical Metrics Manager' could not write preferences.\n")

			typoAsc = int(self.pref("typoAsc"))
			typoDesc = int(self.pref("typoDesc"))
			typoGap = int(self.pref("typoGap"))
			hheaAsc = int(self.pref("hheaAsc"))
			hheaDesc = int(self.pref("hheaDesc"))
			hheaGap = int(self.pref("hheaGap"))
			winDesc = int(self.pref("winDesc"))
			winAsc = int(self.pref("winAsc"))
			verticalMetricDict = {
				"typoAscender": typoAsc,
				"typoDescender": typoDesc,
				"typoLineGap": typoGap,
				"hheaAscender": hheaAsc,
				"hheaDescender": hheaDesc,
				"hheaLineGap": hheaGap,
				"winDescent": winDesc,
				"winAscent": winAsc,
				}

			allOpenFonts = self.pref("allOpenFonts")
			if allOpenFonts:
				theseFonts = Glyphs.fonts
			else:
				theseFonts = (Glyphs.font, ) # iterable tuple of frontmost font only

			for i, thisFont in enumerate(theseFonts):
				print("\n\n🔠 %s%s:" % (
					"%i. " % (i + 1) if allOpenFonts else "",
					thisFont.familyName,
					))
				if thisFont.filepath:
					print(f"📄 {thisFont.filepath}")
				else:
					print("⚠️ The font file has not been saved yet.")

				for verticalMetricName in sorted(verticalMetricDict.keys()):
					try:
						metricValue = int(verticalMetricDict[verticalMetricName])
						print(f"🔢 {verticalMetricName}: {metricValue}")
						for thisMaster in thisFont.masters:
							thisMaster.customParameters[verticalMetricName] = metricValue
							print(f"  ✅ Master {thisMaster.name}: custom parameter set.")
					except:
						print(f"❌ {verticalMetricName}: No valid value found. Deleting parameters:")
						for thisMaster in thisFont.masters:
							if thisMaster.customParameters[verticalMetricName]:
								del thisMaster.customParameters[verticalMetricName]
								print(f"  ⚠️ Master {thisMaster.name}: custom parameter removed.")
							else:
								print(f"  ❎ Master {thisMaster.name}: no custom parameter found.")

				useTypoMetrics = self.pref("useTypoMetrics")
				print("*️⃣ Use Typo Metrics (fsSelection bit 7)")
				if useTypoMetrics:
					thisFont.customParameters["Use Typo Metrics"] = True
					print("  ✅ Set Use Typo Metrics parameter to YES.")
				else:
					thisFont.customParameters["Use Typo Metrics"] = False
					print("  ⁉️ Set Use Typo Metrics parameter to NO. This is not recommended. Are you sure?")

			Message(
				title="Vertical Metrics Set",
				message="Set vertical metrics in %i font%s. Detailed report in Macro Window." % (
					len(theseFonts),
					"" if len(theseFonts) == 1 else "s",
					),
				OKButton=None,
				)

		except Exception as e:
			# brings macro window to front and reports error:
			Glyphs.showMacroWindow()
			print("Vertical Metrics Manager Error: %s" % e)
			import traceback
			print(traceback.format_exc())

VerticalMetricsManager()
