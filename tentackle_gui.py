# -*- coding: utf-8 -*-
# TenTackle_GUI: Simple GUI for TenTackle

import os, sys, logging
import wx
import wx.lib.newevent
import numpy as np
import matplotlib
from matplotlib import pyplot as plt
# import ObjectListViewgit 

from main import Table, Curve_cache, config

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

        self.params = {
            'numbering': True,
            'fontsize': 12,
            'x_unit': config.get('axis').get('x_unit'),
            'y_unit': config.get('axis').get('y_unit'),
            'x_scaling': config['axis']['x_scaling'],
            'y_scaling': config['axis']['y_scaling'],
            'title': ''
        }

        if isinstance(kw.get('params'), dict):
            self.params.update(kw.get('params'))
            

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

    def draw(self, cache, table_id=None, selections = None):

        '''
            Draw curves on the figure.

            - table_id: `string`, a table id in cache, if table id is provided, then all curves in this table will be drawn.

            - cache: `Curve_cache`, a curve cache with all the curves
            - selection:  `list`, a list containing selection, format: [{table_id: table_id_1, batch: batch_1, curve: curve_1}, ...]. If selection is provided, table_id will be ignored.
        ''' 
        
        self.clear()


        self.ax.set_xlabel('Strain [%s]' % self.params['x_unit'], fontsize=self.params['fontsize'])
        self.ax.set_ylabel('Stress [%s]' % self.params['y_unit'], fontsize=self.params['fontsize'])
        self.ax.set_title = (self.params['title'])

        legend_list = []
        if selections:
            for selection in selections:
                table_id = selection['table_id']
                batch = selection['batch']
                subbatch = selection['subbatch']
                array = cache.get_curve(table_id, batch, subbatch)
                legend_text = cache.lut[table_id].table_name
                if self.params['numbering']:
                    legend_text = legend_text  + '-' + str(batch) + '-' +  str(subbatch)
                legend_list.append(legend_text)
                self.ax.plot(array[:, 1]/self.params['x_scaling'], array[:, 0]/self.params['y_scaling'])
        elif table_id:   # If no selections, go through the whole table specified by table_id
            for batch in cache.cached[table_id].keys():
                for subbatch in cache.cached[table_id][batch]:
                    array = cache.get_curve(table_id, batch, subbatch)
                    legend_text = cache.lut[table_id].table_name
                    if self.params['numbering']:
                        legend_text = legend_text  + '-' + str(batch) + '-' +  str(subbatch)
                    legend_list.append(legend_text)
                    self.ax.plot(array[:, 1]/self.params['x_scaling'], array[:, 0]/self.params['y_scaling'])
        else:   # If nothing was specified, draw everything in cache
            for table_id in cache.cached.keys():
                for batch in cache.cached[table_id].keys():
                    for subbatch in cache.cached[table_id][batch]:
                        array = cache.get_curve(table_id, batch, subbatch)
                        legend_text = cache.lut[table_id].table_name
                        if self.params['numbering']:
                            legend_text = legend_text  + '-' + str(batch) + '-' +  str(subbatch)
                        legend_list.append(legend_text)
                        self.ax.plot(array[:, 1]/self.params['x_scaling'], array[:, 0]/self.params['y_scaling'])

        # else:
        #     for index in selection:
        #         curve = curves_list[index]
        #         array = curve.get_data()
        #         legend_list.append(str(curve))
        #         self.ax.plot(array[:, 1]/config['axis']['x_scaling'], array[:, 0]/config['axis']['y_scaling'])

        
        
        # self.ax.legend(legend_list, bbox_to_anchor=(1.05,1), borderaxespad=0.)
        # Quick hack for auto placing the legend, but should be fixed in the future.
        self.ax.legend(legend_list)

        self.canvas.draw()
        self.Layout()

    def clear(self):

        '''
            Erase anything on the figure
        '''

        self.ax.clear()
        self.canvas.draw()

    def save(self, save_path):
        
        self.figure.savefig(save_path, dpi=300, bbox_inches='tight')

    def update_params(self, params):

        '''
            Change the parameters of the plot

            params: `dict`, dictionary of new parameters
        '''

        self.params.update(params)
        


