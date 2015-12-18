# -*- coding: utf-8 -*-
"""
Created on Wed Nov 20 14:44:32 2013

@author: anna
"""

import wx
import os
import sys
from tempfile import gettempdir
from watchdog.observers import Observer
from change_handler import RasterChangeHandler

import wx.lib.newevent
sys.path.append(os.path.join(os.environ['GISBASE'], "etc", "gui", "wxpython"))
from gui_core.gselect import Select
import grass.script as gscript

#from subsurface import compute_crosssection
from run_analyses import run_analyses


updateGUIEvt, EVT_UPDATE_GUI = wx.lib.newevent.NewCommandEvent()


class TangeomsPlugin(wx.Dialog):
    def __init__(self, giface, parent):
        wx.Dialog.__init__(self, parent, title="Tangible Landscape", style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        self.giface=giface
        self.parent=parent
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        hSizer = wx.BoxSizer(wx.HORIZONTAL)
        modelBox = wx.StaticBox(self, label="Scanning parameters")
        modelSizer = wx.StaticBoxSizer(modelBox, wx.VERTICAL)

        # create widgets
        btnCalibrate = wx.Button(self, label="Calibrate")
        btnStart = wx.Button(self, label="Start")
        btnStop = wx.Button(self, label="Stop")
        btnClose = wx.Button(self, label="Close")
        btnScanOnce = wx.Button(self, label="Scan once")
        self.scan_name = wx.TextCtrl(self, value='scan')
        self.status = wx.StaticText(self)
        self.textInfo = wx.TextCtrl(self, size=(-1, 100), style=wx.TE_MULTILINE | wx.TE_READONLY)
        # widgets for model
        self.elevInput = Select(self, size=(-1, -1), type='raster')
        self.regionInput = Select(self, size=(-1, -1), type='region')
        self.zexag = wx.TextCtrl(self)
        self.rotate = wx.SpinCtrl(self, min=0, max=360, initial=180)
        self.numscans = wx.SpinCtrl(self, min=1, max=5, initial=1)
        self.trim = {}
        for each in 'nsewtb':
            self.trim[each] = wx.TextCtrl(self, size=(35, -1))
        self.interpolate = wx.CheckBox(self, label="Use interpolation instead of binning")
        self.smooth = wx.TextCtrl(self)
        self.resolution = wx.TextCtrl(self)

        # layout
        hSizer.Add(btnStart, flag=wx.EXPAND | wx.ALL, border=5)
        hSizer.Add(btnStop, flag=wx.EXPAND | wx.ALL, border=5)
        hSizer.AddStretchSpacer()
        hSizer.Add(btnScanOnce, flag=wx.EXPAND | wx.ALL, border=5)
        mainSizer.Add(hSizer, flag=wx.EXPAND)
        hSizer = wx.BoxSizer(wx.HORIZONTAL)
        hSizer.Add(wx.StaticText(self, label="Name of scanned raster:"), flag=wx.EXPAND | wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=5)
        hSizer.Add(self.scan_name, proportion=1, flag=wx.EXPAND | wx.ALL, border=5)
        mainSizer.Add(hSizer, flag=wx.EXPAND)
        hSizer = wx.BoxSizer(wx.HORIZONTAL)
        hSizer.Add(self.status, flag=wx.EXPAND | wx.ALL, border=5)
        mainSizer.Add(hSizer)
        hSizer = wx.BoxSizer(wx.HORIZONTAL)
        hSizer.Add(self.textInfo, flag=wx.EXPAND | wx.ALL, proportion=1, border=5)
        mainSizer.Add(hSizer, proportion=1, flag=wx.EXPAND)
        # model parameters
        hSizer = wx.BoxSizer(wx.HORIZONTAL)
        hSizer.Add(wx.StaticText(self, label="Reference DEM:"), flag=wx.ALL|wx.ALIGN_CENTER_VERTICAL, border=3)
        hSizer.Add(self.elevInput, proportion=1, flag=wx.ALL|wx.ALIGN_CENTER_VERTICAL, border=3)
        modelSizer.Add(hSizer, flag=wx.EXPAND)
        # region
        hSizer = wx.BoxSizer(wx.HORIZONTAL)
        hSizer.Add(wx.StaticText(self, label="Reference region:"), flag=wx.ALL|wx.ALIGN_CENTER_VERTICAL, border=3)
        hSizer.Add(self.regionInput, proportion=1, flag=wx.ALL|wx.ALIGN_CENTER_VERTICAL, border=3)
        modelSizer.Add(hSizer, flag=wx.EXPAND)
        hSizer = wx.BoxSizer(wx.HORIZONTAL)
        hSizer.Add(wx.StaticText(self, label="Z-exaggeration:"), proportion=1, flag=wx.ALL|wx.ALIGN_CENTER_VERTICAL, border=3)
        hSizer.Add(self.zexag, flag=wx.ALL|wx.ALIGN_CENTER_VERTICAL, border=3)
        modelSizer.Add(hSizer, flag=wx.EXPAND)
        # number of scans
        hSizer = wx.BoxSizer(wx.HORIZONTAL)
        hSizer.Add(wx.StaticText(self, label="Number of scans:"), proportion=1, flag=wx.ALL|wx.ALIGN_CENTER_VERTICAL, border=3)
        hSizer.Add(self.numscans, flag=wx.ALL|wx.ALIGN_CENTER_VERTICAL, border=3)
        modelSizer.Add(hSizer, flag=wx.EXPAND)
        hSizer = wx.BoxSizer(wx.HORIZONTAL)
        hSizer.Add(wx.StaticText(self, label="Rotation angle:"), proportion=1, flag=wx.ALL|wx.ALIGN_CENTER_VERTICAL, border=3)
        hSizer.Add(self.rotate, flag=wx.ALL|wx.ALIGN_CENTER_VERTICAL, border=3)
        modelSizer.Add(hSizer, flag=wx.EXPAND)
        # smooth
        hSizer = wx.BoxSizer(wx.HORIZONTAL)
        hSizer.Add(wx.StaticText(self, label="Smooth value:"), proportion=1, flag=wx.ALL|wx.ALIGN_CENTER_VERTICAL, border=3)
        hSizer.Add(self.smooth, flag=wx.ALL|wx.ALIGN_CENTER_VERTICAL, border=3)
        modelSizer.Add(hSizer, flag=wx.EXPAND)
        # resolution
        hSizer = wx.BoxSizer(wx.HORIZONTAL)
        hSizer.Add(wx.StaticText(self, label="Resolution [mm]:"), proportion=1, flag=wx.ALL|wx.ALIGN_CENTER_VERTICAL, border=3)
        hSizer.Add(self.resolution, flag=wx.ALL|wx.ALIGN_CENTER_VERTICAL, border=3)
        modelSizer.Add(hSizer, flag=wx.EXPAND)
        hSizer = wx.BoxSizer(wx.HORIZONTAL)
        hSizer.Add(wx.StaticText(self, label="Trim scan N, S, E, W [cm]:"), proportion=1, flag=wx.ALL|wx.ALIGN_CENTER_VERTICAL, border=3)
        for each in 'nsew':
            hSizer.Add(self.trim[each], flag=wx.ALL|wx.ALIGN_CENTER_VERTICAL, border=3)
        modelSizer.Add(hSizer, flag=wx.EXPAND)
        hSizer = wx.BoxSizer(wx.HORIZONTAL)
        hSizer.Add(wx.StaticText(self, label="Limit scan vertically T, B [cm]:"), proportion=1, flag=wx.ALL|wx.ALIGN_CENTER_VERTICAL, border=3)
        for each in 'tb':
            hSizer.Add(self.trim[each], flag=wx.ALL|wx.ALIGN_CENTER_VERTICAL, border=3)
        modelSizer.Add(hSizer, flag=wx.EXPAND)
        hSizer = wx.BoxSizer(wx.HORIZONTAL)
        hSizer.Add(self.interpolate, flag=wx.ALL|wx.ALIGN_CENTER_VERTICAL, border=3)
        modelSizer.Add(hSizer, flag=wx.EXPAND)
        mainSizer.Add(modelSizer, flag=wx.EXPAND|wx.ALL, border=5)

        hSizer = wx.BoxSizer(wx.HORIZONTAL)
        hSizer.Add(btnCalibrate, flag=wx.EXPAND | wx.ALL, border=5)
        hSizer.AddStretchSpacer()
        hSizer.Add(btnClose, flag=wx.EXPAND | wx.ALL, border=5)
        mainSizer.Add(hSizer, flag=wx.EXPAND)

        # bind events
        btnStart.Bind(wx.EVT_BUTTON, lambda evt: self.Start())
        btnStop.Bind(wx.EVT_BUTTON, lambda evt: self.Stop())
        btnClose.Bind(wx.EVT_BUTTON, self.OnClose)
        btnCalibrate.Bind(wx.EVT_BUTTON, self.Calibrate)
        btnScanOnce.Bind(wx.EVT_BUTTON, self.ScanOnce)
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        self.Bind(EVT_UPDATE_GUI, self.OnUpdate)

        self.SetSizer(mainSizer)
        mainSizer.Fit(self)

    def OnClose(self, event):
        self.Stop()
        self.Destroy()

    def Start(self):
        raise NotImplementedError

    def Stop(self):
        raise NotImplementedError

    def OnUpdate(self, event):
        for each in self.giface.GetAllMapDisplays():
            each.GetMapWindow().UpdateMap()
        self.UpdateText()

    def Calibrate(self, event):
        from prepare_calibration import write_matrix
        matrix_file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'calib_matrix.txt')
        write_matrix(matrix_path=matrix_file_path)
        # update
        with open(matrix_file_path, 'r') as f:
            self.calib_matrix = f.read()


