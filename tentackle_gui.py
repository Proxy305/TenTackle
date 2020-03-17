# -*- coding: utf-8 -*-
# TenTackle_GUI: Simple GUI for TenTackle

import os, sys, logging
import wx
import wx.lib.newevent
import numpy as np
import matplotlib
# import ObjectListViewgit 

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
        # self.ax = self.figure.add_axes([0, 0 ,1 ,1])
        self.ax.axis(xmin=0, ymin=0)
        self.canvas = FigureCanvasWxAgg(self, wx.ID_ANY, self.figure)



        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.canvas, proportion=1, flag=wx.LEFT | wx.TOP | wx.GROW)
        # self.sizer.Add(self.slider, proportion=0, flag=wx.LEFT | wx.TOP | wx.GROW)
        self.SetSizer(self.sizer)
        self.Fit()
        

        box = self.ax.get_position()
        self.ax.set_position([box.x0, box.y0, box.width*0.65, box.height])

    # def OnSlider(self, event):
    #     self.draw()

    def draw(self, curves_list, selection = None):

        '''
            curves_list: Dictionary {int index: Curve() curve}
            selection: List of curve indices
        ''' 
        
        self.clear()


        self.ax.set_xlabel('Strain [%s]' % config.get('axis').get('x_unit'), fontsize=12)
        self.ax.set_ylabel('Stress [%s]' % config.get('axis').get('y_unit'), fontsize=12)
        self.ax.set_title = ("Strain")

        legend_list = []
        if selection == None:
            for index, curve in curves_list.items():
                array = curve.get_data()
                legend_list.append(str(curve))
                self.ax.plot(array[:, 1]/config['axis']['x_scaling'], array[:, 0]/config['axis']['y_scaling'])
        else:
            for index in selection:
                curve = curves_list[index]
                array = curve.get_data()
                legend_list.append(str(curve))
                self.ax.plot(array[:, 1]/config['axis']['x_scaling'], array[:, 0]/config['axis']['y_scaling'])

        
        
        self.ax.legend(legend_list, bbox_to_anchor=(1.05,1), borderaxespad=0.)

        self.canvas.draw()
        self.Layout()

    def clear(self):

        '''
            Erase anything on the figure
        '''

        self.ax.clear()
        self.canvas.draw()

class Import_dialog(wx.Dialog):

    def __init__(self, *args, **kw):

        self.cache = kw.pop('cache')

        super(Import_dialog, self).__init__(*args, **kw)

        self.SetTitle('Import')

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
        
        self.file_path = file_path
        if os.path.isfile(file_path):
            self.table = Table(file_path)
            indices = self.cache.cache(self.table)

        # Cleanups 
        # self.cache.clear()
        self.list.DeleteAllItems()

        

        # Construct curve list for this single cache action
        curve_list = {}
        for index in indices:
            curve_list[index] = self.cache.cached[index]

        self.canvas_panel.draw(curve_list)

        list_position = 0  # A counter for setting list index
        for curve_index, curve in curve_list.items():
            self.list.InsertItem(list_position, str(curve_index))
            self.list.SetItem(list_position, 1, str(curve.table))
            self.list.SetItem(list_position, 2, str(curve.batch))
            self.list.SetItem(list_position, 3, str(curve.subbatch))
            self.list.SetItemData(list_position, curve_index)
            list_position = list_position + 1
        

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

        '''
            On OK button clicked, revert the previous caching action, then cache the selected curves
        '''

        # Construct selection for Curve_cache.cache() for next caching action
        selected = self.translate_index(self.get_selected())    # List of selected curves
        selections = []  # Selection for Curve_cache.cache()
        for index in selected:  # 
            curve = self.cache.cached[index]
            selections.append((curve.batch, curve.subbatch))

        # Revert the previous action (made by self.set_file_path())
        self.cache.revert(self.table.file_name)

        # Cache selected curves
        self.cache.cache(self.table, selections = selections)

        self.EndModal(0)
        

    

