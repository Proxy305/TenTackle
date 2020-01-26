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
            self._table_name = filename
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
    def table_name():
        return self._table_name

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

        self.table = table
        self.batch = batch
        self.subbatch = subbatch
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
    def slope(self):
        data = self.get_data()
        return linear_regression(data)
    
    @property
    def max_stress(self):
        return max_stress(self.get_data())

class Curve_cache():

    '''
        Cache of curves for further analysis and display
    '''

    def __init__(self, name = None):
        super().__init__()

        self._cache = []    # Selection records, format: [(table, (batch, subbatch, truncation))]
        self.name = name
        # self._strength_pool = [] # A pool containing strength of every curve
        # self._slope_pool = []    # A pool containing slope of every curve

    @property
    def cached(self):

        '''
            Return the current cache
        '''

        return self._cache

    def cache(self, table, selections = None):

        '''
            Put new curves to the curve cache based on selections. If no selections has been specified, all curves in the given table will be cached.

            table: a Table() object
            selections: list of selction
            * selection: a tuple containing batch (required), subbatch (required), truncation point (optional)
        '''

        # If selection exists, then cache the selections:
        if selections != None:
            for selection in selections:
                # Validate each selection, make sure data for a given batch/subbatch combination exists
                if table.get_curve_data(selection[0], selection[1], dry_run = True) == True:
                    if len(selection) == 3: # If selection contains truncation point data
                        self._cache.append(Curve(table, selection[0], selection[1], selection[2]))  # Set truncation if truncation data exists
                    else:
                        self._cache.append(Curve(table, selection[0], selection[1]))

        # If no selection has been specified, then cache everything in the table
        else:
            # logger.debug("%d, %d" % (table.batch_count, table.subbatch_count))
            for batch in range (1, table.batch_count+1):
                for subbatch in range(1, table.subbatch_count+1):
                    if table.get_curve_data(batch, subbatch, dry_run = True) == True:
                        print(table.get_curve_data(batch, subbatch))
                        self._cache.append(Curve(table, batch, subbatch))
            

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

    def clear(self):
        
        '''
            Delete all curves in cache
        '''

        self._cache = []

    def analyze(self):
        strength_pool = []
        slope_pool = []

        # Make sure that there's something in the
        if self._cache == []:
            logger.error('No selection in curve cache "%s"' % self.name)
            return 0

        print("total length %d" % len(self._cache))

        for curve in self._cache:
            print("curve: %s %d %d" % (curve.table, curve.batch, curve.subbatch))
            strength_pool.append(curve.max_stress)
            slope_pool.append(curve.slope)

        strength_array = np.array(strength_pool)

        analysis_result = { # Dictionary object of analysis result

            'ym':{  

                # Young's Modulus

                'value': np.average(slope_pool),
                'std': np.std(slope_pool)
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

        
        
# Plotting function
font = config['font']

plt.rc('font', **font)

def plot_array_cmd(curves_list, compose_mode = None, **kwargs):

    '''
    Function for plotting arrays to file.

    Arguments:
    - array_list: list, list carrying all sample info
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
        for curve in curves_list:
            array = curve.get_data()
            legend_list.append(str(curve))
            main_plt.plot(array[:, 1]/config['axis']['x_scaling'], array[:, 0]/config['axis']['y_scaling'])

        # Set axis labels 
        main_plt.axis(xmin=0, ymin=0)
        main_plt.set(ylabel = 'Stress [%s]' % config.get('axis').get('y_unit'), xlabel = 'Strain [%s]' % config.get('axis').get('x_unit'))
        # main_plt.set_xlabel('Strain [%s]' % config.get('axis').get('x_unit'))

        # Generate legend according to meta_map
        if kwargs.get('legends') or kwargs.get('preview'):              
            box = main_plt.get_position()
            main_plt.set_position([box.x0, box.y0, box.width*0.65, box.height])
            main_plt.legend(legend_list, bbox_to_anchor=(1.05,1), borderaxespad=0.)

        # Output the plot, either show or save to file
        if kwargs.get('preview'):
            plt.show()
        else:
            plt.savefig("%s.png" % os.path.splitext(kwargs.get('meta_map')[0][0])[0], bbox_inches='tight')

    elif compose_mode == 'alone':
        for curve in curves_list:
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



# Main processing flow

# tables_list = []    # List all table objects
# result_list = []    # List of processed results
# meta_list = []    # Metadata of processed results: [(table_name, batch_num, subbatch_num),]
# strength_list = []
# slope_list = []

# def cache(table_file, select_str = ''):

#     '''
#         Cache tables by table file and optional select string
#     '''


#     if select_str != '':
#         select_split = str.split(select_str, ',')
#         for elem in select_split:
#             batch = int(str.split(elem, '-')[0])
#             subbatch = int(str.split(elem, '-')[1])
#             if len(str.split(elem, '-')) == 3:
#                 result = truncate_at(table_file.get(batch, subbatch), int(str.split(elem, '-')[2]))
#             else:
#                 try:
#                     result = table_file.get(batch, subbatch)
#                 except IndexError:
#                     logger.warn("Batch %d subbatch %d not found. Skipping." % (batch, subbatch))
#                     continue
                
#             meta_list.append((table_file.tablename, batch, subbatch))
#             result_list.append(result)
#             strength_list.append(max_stress(result))
#     else:
#         for i in range (0, table_file.batch_count):
#             for j in range(0, table_file.subbatch_count):
#                 try:
#                     result = table_file.get(i+1, j+1)
#                 except IndexError:
#                     logger.warn("Batch %d subbatch %d not found. Skipping." % (i, j))
#                     continue
#                 result_list.append(result)
#                 strength_list.append(max_stress(result))
#                 meta_list.append((table_file.tablename, i+1, j+1))
                
# def analysis(slope_range = None):

#     '''
#         Analyze critical properties of curves
#     '''

#     for elem in result_list:
#         if slope_range != None:
#             slope_range = (int(str.split(args.slope_range, ',')[0]), int(str.split(args.slope_range, ',')[1]))
#             slope_list.append(linear_regression(elem, from_to=slope_range)[0])
#         else:
#             slope_list.append(linear_regression(elem)[0])

#     strength_array = np.array(strength_list)

#     analysis_result = { # Dictionary object of analysis result

#         'ym':{  

#             # Young's Modulus

#             'value': np.average(slope_list),
#             'std': np.std(slope_list)
#         },
#         'uts':{

#             # Ultimate tensile strength

#             'value': np.average(strength_array[:, 0]),
#             'std': np.std(strength_array[:, 0])
#         },
#         'sams':{

#             # Strain at maximum stress

#             'value': np.average(strength_array[:, 1]),
#             'std': np.std(strength_array[:, 1])

#         }
#     }
#     logger.debug(analysis_result.keys())
#     logger.info("Young's modulus for selected samples: %f, standard deviation: %f" % (analysis_result['ym']['value'], analysis_result['ym']['std']))
    
#     logger.info("UTS for selected samples: %f, standard deviation: %f" % (analysis_result["uts"]["value"], analysis_result["uts"]["std"]))
#     logger.info("Strain at maximum stress for selected samples: %f, standard deviation: %f" % (analysis_result["sams"]["value"], analysis_result["sams"]["std"]))

#     return analysis_result

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
                            print(select_str)
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
