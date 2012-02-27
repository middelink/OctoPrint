from __future__ import absolute_import
import __init__

import wx, os, platform, types
import ConfigParser

from fabmetheus_utilities import settings

from newui import configWindowBase
from newui import advancedConfig
from newui import preview3d
from newui import sliceProgessPanel
from newui import alterationPanel
from newui import validators

def main():
	app = wx.App(False)
	mainWindow()
	app.MainLoop()

class mainWindow(configWindowBase.configWindowBase):
	"Main user interface window"
	def __init__(self):
		super(mainWindow, self).__init__(title='SkeinPyPy')
		
		wx.EVT_CLOSE(self, self.OnClose)
		
		menubar = wx.MenuBar()
		fileMenu = wx.Menu()
		i = fileMenu.Append(-1, 'Open Profile...', 'Open Profile...')
		self.Bind(wx.EVT_MENU, self.OnLoadProfile, i)
		i = fileMenu.Append(-1, 'Save Profile...', 'Save Profile...')
		self.Bind(wx.EVT_MENU, self.OnSaveProfile, i)
		i = fileMenu.Append(wx.ID_EXIT, 'Quit', 'Quit application')
		self.Bind(wx.EVT_MENU, self.OnQuit, i)
		menubar.Append(fileMenu, '&File')
		
		expertMenu = wx.Menu()
		i = expertMenu.Append(-1, 'Open expert settings...', 'Open expert settings...')
		self.Bind(wx.EVT_MENU, self.OnExpertOpen, i)
		menubar.Append(expertMenu, 'Expert')
		self.SetMenuBar(menubar)
		
		self.lastPath = ""
		self.filename = configWindowBase.getPreference('lastFile', None)
		self.progressPanelList = []

		#Preview window
		self.preview3d = preview3d.previewPanel(self)

		#Main tabs
		nb = wx.Notebook(self)
		
		(left, right) = self.CreateConfigTab(nb, 'Print config')
		
		configWindowBase.TitleRow(left, "Accuracy")
		c = configWindowBase.SettingRow(left, "Layer height (mm)", 'layer_height', '0.2', 'Layer height in millimeters.\n0.2 is a good value for quick prints.\n0.1 gives high quality prints.')
		validators.validFloat(c, 0.0)
		validators.warningAbove(c, 0.31, "Thicker layers then 0.3mm usually give bad results and are not recommended.")
		c = configWindowBase.SettingRow(left, "Wall thickness (mm)", 'wall_thickness', '0.8', 'Thickness of the walls.\nThis is used in combination with the nozzle size to define the number\nof perimeter lines and the thickness of those perimeter lines.')
		validators.validFloat(c, 0.0)
		validators.wallThicknessValidator(c)
		
		configWindowBase.TitleRow(left, "Fill")
		c = configWindowBase.SettingRow(left, "Bottom/Top thickness (mm)", 'solid_layer_thickness', '0.6', 'This controls the thickness of the bottom and top layers, the amount of solid layers put down is calculated by the layer thickness and this value.\nHaving this value a multiply of the layer thickness makes sense. And keep it near your wall thickness to make an evenly strong part.')
		validators.validFloat(c, 0.0)
		c = configWindowBase.SettingRow(left, "Fill Density (%)", 'fill_density', '20', 'This controls how densily filled the insides of your print will be. For a solid part use 100%, for an empty part use 0%. A value around 20% is usually enough')
		validators.validFloat(c, 0.0, 100.0)
		
		configWindowBase.TitleRow(left, "Skirt")
		c = configWindowBase.SettingRow(left, "Line count", 'skirt_line_count', '1', 'The skirt is a line drawn around the object at the first layer. This helps to prime your extruder, and to see if the object fits on your platform.\nSetting this to 0 will disable the skirt.')
		validators.validInt(c, 0, 10)
		c = configWindowBase.SettingRow(left, "Start distance (mm)", 'skirt_gap', '6.0', 'The distance between the skirt and the first layer.\nThis is the minimal distance, multiple skirt lines will be put outwards from this distance.')
		validators.validFloat(c, 0.0)

		configWindowBase.TitleRow(right, "Speed")
		c = configWindowBase.SettingRow(right, "Print speed (mm/s)", 'print_speed', '50')
		validators.validFloat(c, 1.0)
		validators.warningAbove(c, 150.0, "It is highly unlikely that your machine can achieve a printing speed above 150mm/s")
		
		#Printing temperature is a problem right now, as our start code depends on a heated head.
		#configWindowBase.TitleRow(right, "Temperature")
		#c = configWindowBase.SettingRow(right, "Printing temperature", 'print_temperature', '0', 'Temperature used for printing. Set at 0 to pre-heat yourself')
		#validators.validFloat(c, 0.0, 350.0)
		#validators.warningAbove(c, 260.0, "Temperatures above 260C could damage your machine.")
		
		configWindowBase.TitleRow(right, "Support")
		c = configWindowBase.SettingRow(right, "Support type", 'support', ['None', 'Exterior only', 'Everywhere', 'Empty layers only'], 'Type of support structure build.\nNone does not do any support.\nExterior only only creates support on the outside.\nEverywhere creates support even on the insides of the model.\nOnly on empty layers is for stacked objects.')
		
		(left, right) = self.CreateConfigTab(nb, 'Machine && Filament')
		
		configWindowBase.TitleRow(left, "Machine size")
		c = configWindowBase.SettingRow(left, "Machine center X (mm)", 'machine_center_x', '100', 'The center of your machine, your print will be placed at this location')
		validators.validInt(c, 10)
		configWindowBase.settingNotify(c, self.preview3d.updateCenterX)
		c = configWindowBase.SettingRow(left, "Machine center Y (mm)", 'machine_center_y', '100', 'The center of your machine, your print will be placed at this location')
		validators.validInt(c, 10)
		configWindowBase.settingNotify(c, self.preview3d.updateCenterY)
		#self.AddSetting(left, "Width (mm)", settings.IntSpin().getFromValue(10, "machine_width", None, 1000, 205))
		#self.AddSetting(left, "Depth (mm)", settings.IntSpin().getFromValue(10, "machine_depth", None, 1000, 205))
		#self.AddSetting(left, "Height (mm)", settings.IntSpin().getFromValue(10, "machine_height", None, 1000, 200))

		configWindowBase.TitleRow(left, "Machine nozzle")
		c = configWindowBase.SettingRow(left, "Nozzle size (mm)", 'nozzle_size', '0.4')
		validators.validFloat(c, 0.1, 1.0)

		configWindowBase.TitleRow(left, "Retraction")
		c = configWindowBase.SettingRow(left, "Minimal travel (mm)", 'retraction_min_travel', '5.0')
		validators.validFloat(c, 0.0)
		c = configWindowBase.SettingRow(left, "Speed (mm/s)", 'retraction_speed', '13.5')
		validators.validFloat(c, 0.1)
		c = configWindowBase.SettingRow(left, "Distance (mm)", 'retraction_amount', '0.0')
		validators.validFloat(c, 0.0)
		c = configWindowBase.SettingRow(left, "Extra length on start (mm)", 'retraction_extra', '0.0')
		validators.validFloat(c, 0.0)

		configWindowBase.TitleRow(right, "Speed")
		c = configWindowBase.SettingRow(right, "Travel speed (mm/s)", 'travel_speed', '150')
		validators.validFloat(c, 1.0)
		validators.warningAbove(c, 300.0, "It is highly unlikely that your machine can achieve a travel speed above 150mm/s")
		c = configWindowBase.SettingRow(right, "Max Z speed (mm/s)", 'max_z_speed', '1.0')
		validators.validFloat(c, 0.5)
		c = configWindowBase.SettingRow(right, "Bottom layer speed", 'bottom_layer_speed', '25')
		validators.validFloat(c, 0.0)

		configWindowBase.TitleRow(right, "Cool")
		#c = SettingRow(right, "Cool type", self.plugins['cool'].preferencesDict['Cool_Type'])
		c = configWindowBase.SettingRow(right, "Minimal layer time (sec)", 'cool_min_layer_time', '10', 'Minimum time spend in a layer, gives the layer time to cool down before the next layer is put on top. If the layer will be placed down too fast the printer will slow down to make sure it has spend atleast this amount of seconds printing this layer.')
		validators.validFloat(c, 0.0)

		configWindowBase.TitleRow(right, "Filament")
		c = configWindowBase.SettingRow(right, "Diameter (mm)", 'filament_diameter', '2.98', 'Diameter of your filament, as accurately as possible.\nIf you cannot measure this value you will have to callibrate it, a higher number means less extrusion, a smaller number generates more extrusion.')
		validators.validFloat(c, 1.0)
		c = configWindowBase.SettingRow(right, "Packing Density", 'filament_density', '1.00', 'Packing density of your filament. This should be 1.00 for PLA and 0.85 for ABS')
		validators.validFloat(c, 0.5, 1.5)
		
		nb.AddPage(alterationPanel.alterationPanel(nb), "Start/End-GCode")

		# load and slice buttons.
		loadButton = wx.Button(self, -1, 'Load STL')
		sliceButton = wx.Button(self, -1, 'Slice to GCode')
		self.Bind(wx.EVT_BUTTON, self.OnLoadSTL, loadButton)
		self.Bind(wx.EVT_BUTTON, self.OnSlice, sliceButton)

		#Main sizer, to position the preview window, buttons and tab control
		sizer = wx.GridBagSizer()
		self.SetSizer(sizer)
		sizer.Add(nb, (0,0), span=(1,1), flag=wx.EXPAND)
		sizer.Add(self.preview3d, (0,1), span=(1,3), flag=wx.EXPAND)
		sizer.AddGrowableCol(2)
		sizer.AddGrowableRow(0)
		sizer.Add(loadButton, (1,1))
		sizer.Add(sliceButton, (1,2))
		self.sizer = sizer

		if self.filename != None:
			self.preview3d.loadModelFile(self.filename)
			self.lastPath = os.path.split(self.filename)[0]

		self.updateProfileToControls()

		self.Fit()
		self.Centre()
		self.Show(True)
	
	def OnLoadProfile(self, e):
		dlg=wx.FileDialog(self, "Select profile file to load", self.lastPath, style=wx.FD_OPEN|wx.FD_FILE_MUST_EXIST)
		dlg.SetWildcard("ini files (*.ini)|*.ini")
		if dlg.ShowModal() == wx.ID_OK:
			profileFile = dlg.GetPath()
			self.lastPath = os.path.split(profileFile)[0]
			settings.loadGlobalProfile(profileFile)
			self.updateProfileToControls()
		dlg.Destroy()
	
	def OnSaveProfile(self, e):
		dlg=wx.FileDialog(self, "Select profile file to save", self.lastPath, style=wx.FD_SAVE)
		dlg.SetWildcard("ini files (*.ini)|*.ini")
		if dlg.ShowModal() == wx.ID_OK:
			profileFile = dlg.GetPath()
			self.lastPath = os.path.split(profileFile)[0]
			settings.saveGlobalProfile(profileFile)
		dlg.Destroy()
	
	def OnLoadSTL(self, e):
		dlg=wx.FileDialog(self, "Open file to print", self.lastPath, style=wx.FD_OPEN|wx.FD_FILE_MUST_EXIST)
		dlg.SetWildcard("OBJ, STL files (*.stl;*.obj)|*.stl;*.obj")
		if dlg.ShowModal() == wx.ID_OK:
			self.filename=dlg.GetPath()
			configWindowBase.putPreference('lastFile', self.filename)
			if not(os.path.exists(self.filename)):
				return
			self.lastPath = os.path.split(self.filename)[0]
			self.preview3d.loadModelFile(self.filename)
		dlg.Destroy()
	
	def OnSlice(self, e):
		if self.filename == None:
			return
		settings.saveGlobalProfile(settings.getDefaultProfilePath())
		
		#Create a progress panel and add it to the window. The progress panel will start the Skein operation.
		spp = sliceProgessPanel.sliceProgessPanel(self, self, self.filename)
		self.sizer.Add(spp, (len(self.progressPanelList)+2,0), span=(1,4), flag=wx.EXPAND)
		self.sizer.Layout()
		newSize = self.GetSize();
		newSize.IncBy(0, spp.GetSize().GetHeight())
		self.SetSize(newSize)
		self.progressPanelList.append(spp)

	def OnExpertOpen(self, e):
		acw = advancedConfig.advancedConfigWindow()
		acw.Centre()
		acw.Show(True)

	def removeSliceProgress(self, spp):
		self.progressPanelList.remove(spp)
		newSize = self.GetSize();
		newSize.IncBy(0, -spp.GetSize().GetHeight())
		self.SetSize(newSize)
		spp.Destroy()
		for spp in self.progressPanelList:
			self.sizer.Remove(spp)
		i = 2
		for spp in self.progressPanelList:
			self.sizer.Add(spp, (i,0), span=(1,4), flag=wx.EXPAND)
			i += 1
		self.sizer.Layout()
	
	def updateProfileToControls(self):
		"Update the configuration wx controls to show the new configuration settings"
		for setting in self.settingControlList:
			setting.SetValue(settings.getSetting(setting.configName))

	def OnQuit(self, e):
		self.Close()
	
	def OnClose(self, e):
		settings.saveGlobalProfile(settings.getDefaultProfilePath())
		self.Destroy()

