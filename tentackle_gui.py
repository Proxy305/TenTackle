# -*- coding: utf-8 -*-
# TenTackle_GUI: Simple GUI for TenTackle

import os, sys
import wx
import numpy as np
import matplotlib
import ObjectListView

from main import Table, Curve, Curve_cache, config

matplotlib.interactive(False)
matplotlib.use("WXAgg")
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg
from matplotlib.backends.backend_wx import NavigationToolbar2Wx
from matplotlib.figure import Figure


class CanvasPanel(wx.Panel):
    def __init__(self, *args, **kw):

        super(CanvasPanel, self).__init__(*args, **kw)
        
        # self.slider = wx.Slider(self, -1, value=1, minValue=0, maxValue=11)
        # self.slider.Bind(wx.EVT_SLIDER, self.OnSlider)

        self.figure = Figure()
        self.ax = self.figure.add_axes([0.1, 0.15, 0.8, 0.8])
        self.ax.axis(xmin=0, ymin=0)
        # self.ax.set_title(ylabel = 'Stress [%s]' % config.get('axis').get('y_unit'), xlabel = 'Strain [%s]' % config.get('axis').get('x_unit'))
        self.canvas = FigureCanvasWxAgg(self, wx.ID_ANY, self.figure)



        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.canvas, proportion=1, flag=wx.LEFT | wx.TOP | wx.GROW)
        # self.sizer.Add(self.slider, proportion=0, flag=wx.LEFT | wx.TOP | wx.GROW)
        self.SetSizer(self.sizer)
        self.Fit()
        

    # def OnSlider(self, event):
    #     self.draw()

    def draw(self, curves_list):
        
        self.ax.clear()
        self.ax.set_xlabel("2013", fontsize=12)
        self.ax.set_title = ("Strain")
        for curve in curves_list:
            array = curve.get_data()
            self.ax.plot(array[:, 1]/config['axis']['x_scaling'], array[:, 0]/config['axis']['y_scaling'])
        self.canvas.draw()
        self.Layout()


class Import_dialog(wx.Dialog):

    def __init__(self, *args, **kw):

        super(Import_dialog, self).__init__(*args, **kw)

        self.SetTitle('Import')

        self.cache = Curve_cache()
        self.table = None
        self.file_path = None
        
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.top_h_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.bottom_h_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.left_v_sizer = wx.BoxSizer(wx.VERTICAL)
        self.right_v_sizer = wx.BoxSizer(wx.VERTICAL)

        self.canvas_label = wx.StaticText(self, label = 'Preview')
        self.left_v_sizer.Add(self.canvas_label)
        self.left_v_sizer.Add((0,10))    
        self.canvas_panel = CanvasPanel(self)
        self.left_v_sizer.Add(self.canvas_panel)
        self.top_h_sizer.Add(self.left_v_sizer, proportion = 0, flag = wx.EXPAND|wx.ALL, border = 10)

        self.selection_label = wx.StaticText(self, label = 'Selection')
        self.right_v_sizer.Add(self.selection_label, proportion = 0, flag = wx.EXPAND)
        self.right_v_sizer.Add((0,10))
        self.list = wx.ListCtrl(self, wx.ID_ANY, style = wx.LC_REPORT)
        # self.list.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_select)
        self.list.InsertColumn(0, "Index")
        self.list.InsertColumn(1, "Sample")
        self.list.InsertColumn(2, "Batch")
        self.list.InsertColumn(3, "Subbatch")
        self.right_v_sizer.Add(self.list, proportion = 1, flag = wx.EXPAND)
        self.right_v_sizer.Add((0,10))
        self.redraw_button = wx.Button(self, label = 'Redraw')
        self.redraw_button.Bind(wx.EVT_BUTTON, self.on_redraw_clicked)
        self.right_v_sizer.Add(self.redraw_button, proportion = 0, flag = wx.EXPAND)
        self.top_h_sizer.Add(self.right_v_sizer, flag = wx.EXPAND|wx.ALL, border = 10)
     

        self.button = wx.Button(self, label = 'OK', size=(70, 30))
        self.bottom_h_sizer.Add(self.button, proportion = 1, flag = wx.ALIGN_RIGHT)


        self.main_sizer.Add(self.top_h_sizer)
        self.main_sizer.Add(self.bottom_h_sizer, flag = wx.ALL, border = 10)


        self.SetSizer(self.main_sizer)
        self.Center()
        self.init_ui()
        
        

    def init_ui(self):

        # panel = wx.Panel(self)
        # h_box = wx.BoxSizer(wx.HORIZONTAL)
        # button = wx.Button(panel, label='label')
        
        # print(self.file_path)
        self.Fit()
    
        # self.SetSize((350, 250))

    def set_file_path(self, file_path):
        
        # self.file_path = file_path
        # if os.path.isfile(file_path):
        #     self.table = Table(file_path)
        #     self.cache.cache(self.table)

        self.table = Table('./test.csv')
        self.cache.cache(self.table)

        self.canvas_panel.draw(self.cache.cached)

        index = 0
        for curve in self.cache.cached:
            self.list.InsertItem(index, str(index))
            self.list.SetItem(index, 1, str(curve.table))
            self.list.SetItem(index, 2, str(curve.batch))
            self.list.SetItem(index, 3, str(curve.subbatch))
            index = index + 1

    def on_redraw_clicked(self, event):

        print("on select")

        selection = self.get_selected()
        print(selection)

    def get_selected(self):

        count = self.list.GetFirstSelected()
        selected = []
        selected.append(count)
        while True:
            next_selection = self.list.GetNextSelected(count)
            if next_selection == -1:
                return selected
            print("next")
            print(next_selection)
            selected.append(next_selection)  
            count = next_selection


class Main_window(wx.Frame):

    def __init__(self, *args, **kwargs):
        super(Main_window, self).__init__(*args, **kwargs)

        self.import_dialog = Import_dialog(self, style = wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)

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

        # file_dialog = wx.FileDialog(self, "Open .csv", "", "", "Shimadzu raw data file (*.csv)|*.csv", wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)
        # file_dialog.ShowModal()
        # file_path = file_dialog.GetPath()
        # file_dialog.Destroy()

        self.import_dialog.set_file_path('file_path')
        self.import_dialog.ShowModal()
        self.import_dialog.Destroy()


        


def main():

    app = wx.App()
    main_window = Main_window(None)
    main_window.Show()
    app.MainLoop()


if __name__ == '__main__':
    main()