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
        self.canvas = FigureCanvasWxAgg(self, wx.ID_ANY, self.figure)



        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.canvas, proportion=1, flag=wx.LEFT | wx.TOP | wx.GROW)
        # self.sizer.Add(self.slider, proportion=0, flag=wx.LEFT | wx.TOP | wx.GROW)
        self.SetSizer(self.sizer)
        self.Fit()
        

    # def OnSlider(self, event):
    #     self.draw()

    def draw(self, curves_list, selection = None):

        '''
            curves_list: Dictionary {int index: Curve() curve}
            selection: List of curve indices
        ''' 
        
        self.ax.clear()
        self.ax.set_xlabel('Strain [%s]' % config.get('axis').get('x_unit'), fontsize=12)
        self.ax.set_ylabel('Stress [%s]' % config.get('axis').get('y_unit'), fontsize=12)
        self.ax.set_title = ("Strain")
        if selection == None:
            for index, curve in curves_list.items():
                array = curve.get_data()
                self.ax.plot(array[:, 1]/config['axis']['x_scaling'], array[:, 0]/config['axis']['y_scaling'])
        else:
            for index in selection:
                curve = curves_list[index]
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
     

        self.ok_button = wx.Button(self, label = 'OK', size=(70, 30))
        self.ok_button.Bind(wx.EVT_BUTTON, self.on_ok_clicked)
        self.bottom_h_sizer.Add(self.ok_button, proportion = 1, flag = wx.ALIGN_RIGHT)


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

        # Cleanups 
        self.cache.clear()
        self.list.DeleteAllItems()

        self.table = Table('./test.csv')
        self.cache.cache(self.table)

        self.canvas_panel.draw(self.cache.cached)

        list_postion = 0  # A counter for setting list index
        for curve_index, curve in self.cache.cached.items():
            self.list.InsertItem(list_postion, str(curve_index))
            self.list.SetItem(list_postion, 1, str(curve.table))
            self.list.SetItem(list_postion, 2, str(curve.batch))
            self.list.SetItem(list_postion, 3, str(curve.subbatch))
            self.list.SetItemData(list_postion, curve_index)
            list_postion = list_postion + 1
        

    def on_redraw_clicked(self, event):

        print("Redraw called")
        selection = self.get_selected()
        index_list = self.translate_index(selection)
        self.canvas_panel.draw(self.cache.cached, selection = index_list)

    def get_selected(self):

        count = self.list.GetFirstSelected()
        selected = []
        selected.append(count)
        while True:
            next_selection = self.list.GetNextSelected(count)
            if next_selection == -1:
                return selected
            selected.append(next_selection)  
            count = next_selection

    def translate_index(self, position_list):

        '''
            Convert position list to curve index list
        '''

        index_list = []
        for position in position_list:
            index_list.append(self.list.GetItemData(position))

        return index_list

    def on_ok_clicked(self, event):
        self.EndModal(0)
        
    

class Main_window(wx.Frame):

    def __init__(self, *args, **kwargs):
        super(Main_window, self).__init__(*args, **kwargs)

        self.import_dialog = Import_dialog(self, style = wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)

        self.init_ui()

        self.main_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.left_v_sizer = wx.BoxSizer(wx.VERTICAL)
        self.right_v_sizer = wx.BoxSizer(wx.VERTICAL)


        self.left_v_sizer.Add(wx.StaticText(self, label = 'Preview'), flag = wx.EXPAND)
        self.left_v_sizer.Add((0,10))
        canvas_limiter = wx.Panel(self, size = (800, 600))
        self.canvas = CanvasPanel(canvas_limiter)
        self.canvas.SetSize(wx.Size(800, 600))
        self.left_v_sizer.Add(canvas_limiter, flag = wx.EXPAND)
        self.left_v_sizer.Add((0,10))
        slider_sizer_w = wx.BoxSizer(wx.HORIZONTAL)
        slider_sizer_w.Add(wx.StaticText(self, label = 'Width', size=(50,-1)), proportion = 0, flag = wx.EXPAND|wx.ALIGN_CENTER)
        width_slider = wx.Slider(self, name = 'width_slider', value=100)
        slider_sizer_w.Add(width_slider, proportion = 1, flag = wx.EXPAND)
        self.w_indicator = wx.StaticText(self, label = '100%', size=(50,-1))
        slider_sizer_w.Add(self. w_indicator, proportion = 0, flag = wx.EXPAND)
        self.left_v_sizer.Add(slider_sizer_w, flag = wx.EXPAND)
        self.left_v_sizer.Add((0,10))
        slider_sizer_h = wx.BoxSizer(wx.HORIZONTAL)
        slider_sizer_h.Add(wx.StaticText(self, label = 'Height', size=(50,-1)), proportion = 0, flag = wx.EXPAND|wx.ALIGN_CENTER)
        height_slider = wx.Slider(self, name = 'height_slider', value=100)
        slider_sizer_h.Add(height_slider, proportion = 1, flag = wx.EXPAND)
        self.h_indicator = wx.StaticText(self, label = '100%', size=(50,-1))
        slider_sizer_h.Add(self. h_indicator, proportion = 0, flag = wx.EXPAND)
        self.left_v_sizer.Add(slider_sizer_h, flag = wx.EXPAND)
        

        
        self.right_v_sizer.Add(wx.StaticText(self, label = 'Selection'), flag = wx.EXPAND)
        self.right_v_sizer.Add((0,10))
        self.list = wx.ListCtrl(self, wx.ID_ANY, style = wx.LC_REPORT)
        self.list.InsertColumn(0, "Index")
        self.list.InsertColumn(1, "Sample")
        self.list.InsertColumn(2, "Batch")
        self.list.InsertColumn(3, "Subbatch")
        self.list.InsertColumn(5, "Truncation%")
        self.right_v_sizer.Add(self.list, proportion = 1, flag = wx.EXPAND)

        self.main_sizer.Add(self.left_v_sizer, flag = wx.EXPAND|wx.ALL, border = 10)
        self.main_sizer.Add(self.right_v_sizer, flag = wx.EXPAND|wx.ALL, border = 10)
        self.SetSizer(self.main_sizer)

        self.Fit()
        self.Centre()

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
        
        
    def on_quit(self, e):
        self.Close()

    def on_import(self, e):

        file_dialog = wx.FileDialog(self, "Open .csv", "", "", "Shimadzu raw data file (*.csv)|*.csv", wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)
        file_dialog.ShowModal()
        file_path = file_dialog.GetPath()
        file_dialog.Destroy()

        self.import_dialog.set_file_path(file_path)
        self.import_dialog.ShowModal()
        # self.import_dialog.Destroy()


        


def main():

    app = wx.App()
    main_window = Main_window(None)
    main_window.Show()
    app.MainLoop()


if __name__ == '__main__':
    main()