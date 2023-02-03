# -*- coding: utf-8 -*-
# TenTackle: Tensile data analysis assistance tool for Shimazu

import os,sys
import csv
import logging
import argparse
import numpy as np
import matplotlib.pyplot as plt
import math
import json
import uuid
from enum import Enum

# Read config file
config = {}

if os.path.isfile("config.json"):

    '''
    Use external config first
    '''
    with open("config.json") as config_file:
        config = json.load(config_file)
else:

    '''
    If external config not found, fallback to embedded config
    '''

    config = {
        "axis":{
            "y_unit": "MPa",
            "y_scaling": 1,
            "x_unit": "",
            "x_scaling": 1
        },
        "font":{
            "family" : "Monospace",
            "weight" : "bold",
            "size"   : 12
        },
        "regression":{
            "start": 0.001,
            "end": 0.01           
        },
        "integration":{
            "method": "simps"
        }
    }

# Helper functions: functions that accepts a procecced stress/strain data array
def calculate(array, dimensions):  
    '''
    Calculate stress/strain records of a given sample
    '''
    # Calculate stress/strain value
    array[:, 0] /= (dimensions[0] * dimensions[1])
    array[:, 1] /= dimensions[2]

    return array 

def truncate_at(array, percentage):
    
    '''
    Truncates array at specified percentage
    '''

    truncated_len = math.ceil(len(array) * (percentage/100))

    return array[0:truncated_len, :]

def linear_regression(array, from_to = (0, 0)):

    '''
    Linear regression helper function, for finding slopes

    array: np_array, data source of linear regression
    from_to: tuple, (from_x_equals_to_value, to_x_equals_to_value)
        Example: (0.1, 0.2) means select a part of the array from x=0.1 to x=0.2, and calculate linear regression for this part.
    '''

    range = from_to
    if from_to != [0, 0]:
        # If from_to has been modified
        range = (config['regression']['start'], config['regression']['end'])

    start_idx = idx_of_nearest(array[:, 1], range[0])
    end_idx = idx_of_nearest(array[:, 1], range[1])
    print(range)

    # logger.debug("From, to: %d, %d" % (start_idx, end_idx))

    measure_area = array[start_idx:end_idx, :]
    x = measure_area[:, 1]
    y = measure_area[:, 0]

    slope = (len(x) * np.sum(x*y) - np.sum(x) * np.sum(y)) / (len(x)*np.sum(x*x) - np.sum(x) ** 2)
    intercept = (np.sum(y) - slope *np.sum(x)) / len(x)

    return slope, intercept

def max_stress(array):

    '''
    Find maximum stress in a stress/strain array

    Return value: tuple, (max_stress, strain_at_max_stress)
    '''
    
    max_stress = np.amax(array[:, 0])
    index_at_max_stress = np.argmax(array[:, 0])
    strain_at_max_stress = array[index_at_max_stress, 1]
    return max_stress, strain_at_max_stress

def strain_at_break(array):

    '''
    Find strain at break, the strain value of the last point of the curve

    Return value: number, strain_at_break
    '''
    
    strain_at_break = np.amax(array[:, 1])

    return strain_at_break



def idx_of_nearest(array_1d, target):

    '''
    Find the index of value nearest to target in a 1d array.
    Only 1d array should be given as param; otherwise would not give correct result
    '''

    return (np.abs(array_1d - target)).argmin()

def integrate_x(array):

    '''
    Integration of an array at x direction using np.trapz().

    - array: an 2d array with x and y values.
    '''

    array_x = array[:, 1]
    array_y = array[:, 0]

    try:
        return np.trapz(array_y, array_x)
    except Exception as e:
        print(e)

# Machine types
class MachineType(Enum):
    EZ = 0  # Shimadzu EZ series
    AGSX = -1 # Shimadzu AGS-X series

