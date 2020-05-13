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

def linear_regression(array, from_to = (config['regression']['start'], config['regression']['end'])):

    '''
    Linear regression helper function, for finding slopes

    array: np_array, data source of linear regression
    from_to: tuple, (from_x_equals_to_value, to_x_equals_to_value)
        Example: (0.1, 0.2) means select a part of the array from x=0.1 to x=0.2, and calculate linear regression for this part.
    '''

    start_idx = idx_of_nearest(array[:, 0], from_to[0])
    end_idx = idx_of_nearest(array[:, 1], from_to[1])

    logger.debug("From, to: %d, %d" % (start_idx, end_idx))

    measure_area = array[start_idx:end_idx, :]
    x = measure_area[:, 1]
    y = measure_area[:, 0]

    slope = (len(x) * np.sum(x*y) - np.sum(x) * np.sum(y)) / (len(x)*np.sum(x*x) - np.sum(x) ** 2)
    intercept = (np.sum(y) - slope *np.sum(x)) / len(x)

    return slope, intercept

def max_stress(array):

    '''
    Find maximum stress in a stress/strain array
    '''
    
    max_stress = np.amax(array, axis=0)
    return max_stress   # max_stress: tuple, with stress and corresponding strain info

def idx_of_nearest(array_1d, target):

    '''
    Find the index of value nearest to target in a 1d array.
    Only 1d array should be given as param; otherwise would not give correct result
    '''

    return (np.abs(array_1d - target)).argmin()


# Data structures
class Table:

    '''
    Structure for storaging raw data from a single .csv file
    '''

    def __init__(self, filename, tablename = '', logger=None):

        super().__init__()
        
        self.tables = []    # Keeps all table raw infomation
        self._file_name = filename

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

        # Find batch count and subbatch count
        self.batch_count = int(self.tables[2][1][1])
        self.subbatch_count = int(self.tables[2][1][2])
        if logger != None:
            self.logger = logger
            logger.info("Batch count: " + str(self.batch_count) + ", subbatch count: " + str(self.subbatch_count))
        else:
            self.logger = None

        # Init truncation records
        self.truncation_records = [[0 for i in range(self.batch_count)] for j in range(self.subbatch_count)]

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
        thickness = float(self.tables[2][3+sample_number][1])
        width = float(self.tables[2][3+sample_number][2])
        length = float(self.tables[2][3+sample_number][3])
        # logger.debug("Dimensions for batch %d, subbatch %d: %s" % (batch, subbatch, (thickness, width, length)))

        return thickness, width, length

    def raw(self, batch, subbatch):

        '''
        Fetch stress/strain raw data for a given sample
        '''

        sample_number = batch * subbatch
        # Retrieve raw data, and make new numpy array
        str_array = np.array(self.tables[3+sample_number][3:])
        # Convert data type to float
        array = str_array[:, [1, 2]].astype(np.float)
        
        return array

    def get_curve_data(self, batch, subbatch, dry_run = False):

        '''
        Get processed strain/stress data

        dry_run: if dry_run == True, then calculation would not be performed and no actual data will be returned.
        This is for validating if data of a given batch and subbatch number combination exists.

        '''

        try:
            if dry_run == True:
                self.raw(batch, subbatch)
                return True
            else:
                calculated_curve = calculate(self.raw(batch, subbatch), self.dimensions(batch, subbatch))
                return calculated_curve
        except IndexError:
            if self.logger != None:
                self.logger.warn("Batch %d subbatch %d declared in data, but not found. Skipping." % (batch, subbatch))
    
    # def set_truncation(self, batch, subbatch, truncate_at):

    #     '''
    #         Set truncation point of curve
    #     '''

    #     self.truncation_records[batch-1][subbatch-1] = truncate_at

    def __str__(self):
        return self._table_name

