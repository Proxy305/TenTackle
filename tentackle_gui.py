# -*- coding: utf-8 -*-
# TenTackle_GUI: Simple GUI for TenTackle

import os, sys
import wx
import numpy as np
import matplotlib

from main import Table, Curve, Curve_cache, config

matplotlib.interactive(False)
matplotlib.use("WXAgg")
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg
from matplotlib.backends.backend_wx import NavigationToolbar2Wx
from matplotlib.figure import Figure


class CanvasPanel(wx.Panel):
    def __init__(self, parent):

        wx.Panel.__init__(self, parent)
        
        self.slider = wx.Slider(self, -1, value=1, minValue=0, maxValue=11)
        self.slider.Bind(wx.EVT_SLIDER, self.OnSlider)

        self.figure = Figure()
        self.plot = self.figure.add_subplot(111)
        self.plot.axis(xmin=0, ymin=0)
        self.plot.set(ylabel = 'Stress [%s]' % config.get('axis').get('y_unit'), xlabel = 'Strain [%s]' % config.get('axis').get('x_unit'))
        self.canvas = FigureCanvasWxAgg(self, -1, self.figure)


        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.canvas, proportion=1, flag=wx.LEFT | wx.TOP | wx.GROW)
        self.sizer.Add(self.slider, proportion=0, flag=wx.LEFT | wx.TOP | wx.GROW)
        self.SetSizer(self.sizer)
        # self.Fit()

    def OnSlider(self, event):
        self.draw()

    def draw(self, curves_list):
        
        self.plot.clear()
        for curve in curves_list:
            array = curve.get_data()
            self.plot.plot(array[:, 1]/config['axis']['x_scaling'], array[:, 0]/config['axis']['y_scaling'])
        self.canvas.draw()


class Import_dialog(wx.Dialog):

    def __init__(self, *args, **kw):

        super(Import_dialog, self).__init__(*args, **kw)

        self.SetTitle('Import')
        
        self.file_path = '/test'
        self.canvas_panel = CanvasPanel(self)
        self.cache = Curve_cache()
        self.table = None

        self.Center()
        self.init_ui()
        
        

    def init_ui(self):

        # panel = wx.Panel(self)
        # h_box = wx.BoxSizer(wx.HORIZONTAL)
        # button = wx.Button(panel, label='label')
        
        print(self.file_path)
    
        # self.SetSize((350, 250))

    def set_file_path(self, file_path):
        
        self.file_path = file_path
        if os.path.isfile(file_path):
            self.table = Table(file_path)
            self.cache.cache(self.table)
        self.canvas_panel.draw(self.cache.cached)
        
        

class Main_window(wx.Frame):

    def __init__(self, *args, **kwargs):
        super(Main_window, self).__init__(*args, **kwargs)

        self.import_dialog = Import_dialog(self)

        self.init_ui()

    def init_ui(self):

        # Menu bar

        menubar = wx.MenuBar()
        file_menu = wx.Menu()

        mb_open = wx.MenuItem(file_menu, wx.ID_ANY, '&Open project...\tCtrl+O')
        file_menu.Append(mb_open)

        mb_save = wx.MenuItem(file_menu, wx.ID_ANY, '&Save project...\tCtrl+S')
        file_menu.Append(mb_save)

        mb_save_as = wx.MenuItem(file_menu, wx.ID_ANY, '&Save project as...\tCtrl+Shift+S')
        file_menu.Append(mb_save_as)

        mb_new = wx.MenuItem(file_menu, wx.ID_ANY, '&New project\tCtrl+N')
        file_menu.Append(mb_new)
        
        file_menu.AppendSeparator()

        mb_quit = wx.MenuItem(file_menu, wx.ID_ANY, '&Quit\tCtrl+Q')
        file_menu.Append(mb_quit)
        self.Bind(wx.EVT_MENU, self.on_quit, mb_quit)
       
        menubar.Append(file_menu, '&File')


        help_menu = wx.Menu()
        mb_help = wx.MenuItem(help_menu, wx.ID_HELP, '&Help\tCtrl+H')
        help_menu.Append(mb_help)

        mb_about = wx.MenuItem(help_menu, wx.ID_ANY, '&About...\tCtrl+A')
        help_menu.Append(mb_about)

        menubar.Append(help_menu, '&Help')


        self.SetMenuBar(menubar)

        


        # Tool bar

        self.toolbar = self.CreateToolBar()

        tb_import = self.toolbar.AddTool(wx.ID_ADD, 'Import', wx.ArtProvider.GetBitmap(wx.ART_PLUS))

        self.Bind(wx.EVT_TOOL, self.on_import, tb_import)       

        self.toolbar.AddSeparator()

        tb_info = self.toolbar.AddTool(wx.ID_INFO, 'Info', wx.ArtProvider.GetBitmap(wx.ART_INFORMATION))

        self.toolbar.Realize()

        
        # Set main window

        self.SetTitle('TenTackle GUI')
        self.Centre()
        
    def on_quit(self, e):
        self.Close()

    def on_import(self, e):

        file_dialog = wx.FileDialog(self, "Open .csv", "", "", "Shimadzu raw data file (*.csv)|*.csv", wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)
        file_dialog.ShowModal()
        file_path = file_dialog.GetPath()
        file_dialog.Destroy()

        self.import_dialog.set_file_path(file_path)
        self.import_dialog.ShowModal()
        self.import_dialog.Destroy()


        


def main():

    app = wx.App()
    main_window = Main_window(None)
    main_window.Show()
    app.MainLoop()


if __name__ == '__main__':
    main()