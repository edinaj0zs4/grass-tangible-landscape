# -*- coding: utf-8 -*-
"""
@brief GUI panel fro drawing functionality

This program is free software under the GNU General Public License
(>=v2). Read the file COPYING that comes with GRASS for details.

@author: Anna Petrasova (akratoc@ncsu.edu)
"""
import wx

from gui_core.gselect import Select
import grass.script as gscript

from tangible_utils import run_analyses, updateGUIEvt, EVT_UPDATE_GUI


class DrawingPanel(wx.Panel):
    def __init__(self, parent, giface, settings):
        wx.Panel.__init__(self, parent)
        self.giface = giface
        self.settings = settings
        if 'drawing' not in self.settings:
            self.settings['drawing'] = {}
            self.settings['drawing']['name'] = ''
            self.settings['drawing']['type'] = 'point'
            self.settings['drawing']['append'] = False
            self.settings['drawing']['appendName'] = ''

        mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.draw_vector = Select(self, size=(-1, -1), type='vector')
        self.draw_vector.SetValue(self.settings['drawing']['name'])
        self.draw_vector.Bind(wx.EVT_TEXT, self.OnDrawChange)
        self.draw_type = wx.RadioBox(parent=self, label="Vector type", choices=['point', 'line', 'area'])
        {'point': 0, 'line': 1, 'area': 2}[self.settings['drawing']['type']]
        self.draw_type.SetSelection({'point': 0, 'line': 1, 'area': 2}[self.settings['drawing']['type']])
        self.draw_type.Bind(wx.EVT_RADIOBOX, self.OnDrawChange)
        self.append = wx.CheckBox(parent=self, label="Append vector")
        self.append.SetValue(self.settings['drawing']['append'])
        self.append.Bind(wx.EVT_CHECKBOX, self.OnDrawChange)
        self.appendName = Select(self, size=(-1, -1), type='vector')
        self.appendName.SetValue(self.settings['drawing']['appendName'])
        self.appendName.Bind(wx.EVT_TEXT, self.OnDrawChange)
        self.clearBtn = wx.Button(parent=self, label="Clear")
        self.clearBtn.Bind(wx.EVT_BUTTON, lambda evt: self._newAppendedVector(evt))
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(wx.StaticText(self, label="Vector name:"), flag=wx.ALIGN_CENTER_VERTICAL, border=5)
        sizer.Add(self.draw_vector, proportion=1, flag=wx.ALIGN_CENTER_VERTICAL, border=5)
        mainSizer.Add(sizer, flag=wx.EXPAND | wx.ALL, border=5)
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.draw_type, proportion=1, flag=wx.ALIGN_CENTER_VERTICAL, border=5)
        mainSizer.Add(sizer, flag=wx.EXPAND | wx.ALL, border=5)
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.append, proportion=0, flag=wx.ALIGN_CENTER_VERTICAL, border=5)
        sizer.Add(self.appendName, proportion=1, flag=wx.ALIGN_CENTER_VERTICAL, border=5)
        sizer.Add(self.clearBtn, flag=wx.ALIGN_CENTER_VERTICAL, border=5)
        mainSizer.Add(sizer, flag=wx.EXPAND | wx.ALL, border=5)
        self.SetSizer(mainSizer)
        mainSizer.Fit(self)

    def OnDrawChange(self, event):
        self.settings['drawing']['name'] = self.draw_vector.GetValue().split('@')[0]
        self.settings['drawing']['appendName'] = self.appendName.GetValue().split('@')[0]
        self.settings['drawing']['type'] = ['point', 'line', 'area'][self.draw_type.GetSelection()]
        self.settings['drawing']['append'] = self.append.IsChecked()

    def appendVector(self):
        if not self.settings['drawing']['append']:
            return
        ff = gscript.find_file(self.settings['drawing']['appendName'],
                               element='vector', mapset=gscript.gisenv()['MAPSET'])
        if not(ff and ff['fullname']):
            self._newAppendedVector()
        gscript.run_command('v.patch', input=self.settings['drawing']['name'],
                            output=self.settings['drawing']['appendName'],
                            flags='a', overwrite=True, quiet=True)

    def _newAppendedVector(self, event=None):
        gscript.run_command('v.edit', tool='create', map=self.settings['drawing']['appendName'],
                            overwrite=True, quiet=True)
        if event:
            event.Skip()
        evt = updateGUIEvt(self.GetId())
        wx.PostEvent(self, evt)