class Curve():


    def __init__(self, table, batch, subbatch, truncate_point = -1):

        super().__init__()

        self._table = table # Read only
        self._batch = batch # Read only
        self._subbatch = subbatch   # Read only
        self.truncate_point = truncate_point

    def get_data(self, truncate = False):

        '''
            Get data of points of curve

            truncate: truncate the data before returning
        '''
        calculated_data = self.table.get_curve_data(self.batch, self.subbatch)
        if truncate == True and self.truncate_point != -1:
            return truncate_at(calculated_data, self.truncate_point)
        else:
            return calculated_data

    def __str__(self):
        return '%s-%d-%d' % (str(self.table), self.batch, self.subbatch)

    @property
    def table(self):
        return self._table

    @property
    def batch(self):
        return self._batch

    @property
    def subbatch(self):
        return self._subbatch            

    @property
    def slope(self):
        data = self.get_data()
        return linear_regression(data)
    
    @property
    def max_stress(self):
        return max_stress(self.get_data())

    @property
    def table_name(self):
        return str(self.table)

class Curve_cache():

    '''
        Cache of curves for further analysis and display
    '''

    def __init__(self, name = None):
        super().__init__()

        self._curve_index = 0     # A counter for generating unique index for curves
        self._cache = {}    # Selection records, format: {index: Curve, ...}
        self._cache_status = {}     # Current status of the cache, a LUT for looking up index and truncation of selected curves of each table file being cached, structure: {file_name: {index1: trunction, index2: truncation, ...}}
        self._snapshot = [] # Snapshot for self.cache_status(), structure: [cache_status_1, cache_status_2, ...]
        self._pointer = -1  # A pointer indicating the current position in status snapshot
        self.name = name
        
        self.update_snapshot()  # Set initial status

    @property
    def cached(self):

        '''
            Construct a list of curves
        '''

        curves_list = {}

        for table_file, info_dict in self._cache_status.items():
            for index, turncation_point in info_dict.items():
                var = self._cache[index]
                curves_list[index] = var

        return curves_list

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
                    truncate_point = -1
                    if len(selection) == 3: # If selection contains truncation point data
                        self._cache[self._curve_index] = Curve(table, selection[0], selection[1], selection[2])  # Set truncation if truncation data exists
                        truncate_point = selection[2]
                    else:
                        self._cache[self._curve_index] = Curve(table, selection[0], selection[1])
                    cached_info[self._curve_index] = truncate_point    # Write to list of index of selection
                    self._curve_index += 1    # Set index counter

        # If no selection has been specified, then cache everything in the table
        else:
            # logger.debug("%d, %d" % (table.batch_count, table.subbatch_count))
            for batch in range (1, table.batch_count+1):
                for subbatch in range(1, table.subbatch_count+1):
                    if table.get_curve_data(batch, subbatch, dry_run = True) == True:
                        self._cache[self._curve_index] = Curve(table, batch, subbatch)
                        cached_info[self._curve_index] = -1 # -1: default runcation point (no truncation)
                        self._curve_index += 1    # Set index counter


        # Validate if this table has been cached before
        # if self._cache_status.get(table.file_name) != None:
        #     # If this table has been cached before, revert the cache action
        #     print("fuck python!")
        #     self.remove_by_indices(self._cache_status[table.file_name])
        # Write import record
        self._cache_status[table.file_name] = cached_info

        # Update status snapshot
        self.update_snapshot()

        # Return indices of cached curves
        cached_indices = []
        for index, truncation in cached_info.items():
            cached_indices.append(index)
        return cached_indices
            

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

    def set_truncation(self, index, truncate_at):

        '''
            Set truncation point for a curve in cache

            index: index of the curve in cache
            truncate_ at: percentage turncation point
        '''
        
        # Lookup the table file for the curve
        curve = self._cache[index]

        # Rewrite truncation point information
        self._cache_status[curve.table_file][index] = truncate_at
        curve.truncate_point = truncate_at  # Legacy compatibility solution

        # Update snapshot
        self.update_snapshot()



    def remove(self, index):

        '''
            Remove one curve in cache, by its index
        '''

        self._cache.pop(index, None)


    def remove_by_indices(self, indices):

        '''
            Remove multiple curves specified by a list of indices in cache. A wrapper for Curve_cache.remove()

            indices: a list of index
        '''

        for index in indices:

            self.remove(index)

    def revert(self, file_name):

        '''
            Revert a certain cache action specified by file name
        '''

        cached_info = self._cache_status.get(file_name)
        
        if cached_info  != None:
            # self.remove_by_indices(cached_info)     
            self._cache_status.pop(file_name)

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



    def clear(self):
        
        '''
            Delete all curves in cache status
        '''

        self._cache_status = {}

        self.update_snapshot()

    def analyze(self):
        strength_pool = []
        slope_pool = []

        curve_list = self.cached # Get curves that are current in curve_status
        
        # Make sure that there's something in the cache
        if curve_list == {}:
            logger.error('No selection in curve cache "%s"' % self.name)
            return 0


        for index, curve in curve_list.items():
            strength_pool.append(curve.max_stress)
            slope_pool.append(curve.slope)

        strength_array = np.array(strength_pool)
        slope_array = np.array(slope_pool)

        print(slope_pool)

        analysis_result = { # Dictionary object of analysis result

            'ym':{  

                # Young's Modulus

                'value': np.average(slope_array[:, 0]),
                'std': np.std(slope_array[:, 0])
            },
            'uts':{

                # Ultimate tensile strength

                'value': np.average(strength_array[:, 0]),
                'std': np.std(strength_array[:, 0])
            },
            'sams':{

                # Strain at maximum stress

                'value': np.average(strength_array[:, 1]),
                'std': np.std(strength_array[:, 1])

            }
        }
        logger.debug(analysis_result.keys())
        logger.info("Young's modulus for selected samples: %f, standard deviation: %f" % (analysis_result['ym']['value'], analysis_result['ym']['std']))
        
        logger.info("UTS for selected samples: %f, standard deviation: %f" % (analysis_result["uts"]["value"], analysis_result["uts"]["std"]))
        logger.info("Strain at maximum stress for selected samples: %f, standard deviation: %f" % (analysis_result["sams"]["value"], analysis_result["sams"]["std"]))

        return analysis_result        

    def take_snapshot(self, file_path = None):

        '''
            Dump current cache to a .tcs.json ((T)entackle (C)ache (S)napshot file, for editing in the future

            file_path: optional, specifies the save path of the .tcs.json file. If no path selected, the file will be saved to the same path and with the same name as the .csv table file of first curve in cache.
        '''

        # Figure out where to save the dump file

        path = ''

        if file_path != None:
            if file_path.endswith('.tcs.json'):
                path = file_path
            else:
                path = file_path + '.tcs.json'
        else:
            first_pos = list(self._cache.keys())[0]   # Get index of the 1st element in cache
            path = os.path.splitext(self._cache[first_pos].table.file_name)[0] + '.tcs.json'
            logger.debug('No file path specified for dumping. Saving file to default location: %s' % path)


        # Construst LUT for curves that has been cached
        # LUT is like another version of self._cache_status; Hovever, the value of each item is a tuple containing curve info.
        lut = {}    # Structure of LUT: {filename:[(batch, subbatch, truncation), ...]}

        for file_name, indices in self._cache_status.items():
            
            curve_info_list = []

            # Translation from index to info tuple
            for index in indices:
                curve = self._cache[index]
                curve_info_list.append((curve.batch, curve.subbatch, curve.truncate_point))

            lut[file_name] = curve_info_list

        
        # Save to file

        try:
            with open(path, 'w') as fp:
                json.dump(lut, fp)
            return file_path
        except Exception as e:
            logger.debug(e)
            return 0

            


    def restore_from_snapshot(self, file_path):

        '''
            Retore cache from a .tcs.json ((T)entackle (C)ache (S)napshot file

            file_path: specifies the .tcs.json file to retore
        '''

        if os.path.isfile(file_path) and file_path.endswith('.tcs.json'):
            pass
        
        
# Plotting function

def plot_array_cmd(curves_list, compose_mode = None, **kwargs):

    '''
    Function for plotting arrays to file.

    Arguments:
    - curves_list: Dictionary {int index, Curve() curve}, usually from Curve_cache.cached
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
        for index, curve in curves_list.items():
            array = curve.get_data()
            legend_list.append(str(curve))
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
        plot_array_cmd(cache.cached, compose_mode=args.compose_mode, legends = args.legend)

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
                plot_array_cmd(cache.cached, compose_mode = compose_mode, legends = legend)
                        
            elif main_operation =='analysis':
                cache.analyze()
            elif main_operation =='preview':
                plot_array_cmd(cache.cached, preview = True)
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
    ch.setLevel(logging.DEBUG)
    logger.addHandler(ch)