class Main_window(wx.Frame):

    def __init__(self, *args, **kwargs):

        self.cache = kwargs.pop('cache')

        super(Main_window, self).__init__(*args, **kwargs)

        # self.history = History_manager()

        self.import_dialog = Import_dialog(self, style = wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER, cache = self.cache)

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
        self.width_slider = wx.Slider(self, name = 'width_slider', value=100)
        self.width_slider.Bind(wx.EVT_SLIDER, self.on_slider)
        slider_sizer_w.Add(self.width_slider, proportion = 1, flag = wx.EXPAND)
        self.w_indicator = wx.StaticText(self, label = '100%', size=(50,-1))
        slider_sizer_w.Add(self. w_indicator, proportion = 0, flag = wx.EXPAND)
        self.left_v_sizer.Add(slider_sizer_w, flag = wx.EXPAND)
        self.left_v_sizer.Add((0,10))
        slider_sizer_h = wx.BoxSizer(wx.HORIZONTAL)
        slider_sizer_h.Add(wx.StaticText(self, label = 'Height', size=(50,-1)), proportion = 0, flag = wx.EXPAND|wx.ALIGN_CENTER)
        self.height_slider = wx.Slider(self, name = 'height_slider', value=100)
        self.height_slider.Bind(wx.EVT_SLIDER, self.on_slider)
        slider_sizer_h.Add(self.height_slider, proportion = 1, flag = wx.EXPAND)
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
        self.list.InsertColumn(4, "Truncation%")
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
        self.Bind(wx.EVT_MENU, self.on_save, mb_save)

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

        tb_undo = self.toolbar.AddTool(wx.ID_UNDO, 'Undo', wx.ArtProvider.GetBitmap(wx.ART_UNDO))
        self.Bind(wx.EVT_TOOL, self.on_undo, tb_undo)

        tb_redo = self.toolbar.AddTool(wx.ID_REDO, 'Undo', wx.ArtProvider.GetBitmap(wx.ART_REDO))
        self.Bind(wx.EVT_TOOL, self.on_redo, tb_redo)

        self.toolbar.AddSeparator() 


        tb_clear = self.toolbar.AddTool(wx.ID_CLEAR, 'Clear', wx.ArtProvider.GetBitmap(wx.ART_DELETE))
        self.Bind(wx.EVT_TOOL, self.on_clear, tb_clear)   

        tb_info = self.toolbar.AddTool(wx.ID_INFO, 'Info', wx.ArtProvider.GetBitmap(wx.ART_INFORMATION))
        self.Bind(wx.EVT_TOOL, self.on_info, tb_info)

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
        status = self.import_dialog.ShowModal()

        # self.import_dialog.Destroy()

        if status == 0:

            self.canvas.draw(self.cache.cached)

            # Writr curve info to listbox
            list_position = 0
            for curve_index, curve in self.cache.cached.items():
                self.list.InsertItem(list_position, str(curve_index))
                self.list.SetItem(list_position, 1, str(curve.table))
                self.list.SetItem(list_position, 2, str(curve.batch))
                self.list.SetItem(list_position, 3, str(curve.subbatch))
                self.list.SetItem(list_position, 4, str(0))
                self.list.SetItemData(list_position, curve_index)
                list_position = list_position + 1  
    
    def on_slider(self, event):
        height_value = self.height_slider.GetValue()
        width_value = self.width_slider.GetValue()

        height = height_value * 6
        width = width_value * 8

        self.canvas.SetSize(wx.Size(width, height))

        self.w_indicator.SetLabel(str(width_value) + '%')
        self.h_indicator.SetLabel(str(height_value) + '%')
        

    def on_info(self, e):

        result_dict = self.cache.analyze()
        if result_dict != 0:
            result_str = "YM: %.3f\u00b1%.3f\n UTS: %.3f\u00b1%.3f\n E: %.3f\u00b1%.3f\n" % (result_dict['ym']['value'], result_dict['ym']['std'], result_dict['uts']['value'], result_dict['uts']['std'], result_dict['sams']['value'], result_dict['sams']['std'])
            wx.MessageBox(result_str, "Analysis results", wx.OK | wx.ICON_EXCLAMATION)
        else:
            wx.MessageBox("No curve has been cached!", "Error", wx.OK | wx.ICON_EXCLAMATION)

    def on_clear(self, e):

        reply = wx.MessageBox('Do you really want to clear all curves in cache?', "Warning", wx.CANCEL | wx.CANCEL_DEFAULT | wx.ICON_EXCLAMATION)

        if reply == wx.OK:

            self.cache.clear()
            self.canvas.clear()
            self.list.DeleteAllItems()

    def on_save(self, e):

        file_path = self.cache.take_snapshot()
        if file_path == 0:
            wx.MessageBox('Error occured during saving to file.', "Warning", wx.OK | wx.ICON_EXCLAMATION)

    def on_undo(self, e):
        
        self.cache.undo()
        self.canvas.draw(self.cache.cached)

    def on_redo(self, e):
        
        self.cache.redo()



def main():

    main_cache = Curve_cache()

    app = wx.App()
    main_window = Main_window(None, cache = main_cache)
    main_window.Show()
    app.MainLoop()


if __name__ == '__main__':
    main()