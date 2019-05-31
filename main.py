# -*- coding: utf-8 -*-
# Tensile_auto: Tensile data analysis assistance tool for Shimazu

import os
import csv
import logging
import argparse
import numpy as np
import matplotlib.pyplot as plt
import math

# Initialize Argument Parser (argparse)
parser = argparse.ArgumentParser(description='Tensile_auto: Tensile data analysis assisting tool for Shimazu.')
parser.add_argument("-f", "--file", help="Specifies the .csv file to be processed")
parser.add_argument("-i", "--interactive", help="Use interactive mode", action="store_true")
parser.add_argument("-v", "--verbose", help="Increase output verbosity", action="store_true")
parser.add_argument("-l", "--legend", help="Switch on/off legends", action="store_true")
parser.add_argument("-c", "--compose_mode", help="Specifies how to organize plotted curves of different samples. Available options: combined, alone, sub")
parser.add_argument("-s", "--select", help="Specifies which samples are to be plotted. Format: batch-subbatch(-truncate_percentage),batch-subbatch")
parser.add_argument("-r", "--slope_range", help="Specifies the range of dots for slope/modulus measurement. Format: start,end")
args = parser.parse_args()

# Logging settings
logger = logging.getLogger(name='global')
if args.verbose:
    logger.setLevel(level=logging.DEBUG)