# Data structures
class Table:

    '''
    Structure for reading and keeping raw data from a single .csv file of Shimadzu EZ and AGS-X series
    '''

    def __init__(self, filename, tablename = ''):

        super().__init__()
        
        self.tables = []    # Keeps all table raw infomation
        self._file_name = filename

        # Set logger
        self.logger = logger

        # Set unique identifier for itself
        self.table_id = uuid.uuid1()

        # Split multiple tables in single .csv file
        with open(filename, newline='', encoding='Shift-JIS') as f:
            reader = csv.reader(f)

            temp_table = []

            for row in reader:
                if row != []:
                    temp_table.append(row)
                else:
                    self.tables.append(temp_table)
                    temp_table = []

        # Define table name, if not specified manually
        if tablename == '':
            self._table_name = str.split(str.split(filename, '/')[-1], '.')[-2]
        else:
            self._table_name = tablename

        # Detect intrument type from job file extension
        self.base_shift_value = 0    # Relative position of contents are different in Shimazu EZ and AGS-X series files are different
        self.machine_type = MachineType.EZ
        if str.split(self.tables[0][1][0], '.')[-1] == "tai":
            self.logger.debug("Shimadzu EZ series")
        elif str.split(self.tables[0][1][0], '.')[-1] == "xtas":
            self.logger.debug("Shimadzu AGS-X series")
            self.base_shift_value = -1
            self.machine_type = MachineType.AGSX
        else:
            self.logger.warn("Automatic machine type interpretation failed. Default to legacy... (Shimadzu EZ series)")
        
        

        # Find batch count and subbatch count using declared values. For AGS-X series, special routine that automatically detects the amount of samples were needed as wrong values are sometimes declared.
        # Legacy routine
        self.batch_count = int(self.tables[2 + self.base_shift_value][1][1])
        self.subbatch_count = int(self.tables[2 + self.base_shift_value][1][2])

        # AGS-X routine
        if self.machine_type == MachineType.AGSX:
            self.batch_count = int(self.tables[1][-1][0].split(" _ ")[0])
            self.subbatch_count = int(self.tables[1][-1][0].split(" _ ")[1])


        self.logger.info("Batch count: " + str(self.batch_count) + ", subbatch count: " + str(self.subbatch_count))


        # # Init truncation records
        # self.truncation_records = [[0 for i in range(self.batch_count)] for j in range(self.subbatch_count)]

    @property
    def id(self):
        return str(self.table_id)

    @property
    def table_name(self):
        return self._table_name

    @property
    def file_name(self):
        return self._file_name

    def dimensions(self, batch, subbatch):

        '''
        Find dimensions of a given sample specified by batch and subbatch
        '''
        sample_number = batch * subbatch
        thickness = float(self.tables[2 + self.base_shift_value][3+sample_number][1])
        width = float(self.tables[2 + self.base_shift_value][3+sample_number][2])
        length = float(self.tables[2 + self.base_shift_value][3+sample_number][3])
        # logger.debug("Dimensions for batch %d, subbatch %d: %s" % (batch, subbatch, (thickness, width, length)))

        return thickness, width, length

    def raw(self, batch, subbatch):

        '''
        Fetch stress/strain raw data for a given sample
        '''

        sample_number = batch * subbatch
        # Retrieve raw data, and make new numpy array
        str_array = np.array(self.tables[3 + sample_number + self.base_shift_value][3:])
        # Convert data type to float
        array = str_array[:, [1, 2]].astype(np.single)
        
        return array

    def get_curve_data(self, batch, subbatch, truncate_point = -1, dry_run = False):

        '''
        Get processed strain/stress data

        dry_run: if dry_run == True, then calculation would not be performed and no actual data will be returned.
        This is for validating if data of a given batch and subbatch number combination exists.
        truncate_point: set the truncation point, if set, the return data will be truncated.

        '''

        try:
            if dry_run == True:
                self.raw(batch, subbatch)
                return True
            else:
                calculated_curve = calculate(self.raw(batch, subbatch), self.dimensions(batch, subbatch))
                if truncate_point == -1:
                    return calculated_curve
                else:
                    return truncate_at(calculated_curve, truncate_point)
        except IndexError:
            if self.logger != None:
                self.logger.warn("Batch %d subbatch %d declared in data, but not found. Skipping." % (batch, subbatch))

    def __str__(self):
        return self._table_name


