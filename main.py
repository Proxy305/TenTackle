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
parser.add_argument("file", help="Specifies the .csv file to be processed")
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

# tables: keeps all table raw infomation
tables = []

# Split multiple tables in single .csv file
try:
    with open(args.file, newline='', encoding='Shift-JIS') as f:
        reader = csv.reader(f)

        temp_table = []

        for row in reader:
            if row != []:
                temp_table.append(row)
            else:
                tables.append(temp_table)
                temp_table = []
except FileNotFoundError as e:
    logger.error(str(e))
    exit(1)


# Find batch count and subbatch count
batch_count = int(tables[2][1][1])
subbatch_count = int(tables[2][1][2])

logger.info("Batch count: " + str(batch_count) + ", subbatch count: " + str(subbatch_count))

# Helper functions

# Helper function category A: functions that directly deals with raw data
# Creation, and usage of cat. A helper function should be avoided for better de-coupling

def find_dimensions(batch, subbatch):

    '''
    Find dimensions of a given sample specified by batch and subbatch
    '''
    sample_number = batch * subbatch
    thickness = float(tables[2][3+sample_number][1])
    width = float(tables[2][3+sample_number][2])
    length = float(tables[2][3+sample_number][3])

    logger.debug("Demensions for batch %d, subbatch %d: %s" % (batch, subbatch, (thickness, width, length)))

    return thickness, width, length

def fetch_raw(batch, subbatch):

    '''
    Fetch stress/strain raw data for a given sample
    '''

    sample_number = batch * subbatch
    # Retrieve raw data, and make new numpy array
    str_array = np.array(tables[3+sample_number][3:])
    # Convert data type to float
    array = str_array[:, [1, 2]].astype(np.float)
    
    return array

# Helper function category B: functions that accepts a procecced stress/strain data array

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

# Plotting function
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
            - format: [(batch, subbatch), (batch, subbatch)]
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
                    legend_list.append(str(str(elem[0])) + '-' + str(elem[1]))
                plt.legend(legend_list, loc='upper left')
            
        plt.axis(xmin=0, ymin=0)
        plt.ylabel('Stress [MPa]')
        plt.xlabel('Strain')
        plt.savefig("%s.png" % os.path.splitext(args.file)[0])

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
                plt.savefig(os.path.join(os.path.dirname(args.file), "%s-%d-%d.png" % (os.path.splitext(args.file)[0], meta_map[count-1][0], meta_map[count-1][1])))
            else:
                plt.savefig(os.path.join(os.path.dirname(args.file), "%s-%d.png" % (os.path.splitext(args.file)[0], count)))
            count += 1  
    elif compose_mode == 'sub':
        pass
    else:
        logger.error("Incorrect compose_mode.")

def max_stress(array):

    '''
    Find maximum stress in a stress/strain array
    '''
    
    max_stress = np.amax(array, axis=0)
    return max_stress   # max_stress: tuple, with stress and corresponding strain info

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


# Main processing flow

result_list = []
meta_list = []
strength_list = []
slope_list = []

if args.select:
    select_split = str.split(args.select, ',')
    for elem in select_split:
        batch = int(str.split(elem, '-')[0])
        subbatch = int(str.split(elem, '-')[1])
        if len(str.split(elem, '-')) == 3:
            result = truncate_at(calculate(fetch_raw(batch, subbatch), find_dimensions(batch, subbatch)), int(str.split(elem, '-')[2]))
        else:
            result = calculate(fetch_raw(batch, subbatch), find_dimensions(batch, subbatch))
        result_list.append(result)
        strength_list.append(max_stress(result)[0])
        meta_list.append((batch, subbatch))

else:
    for i in range (0, batch_count):
        for j in range(0, subbatch_count):
            result = calculate(fetch_raw(i + 1, j + 1), find_dimensions(i + 1, j + 1))
            result_list.append(result)
            strength_list.append(max_stress(result)[0])
            meta_list.append((i+1, j+1))

for elem in result_list:
    if args.slope_range:
        slope_range = (int(str.split(args.slope_range, ',')[0]), int(str.split(args.slope_range, ',')[1]))
        slope_list.append(linear_regression(elem, from_to=slope_range)[0])
    else:
        slope_list.append(linear_regression(elem)[0])

logger.info("Young's modulus for plotted samples: %f, standard deviation: %f" % (np.average(slope_list), np.std(slope_list)))
logger.info("UTS for plotted samples: %f, standard deviation: %f" % (np.average(strength_list), np.std(strength_list)))

if args.compose_mode:
    plot_array(result_list, compose_mode=args.compose_mode, meta_map = meta_list, legends = args.legend)
else:
    plot_array(result_list, meta_map = meta_list, legends = args.legend)


# Testing code

# arr = calculate(fetch_raw(1,1), find_dimensions(1,1))
# plot_array([calculate(fetch_raw(1,1), find_dimensions(1,1)), calculate(fetch_raw(1,2), find_dimensions(1,2))], compose_mode='combined', meta_map = [(1,1), (1,2)])
# print("Max stress: " + str(max_stress(arr)))
# print(arr.shape)
# print(truncate_at(arr, 0.9).shape)