class TangeomsImportPlugin(TangeomsPlugin):
    def __init__(self, giface, guiparent,  elev_real, scan, scanFile, minZ, maxZ):
        TangeomsPlugin.__init__(self, giface, guiparent)
        self.output = scan
        self.tmp_file = scanFile
        self.minZ = minZ
        self.maxZ = maxZ
        self.data = {'scan_name': self.output, 'info_text': [],
                     'elevation': elev_real, 'region': '',
                     'zexag': 1., 'smooth': 7, 'numscans': 1,
                     'rotation_angle': 180, 'resolution': 2,
                     'trim_nsewtb': [0, 0, 0, 0, 60, 100],
                     'interpolate': False}
        self.elevInput.SetValue(self.data['elevation'])
        self.zexag.SetValue(str(self.data['zexag']))
        self.rotate.SetValue(self.data['rotation_angle'])
        self.numscans.SetValue(self.data['numscans'])
        self.interpolate.SetValue(self.data['interpolate'])
        for i, each in enumerate('nsewtb'):
            self.trim[each].SetValue(str(self.data['trim_nsewtb'][i]))
        self.interpolate.SetValue(self.data['interpolate'])
        self.smooth.SetValue(str(self.data['smooth']))
        self.resolution.SetValue(str(self.data['resolution']))

        calib = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'calib_matrix.txt')
        if os.path.exists(calib):
            with open(calib, 'r') as f:
                self.calib_matrix = f.read()
        else:
            self.calib_matrix = None
            giface.WriteWarning("WARNING: No calibration file exists")

        self.process = None
        self.observer = None
        self.timer = wx.Timer(self)
        self.changedInput = False
        self.Bind(wx.EVT_TIMER, self.RestartIfNotRunning, self.timer)
        self.BindModelProperties()

    def BindModelProperties(self):
        self.scan_name.Bind(wx.EVT_TEXT, self.OnScanName)
        # model parameters
        self.elevInput.Bind(wx.EVT_TEXT, self.OnModelProperties)
        self.regionInput.Bind(wx.EVT_TEXT, self.OnModelProperties)
        self.zexag.Bind(wx.EVT_TEXT, self.OnModelProperties)
        self.rotate.Bind(wx.EVT_SPINCTRL, self.OnModelProperties)
        self.rotate.Bind(wx.EVT_TEXT, self.OnModelProperties)
        self.numscans.Bind(wx.EVT_SPINCTRL, self.OnModelProperties)
        self.numscans.Bind(wx.EVT_TEXT, self.OnModelProperties)
        self.interpolate.Bind(wx.EVT_CHECKBOX, self.OnModelProperties)
        self.smooth.Bind(wx.EVT_TEXT, self.OnModelProperties)
        self.resolution.Bind(wx.EVT_TEXT, self.OnModelProperties)
        for each in 'nsewtb':
            self.trim[each].Bind(wx.EVT_TEXT, self.OnModelProperties)

    def ScanOnce(self, event):
        if self.process:
            return
        self.status.SetLabel("Scanning...")
        wx.SafeYield()
        params = {}
        if self.calib_matrix:
            params['calib_matrix'] = self.calib_matrix
        if self.data['elevation']:
            params['raster'] = self.data['elevation']
        elif self.data['region']:
            params['region'] = self.data['region']
        trim_nsew = ','.join([str(i) for i in self.data['trim_nsewtb'][:4]])
        zrange = ','.join([str(i) for i in self.data['trim_nsewtb'][4:]])
        self.process = gscript.start_command('r.in.kinect', output=self.data['scan_name'],             
                              quiet=True, trim=trim_nsew, smooth_radius=float(self.data['smooth'])/1000,
                              zrange=zrange, rotate=self.data['rotation_angle'], resolution=float(self.data['resolution'])/1000,
                              zexag=self.data['zexag'], numscan=self.data['numscans'], overwrite=True, **params)
        self.status.SetLabel("Importing scan ...")
        self.process.wait()
        self.process = None
        run_analyses(self.data['scan_name'], real_elev=self.data['elevation'], zexag=self.data['zexag'])
        self.status.SetLabel("Done.")
        self.OnUpdate(None)
        
    
    def OnScanName(self, event):
        name = self.scan_name.GetValue()
        self.data['scan_name'] = name
        if self.process and self.process.poll() is None:
            self.Stop()
            self.Start()

    def OnModelProperties(self, event):
        self.data['elevation'] = self.elevInput.GetValue()
        self.data['region'] = self.elevInput.GetValue()
        self.data['rotation_angle'] = self.rotate.GetValue()
        self.data['numscans'] = self.numscans.GetValue()
        self.data['interpolate'] = self.interpolate.IsChecked()
        self.data['smooth'] = self.smooth.GetValue()
        self.data['resolution'] = self.resolution.GetValue()

        try:
            self.data['zexag'] = float(self.zexag.GetValue())
            for i, each in enumerate('nsewtb'):
                self.data['trim_nsewtb'][i] = float(self.trim[each].GetValue())
        except ValueError:
            pass
        self.changedInput = True

    def UpdateText(self):
        self.textInfo.SetValue(os.linesep.join(self.data['info_text']))
        del self.data['info_text'][:]

    def RestartIfNotRunning(self, event):
        """Mechanism to restart scanning if process ends or
        there was a change in input options"""
        if self.process and self.process.poll is not None:
            self.Start()
        if self.changedInput:
            self.changedInput = False
            self.Stop()
            self.Start()
        
    def Start(self):
        if self.process and self.process.poll() is None:
            return
        if self.data['interpolate']:
            method = 'interpolation'
        else:
            method =  'mean'
        params = {}
        if self.calib_matrix:
            params['calib_matrix'] = self.calib_matrix
        if self.data['elevation']:
            params['raster'] = self.data['elevation']
        elif self.data['region']:
            params['region'] = self.data['region']
        trim_nsew = ','.join([str(i) for i in self.data['trim_nsewtb'][:4]])
        zrange = ','.join([str(i) for i in self.data['trim_nsewtb'][4:]])
        self.process = gscript.start_command('r.in.kinect', output=self.data['scan_name'],
                              quiet=True, trim=trim_nsew, smooth_radius=float(self.data['smooth'])/1000,
                              zrange=zrange, rotate=self.data['rotation_angle'], method=method, 
                              zexag=self.data['zexag'], numscan=self.data['numscans'], overwrite=True,
                              flags='l', resolution=float(self.data['resolution'])/1000, **params)
        self.status.SetLabel("Real-time scanning is running now.")
        gisenv = gscript.gisenv()
        path = os.path.join(gisenv['GISDBASE'], gisenv['LOCATION_NAME'], gisenv['MAPSET'], 'fcell')
        event_handler = RasterChangeHandler(self.runImport, self.data)
        self.observer = Observer()
        self.observer.schedule(event_handler, path)
        self.observer.start()
        self.timer.Start(1000)

    def Stop(self):
        if self.process and self.process.poll() is None:  # still running
            self.process.terminate()
            self.process.wait()
            self.process = None
            if self.observer:
                self.observer.stop()
                self.observer.join()
        self.timer.Stop()
        self.status.SetLabel("Real-time scanning stopped.")

    def runImport(self):
        run_analyses(self.data['scan_name'], real_elev=self.data['elevation'], zexag=self.data['zexag'])
        evt = updateGUIEvt(self.GetId())
        wx.PostEvent(self, evt)


def run(giface, guiparent):
    dlg = TangeomsImportPlugin(giface, guiparent, elev_real='elevation', scan='scan',
                scanFile=os.path.join(os.path.realpath(gettempdir()), 'kinect_scan.txt'), minZ=0.4, maxZ=1.2)
    dlg.CenterOnParent()
    dlg.Show()


if __name__ == '__main__':
    run(None, None)