class Curve_cache():

    '''
        Cache of curves for further analysis and display
    '''

    def __init__(self, name = None):
        super().__init__()

        self._cache_status = {}     # Current status of the cache, a LUT for looking up index and truncation of selected curves of each table file being cached, structure: {table_id1: {batch1: {subbatch1: truncation1, ...}, ...}, ...}
        self._ref_lut = {} # LUT for refereces to Table() objects, format: {table_id: Table(), ...}
        self._snapshot = [] # Snapshot stack for self.cache_status(), structure: [cache_status_1, cache_status_2, ...]
        self._pointer = -1  # A pointer indicating the current position in status snapshot
        self._snapshot_saved_pos = None # A position in self._snapshot, at which the snapshot has been saved to a JSON snapshot file
        self._working_snapshot_file = None # The path of active JSON snapshot file
        self.name = name
        self.description = '' # Plain text description of the file
        
        self.update_snapshot()  # Set initial status

    @property
    def cached(self):

        '''
            Return a dict of cached curves
        '''

        return self._cache_status
    
    @property
    def lut(self):
        
        '''
            Retrun a lut of table id and reference to table objs
        '''

        return self._ref_lut

    @property
    def modified(self):
        
        '''
            Tells if the current cache status is different from last save/load process
        '''

        if self._snapshot_saved_pos == self._pointer:
            return False
        else:
            return True

    @property
    def working_snapshot_file(self):

        '''
            Get the URI of currently active snapshot JSON file
        '''
        return self._working_snapshot_file

    def cache(self, table, selections = None):

        '''
            Put new curves to the curve cache based on selections. If no selections has been specified, all curves in the given table will be cached.

            table: a Table() object
            selections: list of selction
            * selection: a tuple containing batch (required), subbatch (required), truncation point (optional)

            Notice: If a table has been cached before, then when it is cached again, the previous caching action gets reverted. All table objects pointing to a same data file will be deemed as the same object.
        '''

        cached_info = {}     # List of indices of cached curves of the current operating table file

        # If selection exists, then cache the selections:
        if selections != None:
            for selection in selections:
                # Validate each selection, make sure data for a given batch/subbatch combination exists
                if table.get_curve_data(selection[0], selection[1], dry_run = True) == True:
                    if selection[0] not in cached_info:
                        cached_info[selection[0]] = {}
                    if len(selection) == 3: # If selection contains truncation point data
                        cached_info[selection[0]][selection[1]] = selection[2]
                    else:
                        cached_info[selection[0]][selection[1]] = -1   # Write to list of index of selection
                    # self._curve_index += 1    # Set index counter

        # If no selection has been specified, then cache everything in the table
        else:
            # logger.debug("%d, %d" % (table.batch_count, table.subbatch_count))
            for batch in range (1, table.batch_count+1):
                for subbatch in range(1, table.subbatch_count+1):
                    if batch not in cached_info:
                        cached_info[batch] = {}
                    if table.get_curve_data(batch, subbatch, dry_run = True) == True:
                        cached_info[batch][subbatch] = -1
                        # self._curve_index += 1    # Set index counter

        # Write import record
        self._cache_status[table.id] = cached_info
        self._ref_lut[table.id] = table

        # Update status snapshot
        self.update_snapshot()



    def cache_s(self, table, selection_str = ''):

        '''
            A variant of Curve_cache.cache() allowing selection with selection string.

            table: a Table() object
            select_str: select string with the form of batch-subbatch-truncation, batch subbatch truncation
        '''

        selections = None

        if select_str != '':

            selections = []
            selection_strs = str.split(select_str, ',')
            for selection_str in selection_strs:
                batch = int(str.split(selection_str, '-')[0])
                subbatch = int(str.split(selection_str, '-')[1])
                if len(str.split(selection_str, '-')) == 3:
                    truncate_point = int(str.split(selection_str, '-')[2])
                    selections.append((batch, subbatch, truncate_point))
                else:
                    selections.append((batch, subbatch))

        self.cache(table, selections)

    def set_truncation(self, table_id, batch, subbatch, truncate_at):

        '''
            Set truncation point for a curve in cache

            index: index of the curve in cache
            truncate_ at: percentage turncation point
        '''
        
        # # Lookup the table file for the curve
        # curve = self._cache[index]

        # Rewrite truncation point information
        self._cache_status[table_id][batch][subbatch] = truncate_at
        # curve.truncate_point = truncate_at  # Legacy compatibility solution

        # Update snapshot
        self.update_snapshot()



    def remove(self, table_id, batch = None, subbatch = None):

        '''
            Remove one curve/batch/table in cache
        '''

        self._cache_status[table_id][batch].pop(subbatch, None)

        if self._cache_status[table_id][batch] == {} or subbatch == None:
            # If batch is empty or no subbatch is given (deem as delete the whole batch), remove the subbatch
            self._cache_status[table_id].pop(batch, None)

        if self._cache_status[table_id] == {} or batch == None and subbatch == None:
            # If table is empty or no batch and subbatch is given (deem as delete the whole table), remove the table
            self._cache_status.pop(table_id, None)
            self._ref_lut.pop(table_id, None)

        # Update snapshot
        self.update_snapshot()


    def update_snapshot(self):

        '''
            Update snapshot and manage pointer
        '''

        # Verify if there is anything beyond the current pointer position
        if len(self._snapshot) > self._pointer + 1:
            # If yes, then drop everything beyond
            self._snapshot = self._snapshot[: self._pointer + 1]

        # Move pointer
        self._pointer += 1

        # Update snapshot

        self._snapshot.append(self._cache_status.copy())


    def undo(self, dry_run = False):

        '''
            Roll the current cache information one version back

            dry_run: if True, then only whether the cache information can be rolled back to the designated version will verified, and no real rolling back action will be done.

            Return value: (bool1, bool2)
            - bool1: Whether the current operation has succeeded. Always true when dry_run is true.
            - bool2: Whether there is enough version in the snapshot so another undo can be performed
        '''

        succeeded = True   # Flag: If the current operation has succeeded
        can_proceed = False # Flag: If another undo can be performed

        # Verify if the status can be reverted to 1 version before
        if self._pointer > 0:
            
            # If not in dry_run mode, do the undo process:
            if dry_run != True:

                # If something can be undone, move pointer
                self._pointer -= 1

                # Rewrite cache status
                self._cache_status = self._snapshot[self._pointer].copy()

            # If the status can be further reverted
            if self._pointer > 0:
                can_proceed = True
        
        else:
            succeeded = False

        return succeeded, can_proceed
        


    def redo(self, dry_run = False):
        
        '''
            Move the current cache information one version Forward

            dry_run: if True, then only whether the cache information can be restored to the designated version will verified, and no real restoration action will be done.

            Return value: (bool1, bool2)
            - bool1: Whether the current operation has succeeded. Always true when dry_run is true.
            - bool2: Whether there is enough version in the snapshot so another undo can be performed
        '''

        succeeded = True   # Flag: If the current operation has succeeded
        can_proceed = False # Flag: If another undo can be performed

        # Verify if the status can be moved to 1 version after
        if len(self._snapshot) - self._pointer > 1:
            
            # If not in dry_run mode, do the redo process:
            if dry_run != True:

                # If something can be redone, move pointer
                self._pointer += 1

                # Rewrite cache status
                self._cache_status = self._snapshot[self._pointer].copy()

            # If the status can be further moved
            if len(self._snapshot) - self._pointer > 1:
                can_proceed = True
        
        else:
            succeeded = False

        return succeeded, can_proceed

    def reset(self):

        '''
            Nuke everything, including history
        '''
        # self._curve_index = 0
        # self._cache = {}
        self._cache_status = {}
        self._ref_lut = {}
        self._snapshot = []
        self._pointer = -1
        self._snapshot_saved_pos = None
        self._working_snapshot_file = None

        self.update_snapshot()
    
    def is_empty(self):

        '''
            Tells if the cache object have data or not
        '''
        # All actions generates history snapshots
        # If history snapshot is empty, then this cache can be deemed empty
        if len(self._snapshot) == 1:
            return True
        else:
            return False


    def clear(self):
        
        '''
            Delete all curves in cache status
        '''

        self._cache_status = {}

        self.update_snapshot()

    def analyze(self, selection = None):

        '''
        Analyze multiple curves and calculate average values.

        selection: a dict of curves in the same format as in self._cache_status, if None, then every curve in the cache will be analyzed.

        '''

        strength_pool = []
        slope_pool = []
        toughness_pool = []
        sab_pool = []      
        
        # Make sure that there's something in the cache
        if self._cache_status == {}:
            logger.error('No selection in curve cache "%s"' % self.name)
            return 0

        if selection != None:
            selection = self._cache_status

        # Traverse the whole selection, calculate values for every curve
        for table_id, table_contents in self._cache_status.items():

            table = self._ref_lut[table_id] # Get reference to the Table object

            for batch, batch_contents in table_contents.items():
                for subbatch, truncate_point in batch_contents.items():

                    data = table.get_curve_data(batch, subbatch, truncate_point)

                    max_stress_point = max_stress(data)
                    strain_value_at_break = strain_at_break(data)
                    slope = linear_regression(data)
                    toughness = (integrate_x(data))/config["axis"]["y_scaling"] # Convert to N/m^2

                    strength_pool.append(max_stress_point)
                    slope_pool.append(slope)
                    toughness_pool.append(toughness)
                    sab_pool.append(strain_value_at_break)

        strength_array = np.array(strength_pool)
        slope_array = np.array(slope_pool)
        toughness_array = np.array(toughness_pool)
        sab_array = np.array(sab_pool)

        # print(slope_array)
        # print(toughness_array)

        analysis_result = { # Dictionary object of analysis result

            'ym':{  

                # Young's Modulus

                'value': np.average(slope_array[:, 0])/config["axis"]["y_scaling"],
                'std': np.std(slope_array[:, 0])/config["axis"]["y_scaling"],
                'unit': config['axis']['y_unit']
            },
            'uts':{

                # Ultimate tensile strength

                'value': np.average(strength_array[:, 0])/config["axis"]["y_scaling"],
                'std': np.std(strength_array[:, 0])/config["axis"]["y_scaling"],
                'unit': config['axis']['y_unit']
            },
            'sams':{

                # Strain at maximum stress

                'value': np.average(strength_array[:, 1])/config["axis"]["y_scaling"],
                'std': np.std(strength_array[:, 1])/config["axis"]["y_scaling"],
                'unit': config["axis"]["x_unit"]

            },
            'sab':{

                # Strain at break
                'value': np.average(sab_array)/config["axis"]["x_scaling"],
                'std': np.std(sab_array)/config["axis"]["x_scaling"],
                'unit': config["axis"]["x_unit"]
            },
            'toughness':{

                # Area covered by the curve

                'value': np.average(toughness_array),
                'std': np.std(toughness_array),
                'unit': 'N*m^-2'
            }
        }
        print("Young's modulus for selected samples: %f, standard deviation: %f" % (analysis_result['ym']['value'], analysis_result['ym']['std']))   
        print("UTS for selected samples: %f, standard deviation: %f" % (analysis_result["uts"]["value"], analysis_result["uts"]["std"]))
        print("Strain at maximum stress for selected samples: %f, standard deviation: %f" % (analysis_result["sams"]["value"], analysis_result["sams"]["std"]))
        print("Toughness for selected samples: %f, standard deviation: %f" % (analysis_result["toughness"]["value"], analysis_result["toughness"]["std"]))

        return analysis_result        

    def take_snapshot(self, file_path = None):

        '''
            Save current cache to a .json file, for editing in the future

            - `file_path`: optional, specifies the save path of the .json file. If no path selected, will first attempt to save to the current active JSON snapshot file. If active JSON file path has not been set, save to the same directory as the corresponding .csv file of the 1st curve.
        '''

        # Figure out where to save the save file

        path = ''

        if file_path != None:
            # If a path is given, check if the path is legal and correct it
            if file_path.endswith('.json'):
                path = file_path
            else:
                path = file_path + '.json'

        elif self._working_snapshot_file != None:
            # If no path is given but active JSON file path has been set, use the latter
            path = self._working_snapshot_file
        else:
            # If no path is given and no active JSON file path has been set, save to the same directory as the corresponding .csv file of the 1st curve.
            first_pos = list(self._cache.keys())[0]   # Get index of the 1st element in cache
            path = os.path.splitext(self._cache[first_pos].table.file_name)[0] + '.json'
            logger.debug('No file path specified. Saving file to default location: %s' % path)


        # Construst LUT for curves that has been cached
        # LUT is like another version of self._cache_status; Hovever, the value of each item is a tuple containing curve info.
        lut = {}    # Structure of LUT: {filename:[(batch, subbatch, truncation), ...]}

        for table_id, table_contents in self._cache_status.items():
            
            curve_info_list = []
            file_name = self._ref_lut[table_id].file_name

            # Translation from dictionary to info tuple
            for batch, batch_contents in table_contents.items():
                for subbatch, truncate_point in batch_contents.items():
                    curve_info_list.append([batch, subbatch, truncate_point])

            lut[file_name] = curve_info_list


        # Construct file contents

        snapshot_contents = {
            "assets": lut,
            "config": config,
            "metadata": {
                "notes": ""
            },
            "version": 2
        }
        
        # Save to file

        try:
            with open(path, 'w') as fp:
                json.dump(snapshot_contents, fp)
                
                # Mark the current status as "saved"
                self._snapshot_saved_pos = self._pointer
                # Set new working JSON path
                self._working_snapshot_file = path

            return file_path
        except Exception as e:
            logger.debug(e)
            return -1

            


    def restore_snapshot(self, file_path, force = False):

        '''
            Retore cache from a .json snapshot file

            file_path: string, specifies the .json file to retore
            force: bool, if True, then anything in current cache will be overwritten; if False, then this function will refuse to restore if something is already in the cache.
        '''

        data = False

        if self.is_empty() == True or force == True:
            # Reset the current cache
            self.reset()
            
            if os.path.isfile(file_path) and file_path.endswith('.json'):
                try:
                    with open(file_path, 'r') as fp:
                        data = json.load(fp)

                except FileNotFoundError as e:
                    pass
                except json.JSONDecodeError as e:
                    # When something's wrong with the json file
                    pass
            else:
                return -1
        elif self.is_empty() == False and force != True:
            return -2

        # Process the snapshot file

        # Identify snapshot file version
        isV2 = data.get('version', 1)

        if isV2 == 2:
            assets = data['assets']
            config = data['config']
            self.description = data['metadata'].get('notes')
        else:
            assets = data

        # Load data to cache
        for data_file, selection_list in assets.items():
            table = Table(data_file)

            # Construct selection info in the format required by self.cache()
            selections = []
            for selection in selection_list:
                selections.append(tuple(i for i in selection))

            # Cache items
            self.cache(table, selections)

        # Compress snapshot stack, so the whole restoration process will be treated as one action
        del self._snapshot[1 : len(self._snapshot) - 1]
        self._pointer = 1

        # Mark the current status as "saved"
        self._snapshot_saved_pos = self._pointer

        # Set the current active snapshot file path
        self._working_snapshot_file = file_path

        return 0
            
    def get_table_obj(self, table_id):

        '''
            Get the reference of a table object specified by table_id
        '''

        return self._ref_lut(table_id)

    def get_curve(self, table_id, batch, subbatch):

        '''
            Get processed data for a given curve
        '''

        table = self.lut[table_id]
        truncate = self.cached[table_id][batch][subbatch]

        return table.get_curve_data(batch, subbatch, truncate_point = truncate)
            
        
        