else:
    logger.setLevel(level=logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
logger.addHandler(ch)

# Echo of commanlind options
if args.verbose:
    logger.debug("Verbose mode: on")
if args.interactive:
    logger.debug("Interactive mode: on")


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

def linear_regression(array, from_to = (30, 150)):

    '''
    Linear regression helper function, for finding slopes
    '''

    measure_area = array[from_to[0]:from_to[1], :]
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

class Table:

    '''
    Structure for storaging raw data from a single .csv file
    '''

    def __init__(self, filename, tablename = ''):
        
        # self.tables: keeps all table raw infomation
        self.tables = []

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
            self.tablename = filename

        # Find batch count and subbatch count
        self.batch_count = int(self.tables[2][1][1])
        self.subbatch_count = int(self.tables[2][1][2])

        logger.info("Batch count: " + str(self.batch_count) + ", subbatch count: " + str(self.subbatch_count))


    def dimensions(self, batch, subbatch):

        '''
        Find dimensions of a given sample specified by batch and subbatch
        '''
        sample_number = batch * subbatch
        thickness = float(self.tables[2][3+sample_number][1])
        width = float(self.tables[2][3+sample_number][2])
        length = float(self.tables[2][3+sample_number][3])

        logger.debug("Demensions for batch %d, subbatch %d: %s" % (batch, subbatch, (thickness, width, length)))

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

    def get(self, batch, subbatch):

        '''
        Get processed strain/stress data
        '''

        return calculate(self.raw(batch, subbatch), self.dimensions(batch, subbatch))


# Plotting function
font = {'family' : 'Monospace',
        'weight' : 'bold',
        'size'   : 14}

plt.rc('font', **font)

def plot_array(array_list, compose_mode = 'combined', **kwargs):

    '''
    Function for plotting arrays to file.

    Arguments:
    - array_list: list, list carrying all sample info
    - compose_mode: string, to plot the arrays in what manner
        - 'combined': plot all array in one plot
        - 'alone': plot each array in a single plot
        - 'sub: plot each array in a subplot
    - kwargs:
        - meta_map: list, mapping of sample batch/subbatch number and position of array in array_list
            - format: [(table_name, batch_num, subbatch_num),]
        - sub_width: int, specifies how many subplots should be in a row
        - legends: bool, switch on/off legends
    '''

    if compose_mode == 'combined':
        # Plot arrays in array_list
        for array in array_list:
            plt.plot(array[:, 1], array[:, 0])
        # Generate legend according to meta_map
        if kwargs['legends']:
            if kwargs.get('meta_map') != None:
                meta_map = kwargs.get('meta_map')
                legend_list = []
                for elem in meta_map:
                    tablename = os.path.splitext(os.path.split(elem[0])[1])[0]
                    legend_list.append(tablename + '-' + str(elem[1])  + '-' + str(elem[2]))
                plt.legend(legend_list, loc='best')
            
        plt.axis(xmin=0, ymin=0)
        plt.ylabel('Stress [MPa]')
        plt.xlabel('Strain')
        plt.savefig("%s.png" % os.path.splitext(kwargs.get('meta_map')[0][0])[0])

    elif compose_mode == 'alone':
        count = 1
        for array in array_list:
            plt.figure(count)
            plt.plot(array[:, 1], array[:, 0])
            plt.axis(xmin=0, ymin=0)
            plt.ylabel('Stress [MPa]')
            plt.xlabel('Strain')
            if kwargs.get('meta_map') != None:
                meta_map = kwargs.get('meta_map')
                plt.savefig(os.path.join(os.path.dirname(args.file), "%s-%d-%d.png" % (meta_map[count-1][0], meta_map[count-1][1], meta_map[count-1][2])))
            else:
                plt.savefig(os.path.join(os.path.dirname(args.file), "%s-%d.png" % (os.path.splitext(args.file)[0], count)))    # If meta_map is not specified, then it should not be in interactive mode and only have 1 file/table working, so args.file is used as a dirty hack
            count += 1  
    elif compose_mode == 'sub':
        pass
    else:
        logger.error("Incorrect compose_mode.")



# Main processing flow

tables_list = []    # List all table objects
result_list = []    # List of processed results
meta_list = []  # Metadata of processed results: [(table_name, batch_num, subbatch_num),]
strength_list = []
slope_list = []

def cache(table, select_str = ''):
    if select_str != '':
        select_split = str.split(select_str, ',')
        for elem in select_split:
            batch = int(str.split(elem, '-')[0])
            subbatch = int(str.split(elem, '-')[1])
            if len(str.split(elem, '-')) == 3:
                result = truncate_at(table.get(batch, subbatch), int(str.split(elem, '-')[2]))
            else:
                result = table.get(batch, subbatch)
            meta_list.append((table.tablename, batch, subbatch))
            result_list.append(result)
            strength_list.append(max_stress(result)[0])
    else:
        for i in range (0, table.batch_count):
            for j in range(0, table.subbatch_count):
                result = table.get(i+1, j+1)
                result_list.append(result)
                strength_list.append(max_stress(result)[0])
                meta_list.append((table.tablename, i+1, j+1))
                
def analysis():
    for elem in result_list:
        if args.slope_range:
            slope_range = (int(str.split(args.slope_range, ',')[0]), int(str.split(args.slope_range, ',')[1]))
            slope_list.append(linear_regression(elem, from_to=slope_range)[0])
        else:
            slope_list.append(linear_regression(elem)[0])

    logger.info("Young's modulus for selected samples: %f, standard deviation: %f" % (np.average(slope_list), np.std(slope_list)))
    logger.info("UTS for selected samples: %f, standard deviation: %f" % (np.average(strength_list), np.std(strength_list)))


if args.interactive != True and args.file:

    if os.path.isfile(args.file):
        tables_list.append(Table(args.file))
    else:
        logger.error("Unable to open %s, exit." % args.file)

    if args.select:

        cache(tables_list[0], args.select)

    else:

        cache(tables_list[0])

    analysis()

    if args.compose_mode:
        plot_array(result_list, compose_mode=args.compose_mode, meta_map = meta_list, legends = args.legend)
    else:
        plot_array(result_list, meta_map = meta_list, legends = args.legend)

elif args.interactive == True:

    # Interactive mode

    while(True):
        main_operation = input("Enter action: open/output/analysis/exit\n")

        if main_operation == 'open':
            while(True): 
                filename = input("Enter file name, or press enter to return:\n")
                if os.path.isfile(filename):
                    working_table = Table(filename)
                    tables_list.append(working_table)                
                    while(True):
                        select = input("Select samples, or input 'all' to select all. Format: batch-subbatch-truncate_at, batch-subbatch,... Press enter to return\n")
                        if select == 'all':
                            cache(working_table)
                            print("Selection has been successfully cached.")
                            break
                        elif select == '':
                            break
                        else:                   
                            try:
                                print(select)
                                cache(working_table, select)
                                print("Selection has been successfully cached.")
                                break
                            except Exception as e:
                                logger.error("Error happened during cache process. Check selection string.")
                                logger.debug(str(e))
                                continue
                elif filename == '':
                    break
                else:
                    continue

        elif main_operation == 'exit':
            print("Exit now.")
            break
        elif main_operation =='output':
            legend = False
            while(True):
                legend_input = input("Turn on legends (default = no)? yes/no\n")
                if legend_input == 'yes':
                    legend = True
                    break
                elif legend_input == 'no':
                    break
                else:
                    if legend_input == '':
                        break
                    else:
                        print("Type 'yes' or 'no'.\n")
            
            compose_mode = 'combined'
            while(True):
                compose_mode_input = input("Input compose mode (default = combined). combined/alone\n")
                if compose_mode_input == 'combined':
                    legend = True
                    break
                elif compose_mode_input == 'alone':
                    break
                else:
                    if compose_mode_input == '':
                        break
                    else:
                        print("Type combined/alone .\n")            
            plot_array(result_list, compose_mode=compose_mode, meta_map = meta_list, legends = legend)
                    
        elif main_operation =='analysis':
            analysis()
        else:
            print("Invalid action.")
else:
    logger.error("No file specified. Exit.\n Use -h for help.")



# Testing code

# arr = calculate(fetch_raw(1,1), find_dimensions(1,1))
# plot_array([calculate(fetch_raw(1,1), find_dimensions(1,1)), calculate(fetch_raw(1,2), find_dimensions(1,2))], compose_mode='combined', meta_map = [(1,1), (1,2)])
# print("Max stress: " + str(max_stress(arr)))
# print(arr.shape)
# print(truncate_at(arr, 0.9).shape)