class Console(wx.Panel):

    def __init__(self, *args, **kw):

        super(Console, self).__init__(*args, **kw)

        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.console_label = wx.StaticText(self, label = 'Console')
        self.main_sizer.Add(self.console_label, flag=wx.GROW)
        self.main_sizer.Add((0,10))
        self.console_text = wx.TextCtrl(self, size = (-1, 100), style = wx.TE_MULTILINE|wx.TE_RICH2|wx.TE_AUTO_URL)
        self.main_sizer.Add(self.console_text, flag=wx.GROW)

        self.SetSizer(self.main_sizer)
        self.Fit()
    
    def write(self, text, style = None):

        '''
            Append text to the console.

            text: str, message to be appended
            style: A wx.TextAttr() style
        '''

        if style != None:
            self.console_text.SetDefaultStyle(wx.TextAttr(style))
        self.console_text.AppendText(text)
        self.console_text.AppendText("\n--------------------\n")

        


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
        self.bottom_h_sizer.Add(self.ok_button, proportion = 1)


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
            self.cache.cache(self.table)

        # Cleanups 
        # self.cache.clear()
        self.list.DeleteAllItems()

        

        # Construct curve list for this single cache action
        # curve_list = {}
        # for index in indices:
        #     curve_list[index] = self.cache.cached[index]

        self.canvas_panel.draw(self.cache, table_id=self.table.id)

        list_position = 0  # A counter for setting list index
        for table_id, table_contents in self.cache.cached.items():
            table_name = self.cache.lut[table_id].table_name
            for batch, batch_contents in table_contents.items():
                for subbatch, truncation_point in batch_contents.items():
                    self.list.InsertItem(list_position, label = "%s %s %s" % (table_id, batch, subbatch))
                    self.list.SetItem(list_position, 1, table_name)
                    self.list.SetItem(list_position, 2, str(batch))
                    self.list.SetItem(list_position, 3, str(subbatch))
                    # self.list.SetItemPtrData(list_position, {
                    #     "table_id": table_id,
                    #     "batch": batch,
                    #     "subbatch": subbatch
                    # })
            list_position = list_position + 1
        

    def on_redraw_clicked(self, event):

        print("Redraw called")
        selection = self.get_selected()
        selections_list = self.translate_index(selection)
        self.canvas_panel.draw(self.cache, selections = selections_list)

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
            Convert position list to list of curve info
        '''

        info_list = []
        for position in position_list:
            info = {
                'table_id': self.list.GetItemText(position, col=0).split(' ')[0],
                'batch': int(self.list.GetItemText(position, col=0).split(' ')[1]),
                'subbatch': int(self.list.GetItemText(position, col=0).split(' ')[2])}
            print(info)
            info_list.append(info)

        return info_list

    def on_ok_clicked(self, event):

        '''
            On OK button clicked, revert the previous caching action, then cache the selected curves
        '''

        # Construct selection for Curve_cache.cache() for next caching action
        selected = self.translate_index(self.get_selected())    # List of selected curves
        selections = []  # Selection for Curve_cache.cache()
        for selection in selected:  # 
            selections.append((selection['batch'], selection['subbatch']))

        # Revert the previous action (made by self.set_file_path())
        self.cache.undo()

        # Cache selected curves
        self.cache.cache(self.table, selections = selections)

        self.EndModal(0)
        

class Plot_settings_dialog(wx.Dialog):

    def __init__(self, *args, **kw):

        super(Plot_settings_dialog, self).__init__(*args, **kw)

        panel = wx.Panel(self)
        # hbox = wx.BoxSizer(wx.HORIZONTAL)

        # self.listbox = wx.ListBox(panel)
        # hbox.Add(self.listbox, wx.ID_ANY, wx.EXPAND | wx.ALL, 20)

        # config_panel = wx.panel(panel)
        

        op_panel = wx.Panel(panel)
        op_panel_hbox = wx.BoxSizer(wx.HORIZONTAL)
        cancel_button = wx.Button(op_panel, wx.ID_ANY, 'Cancel', size=(90, 30))
        apply_button = wx.Button(op_panel, wx.ID_ANY, 'Apply', size=(90, 30))

        self.Bind(wx.EVT_BUTTON, self.on_cancel_clicked, id=cancel_button.GetId())
        self.Bind(wx.EVT_BUTTON, self.on_apply_clicked, id=apply_button.GetId())
        # self.Bind(wx.EVT_BUTTON, self.OnDelete, id=delBtn.GetId())
        # self.Bind(wx.EVT_BUTTON, self.OnClear, id=clrBtn.GetId())
        # self.Bind(wx.EVT_LISTBOX_DCLICK, self.OnRename)

        # op_panel_hbox.Add((-1, 20))
        op_panel_hbox.Add(cancel_button)
        op_panel_hbox.Add(apply_button)

        op_panel.SetSizer(op_panel_hbox)
        op_panel_hbox.Add(op_panel, 0.6, wx.EXPAND | wx.RIGHT, 20)

        self.SetTitle('wx.ListBox')

    def on_cancel_clicked():

        pass

    def on_apply_clicked():

        pass


    

class Main_window(wx.Frame):

    def __init__(self, *args, **kwargs):

        self.cache = kwargs.pop('cache')

        super(Main_window, self).__init__(*args, **kwargs)

        # self.history = History_manager()

        self.import_dialog = Import_dialog(self, style = wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER, cache = self.cache)

        self.init_ui()

        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.top_h_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.bottom_h_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.left_v_sizer = wx.BoxSizer(wx.VERTICAL)
        self.right_v_sizer = wx.BoxSizer(wx.VERTICAL)


        self.left_v_sizer.Add(wx.StaticText(self, label = 'Preview'), flag = wx.EXPAND)
        self.left_v_sizer.Add((0,10))
        canvas_limiter = wx.Panel(self, size = (800, 600))
        self.canvas = CanvasPanel(canvas_limiter)
        self.canvas.SetSize(wx.Size(800, 600))
        self.left_v_sizer.Add(canvas_limiter, flag = wx.EXPAND)
        self.left_v_sizer.Add((0,10))
        self.plot_settings_button = wx.Button(self, label = 'Plot/calculation settings', size=(120, 30))
        self.plot_settings_button.Bind(wx.EVT_BUTTON, self.on_plot_settings)
        self.left_v_sizer.Add(self.plot_settings_button, proportion = 1)
        self.left_v_sizer.Add((0,10))
        slider_sizer_w = wx.BoxSizer(wx.HORIZONTAL)
        slider_sizer_w.Add(wx.StaticText(self, label = 'Width', size=(50,-1)), proportion = 0, flag = wx.ALIGN_CENTER)
        self.width_slider = wx.Slider(self, name = 'width_slider', value=100)
        self.width_slider.Bind(wx.EVT_SLIDER, self.on_slider)
        slider_sizer_w.Add(self.width_slider, proportion = 1, flag = wx.EXPAND)
        self.w_indicator = wx.StaticText(self, label = '100%', size=(50,-1))
        slider_sizer_w.Add(self. w_indicator, proportion = 0, flag = wx.EXPAND)
        self.left_v_sizer.Add(slider_sizer_w, flag = wx.EXPAND)
        self.left_v_sizer.Add((0,10))
        slider_sizer_h = wx.BoxSizer(wx.HORIZONTAL)
        slider_sizer_h.Add(wx.StaticText(self, label = 'Height', size=(50,-1)), proportion = 0, flag = wx.ALIGN_CENTER)
        self.height_slider = wx.Slider(self, name = 'height_slider', value=100)
        self.height_slider.Bind(wx.EVT_SLIDER, self.on_slider)
        slider_sizer_h.Add(self.height_slider, proportion = 1, flag = wx.EXPAND)
        self.h_indicator = wx.StaticText(self, label = '100%', size=(50,-1))
        slider_sizer_h.Add(self. h_indicator, proportion = 0, flag = wx.EXPAND)
        self.left_v_sizer.Add(slider_sizer_h, flag = wx.EXPAND)
        

        
        self.right_v_sizer.Add(wx.StaticText(self, label = 'Selection'), flag = wx.GROW)
        self.right_v_sizer.Add((0,10))
        self.list = wx.ListCtrl(self, wx.ID_ANY, style = wx.LC_REPORT)
        self.list.InsertColumn(0, "Sample")
        self.list.InsertColumn(1, "Batch")
        self.list.InsertColumn(2, "Subbatch")
        self.list.InsertColumn(3, "Truncation%")
        self.right_v_sizer.Add(self.list, proportion = 1, flag = wx.GROW)


        
        self.console = Console(self)
        self.bottom_h_sizer.Add(self.console, proportion = 10, flag = wx.EXPAND|wx.ALL, border = 10)

        self.top_h_sizer.Add(self.left_v_sizer, flag = wx.EXPAND|wx.ALL, border = 10)
        self.top_h_sizer.Add(self.right_v_sizer, flag = wx.GROW|wx.ALL, border = 10)
        self.main_sizer.Add(self.top_h_sizer, flag = wx.EXPAND)
        self.main_sizer.Add(self.bottom_h_sizer, flag = wx.EXPAND)
        self.SetSizer(self.main_sizer)

        self.Fit()
        self.Centre()

        self.console.write("TenTackle pre-alpha - https://github.com/Proxy305/TenTackle")
        self.console.write("Standby.")

    def init_ui(self):

        # Menu bar

        menubar = wx.MenuBar()
        file_menu = wx.Menu()

        mb_open = wx.MenuItem(file_menu, wx.ID_ANY, '&Open project...\tCtrl+O')
        file_menu.Append(mb_open)
        self.Bind(wx.EVT_MENU, self.on_open, mb_open)

        self.mb_save = wx.MenuItem(file_menu, wx.ID_ANY, '&Save snapshot \tCtrl+S')
        file_menu.Append(self.mb_save)
        self.Bind(wx.EVT_MENU, self.on_save, self.mb_save)
        self.mb_save.Enable(False)

        self.mb_save_as = wx.MenuItem(file_menu, wx.ID_SAVEAS, '&Save snapshot as ...\tCtrl+S')
        file_menu.Append(self.mb_save_as)
        self.Bind(wx.EVT_MENU, self.on_save, self.mb_save_as)

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

        tb_redo = self.toolbar.AddTool(wx.ID_REDO, 'Redo', wx.ArtProvider.GetBitmap(wx.ART_REDO))
        self.Bind(wx.EVT_TOOL, self.on_redo, tb_redo)

        tb_clear = self.toolbar.AddTool(wx.ID_REVERT, 'Clear', wx.ArtProvider.GetBitmap(wx.ART_DELETE))
        self.Bind(wx.EVT_TOOL, self.on_clear, tb_clear) 

        self.toolbar.AddSeparator() 

        tb_info = self.toolbar.AddTool(wx.ID_INFO, 'Info', wx.ArtProvider.GetBitmap(wx.ART_REPORT_VIEW))
        self.Bind(wx.EVT_TOOL, self.on_info, tb_info)

        tb_save_img = self.toolbar.AddTool(wx.ID_PRINT, 'Save image', wx.ArtProvider.GetBitmap(wx.ART_PRINT))
        self.Bind(wx.EVT_TOOL, self.on_save_image, tb_save_img)

        self.toolbar.AddSeparator()

        tb_write_notes = self.toolbar.AddTool(wx.ID_EDIT, 'Write text notes', wx.ArtProvider.GetBitmap(wx.ART_INFORMATION))
        self.Bind(wx.EVT_TOOL, self.on_write_notes, tb_write_notes)


        self.toolbar.Realize()

        
        # Set main window

        self.SetTitle('TenTackle GUI')

    def update_listbox(self):

        self.list.DeleteAllItems()

        list_position = 0
        for table_id, table_contents in self.cache.cached.items():
            table_name = self.cache.lut[table_id].table_name
            for batch, batch_contents in table_contents.items():
                for subbatch, truncation_point in batch_contents.items():
                    self.list.InsertItem(list_position, table_name)
                    self.list.SetItem(list_position, 1, str(batch))
                    self.list.SetItem(list_position, 2, str(subbatch))
                    self.list.SetItem(list_position, 3, str(0))
                    list_position = list_position + 1  
        
        
    def on_quit(self, e):
        self.Close()

    def on_import(self, e):

        # Get the file to be opened

        file_dialog = wx.FileDialog(self, "Open .csv", "", "", "Shimadzu raw data file (*.csv)|*.csv", wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)
        dialog_status = file_dialog.ShowModal()
        file_path = file_dialog.GetPath()
        file_dialog.Destroy()

        if dialog_status == wx.ID_CANCEL:
            return

        # Set up the import dialog, and then open the dialog
        # The import dialog was not destroyed and kepted for next use

        self.import_dialog.set_file_path(file_path)
        status = self.import_dialog.ShowModal()

        # If the import dialog was closed by "OK", which means selection has been done
        if status == 0:
            print(self.cache)
            self.canvas.draw(self.cache)

            # Write curve info to listbox
            self.update_listbox()
            
            working_file_path = self.cache.working_snapshot_file
            if working_file_path != None:
                # If an active file has been set
                self.mb_save.Enable(True)  # Enable "save" menubar item
                self.SetTitle('TenTackle GUI - ' + working_file_path + '*')
            else:
                self.SetTitle('TenTackle GUI - *')

    
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
            result_str = '''Analysis result for curves in main cache:
            YM: %.3f\u00b1%.3f %s
            UTS: %.3f\u00b1%.3f %s
            Elongation at max stress: %.3f\u00b1%.3f
            Elongation at break: %.3f\u00b1%.3f
            Toughness: %.3f\u00b1%.3f %s'''% (
                result_dict['ym']['value'], result_dict['ym']['std'], result_dict['ym']['unit'], result_dict['uts']['value'], result_dict['uts']['std'], result_dict['uts']['unit'], result_dict['sams']['value'], result_dict['sams']['std'], result_dict['sab']['value'], result_dict['sab']['std'], result_dict['toughness']['value'], result_dict['toughness']['std'], result_dict['toughness']['unit'])
            self.console.write(result_str)
        else:
            wx.MessageBox("No curve has been cached!", "Error", wx.OK | wx.ICON_EXCLAMATION)

    def on_clear(self, e):

        reply = wx.MessageBox('Do you really want to clear all curves in cache?', "Warning", wx.CANCEL | wx.CANCEL_DEFAULT | wx.ICON_EXCLAMATION)

        if reply == wx.OK:

            self.cache.clear()
            self.canvas.clear()
            self.update_listbox()

            working_file_path = self.cache.working_snapshot_file
            if working_file_path != None:
                # If an active file has been set
                self.mb_save.Enable(True)  # Enable "save" menubar item
                self.SetTitle('TenTackle GUI - ' + working_file_path + '*')
            else:
                self.SetTitle('TenTackle GUI - *')


    def on_open(self, e):

        file_path = ''
        file_dialog = wx.FileDialog(self, "Open snapshot .json", "", "", "Snapshot json (*.json)|*.json", wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)
        dialog_status = file_dialog.ShowModal()
        file_path = file_dialog.GetPath()
        file_dialog.Destroy()

        if dialog_status == wx.ID_CANCEL:
            return

        result = self.cache.restore_snapshot(file_path = file_path)
        if result != -1:

            if result == -2:
                # It the current history stack is not empty, ask user what to do
                reply = wx.MessageBox('The current cache is not empty!\n All unsaved data will be lost if another file is loaded.\n Press OK if you still wish to proceed.', "Warning", wx.CANCEL | wx.CANCEL_DEFAULT | wx.ICON_EXCLAMATION)
                self.cache.restore_snapshot(file_path = file_path, force = True)
            elif result == -3:
                wx.MessageBox('You have just loaded a JSON snapshot file ', "Warning", wx.OK)

            # If no error at all

            self.canvas.update_params({"numbering": False}) # Workaround 2021/12/27
            self.canvas.draw(self.cache)
            self.update_listbox()

            # Set window title
            self.SetTitle('TenTackle GUI - ' + file_path)

            # Disable "save" menubar item
            self.mb_save.Enable(False)
        else:
            wx.MessageBox('Error occured opening file.', "Warning", wx.OK | wx.ICON_EXCLAMATION)


    def on_save(self, e):

        file_path = None

        # To find out who is calling, save or save as?
        if e.GetId() == wx.ID_SAVEAS:      
            # If the caller is save as, then ask user where to save
            file_dialog = wx.FileDialog(self, "Save snapshot", "", "", "TenTackle snapshot (*.json)|*.json", wx.FD_SAVE)
            dialog_status = file_dialog.ShowModal()
            file_path = file_dialog.GetPath()
            file_dialog.Destroy()
            if dialog_status == wx.ID_CANCEL:
                return

        result = self.cache.take_snapshot(file_path = file_path)
        if result == -1:
            wx.MessageBox('Error occured during saving to file.', "Warning", wx.OK | wx.ICON_EXCLAMATION)

        # Get the save path, then update title bar
        self.SetTitle('TenTackle GUI - ' + self.cache.working_snapshot_file)

        # Disable "save" menubar item
        self.mb_save.Enable(False)

    def on_undo(self, e):
        
        result = self.cache.undo()
        self.canvas.draw(self.cache.cached, self.cache.lut)
        self.update_listbox()

        working_file_path = self.cache.working_snapshot_file
        if self.cache.modified == True:
            # If the cache is in a modified stage, unlock save function and rewrite title bar to indicate change has been made
            
            if working_file_path != None:
                self.mb_save.Enable(True)  # Enable "save" menubar item
                self.SetTitle('TenTackle GUI - ' + working_file_path + '*')
            else:
                self.SetTitle('TenTackle GUI - *')
        else:
            self.SetTitle('TenTackle GUI - ' + working_file_path)
            

    def on_redo(self, e):
        
        result = self.cache.redo()
        self.canvas.draw(self.cache.cached, self.cache.lut)
        self.update_listbox()

        working_file_path = self.cache.working_snapshot_file
        if self.cache.modified == True:
            # If the cache is in a modified stage, unlock save function and rewrite title bar to indicate change has been made
            
            if working_file_path != None:
                self.mb_save.Enable(True)  # Enable "save" menubar item
                self.SetTitle('TenTackle GUI - ' + working_file_path + '*')
            else:
                self.SetTitle('TenTackle GUI - *')
        else:
            self.SetTitle('TenTackle GUI - ' + working_file_path)

    def on_save_image(self, e):

        file_path = None

        file_dialog = wx.FileDialog(self, "Save image", "", "", "Image (*.png)|*.png", wx.FD_SAVE)
        dialog_status = file_dialog.ShowModal()
        file_path = file_dialog.GetPath()
        file_dialog.Destroy()
        if dialog_status == wx.ID_CANCEL:
            return
        print(file_path)

        self.canvas.save(file_path)

    def on_write_notes(self, e):

        pass

    def on_plot_settings(self, e):

        plot_settings_dialog = Plot_settings_dialog(self, style = wx.DEFAULT_DIALOG_STYLE)
        dialog_status = plot_settings_dialog.ShowModal()
        # plot_settings_dialog.destroy()



def main():

    main_cache = Curve_cache()
    plot_settings = {}

    app = wx.App()
    main_window = Main_window(None, cache = main_cache)
    main_window.Show()
    app.MainLoop()


if __name__ == '__main__':
    main()