# Plotting function

def plot_array_cmd(curves_dict, lut, compose_mode = None, **kwargs):

    '''
    Function for plotting arrays to file.

    Arguments:
    - curves_dict: A dict in the style of Curve_cache()._cache_status, structure: {table_id1: {batch1: {subbatch1: truncation1, ...}, ...}, ...}
    - lut: a dict for looking up references to table object by table_id
    - compose_mode: string, to plot the arrays in what manner
        - 'combined': plot all array in one plot
        - 'alone': plot each array in a single plot
        - 'sub: plot each array in a subplot
    - kwargs:
        - sub_width: int, specifies how many subplots should be in a row
        - legends: bool, switch on/off legends
        - preview: bool, use preview mode
    '''

    if compose_mode == 'combined' or compose_mode == None:
        fig = plt.figure()
        main_plt = fig.add_axes([0.1, 0.15, 0.7, 0.7])

        legend_list = []

        # Plot arrays in curves_list
        for table_id, table_contents in curves_dict.items():

            table = lut[table_id]

            for batch, batch_contents in table_contents.items():
                for subbatch, truncation in batch_contents.items():

                    array = table.get_curve_data(batch, subbatch, truncation)
                    legend_text = table.table_name + '-' + str(batch) + '-' +  str(subbatch)
                    legend_list.append(legend_text)
                    main_plt.plot(array[:, 1]/config['axis']['x_scaling'], array[:, 0]/config['axis']['y_scaling'])

        # Set axis labels 
        main_plt.axis(xmin=0, ymin=0)
        main_plt.set(ylabel = 'Stress [%s]' % config.get('axis').get('y_unit'), xlabel = 'Strain [%s]' % config.get('axis').get('x_unit'))
        # main_plt.set_xlabel('Strain [%s]' % config.get('axis').get('x_unit'))

        # Generate legends
        if kwargs.get('legends') or kwargs.get('preview'):              
            box = main_plt.get_position()
            main_plt.set_position([box.x0, box.y0, box.width*0.65, box.height])
            main_plt.legend(legend_list, bbox_to_anchor=(1.05,1), borderaxespad=0.)

        # Output the plot, either show or save to file
        if kwargs.get('preview'):
            plt.show()
        else:
            if kwargs.get('filename'):
                plt.savefig("%s.png" % kwargs.get('filename'), bbox_inches='tight')
            else:
                plt.savefig("%s.png" % str.split(curves_list[0].table.file_name, '.')[-2], bbox_inches='tight')

    elif compose_mode == 'alone':
        for index, curve in curves_list.items():
            array = curve.get_data()
            plt.figure(i)
            plt.plot(array[:, 1]/config['axis']['x_scaling'], array[:, 0]/config['axis']['y_scaling'])
            plt.axis(xmin=0, ymin=0)
            plt.ylabel('Stress [%s]' % config.get('axis').get('y_unit'))
            plt.xlabel('Strain [%s]' % config.get('axis').get('x_unit'))
            plt.savefig(str(curve) + '.png')
    elif compose_mode == 'sub':
        pass
    else:
        logger.error("Incorrect compose_mode.")



# Command line mode main processing flow
if __name__ == "__main__":


    # Initialize Argument Parser (argparse)
    parser = argparse.ArgumentParser(description='TenTackle: Tensile data analysis assisting tool for Shimazu.')
    parser.add_argument("-f", "--file", help="Specifies the .csv file to be processed")
    parser.add_argument("-i", "--interactive", help="Use interactive mode", action="store_true")
    parser.add_argument("-v", "--verbose", help="Increase output verbosity", action="store_true")
    parser.add_argument("-l", "--legend", help="Switch on/off legends", action="store_true")
    parser.add_argument("-c", "--compose_mode", help="Specifies how to organize plotted curves of different samples. Available options: combined, alone, sub")
    parser.add_argument("-s", "--select", help="Specifies which samples are to be plotted. Format: batch-subbatch(-truncate_percentage),batch-subbatch")
    # parser.add_argument("-r", "--slope_range", help="Specifies the range of data for slope/modulus measurement. Format: start_strain,end_strain")
    args = parser.parse_args()

    # Logging settings
    logger = logging.getLogger(__name__)
    if args.verbose:
        logger.setLevel(level=logging.DEBUG)
    else:
        logger.setLevel(level=logging.ERROR)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    logger.addHandler(ch)

    # Echo of commanlind options
    if args.verbose:
        logger.debug("Verbose mode: on")
    if args.interactive:
        logger.debug("Interactive mode: on")

    # Initialize curve cache
    cache = Curve_cache(name="main_cmd_cache")

    # Set up plotting config
    font = config['font']
    plt.rc('font', **font)

    if args.interactive != True and args.file:

        # Command line mode processing flow

        if os.path.isfile(args.file):
            try:
                table = Table(args.file)
            except Exception as e:
                logger.error(str(e))
                sys.exit()
        else:
            logger.error("Unable to open %s, exit." % args.file)
            sys.exit()

        if args.select:
            cache.cache_s(table, args.select)
        else:
            cache.cache(table)

        analyze_result = cache.analyze()
        plot_array_cmd(cache.cached, cache.lut, compose_mode=args.compose_mode, legends = args.legend)

    elif args.interactive == True:

        # Interactive mode

        while(True):
            main_operation = input("Enter action: open/preview/output/analysis/clear/exit\n")

            if main_operation == 'open':
                while(True): 
                    filename = input("Enter file name, or press enter to return:\n")
                    if os.path.isfile(filename):
                        working_table = Table(filename)             
                        select_str = input("Select data of samples, or input 'all' to select all. Format: batch-subbatch-truncate_at, batch-subbatch,... Press enter to return\n")
                        if select_str == 'all' or select_str == '':
                            cache.cache(working_table)
                            print("Data of all samples has been successfully cached.")
                        else:                   
                            cache.cache_s(working_table, select_str)
                            print("Selection has been successfully cached.")
                    elif filename == '':
                        break
                    else:
                        logger.error("File not found: %s" % filename)
                        continue

            elif main_operation == 'exit':
                print("Exit now.")
                break
            elif main_operation =='output':
                legend = False
                while(True):
                    legend_input = input("Turn on legends (default = no)? y/n\n")
                    if legend_input == 'y':
                        legend = True
                        break
                    elif legend_input == 'n' or legend_input == '':
                        break
                    else:
                        print("Type 'y' or 'n'.\n")
                
                compose_mode = 'combined'
                while(True):
                    compose_mode_input = input("Input compose mode (default = combined). combined/alone\n")
                    if compose_mode_input == 'combined' or compose_mode_input == '':
                        legend = True
                        break
                    elif compose_mode_input == 'alone':
                        compose_mode = 'alone'
                        break
                    else:
                        print("Type combined/alone .\n")            
                plot_array_cmd(cache.cached, cache.lut, compose_mode = compose_mode, legends = legend)
                        
            elif main_operation =='analysis':
                cache.analyze()
            elif main_operation =='preview':
                plot_array_cmd(cache.cached, cache.lut, preview = True)
            elif main_operation =='clear':
                cache.clear()
            else:
                print("Invalid action.")
    else:
        logger.error("No file specified. Exit.\n Use -h for help.")

else:
    # Logging settings (when used as a module)
    logger = logging.getLogger(__name__)
    logger.setLevel(level=logging.DEBUG)
    ch = logging.StreamHandler()
    # ch.setLevel(logging.DEBUG)
    logger.addHandler(ch)
