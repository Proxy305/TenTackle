# TenTackle

Tensile data analysis assisting tool for Shimazu.

## Introduction

TenTackle assists with analysis of raw tensile data from certain models of Shimazu universal testing machine.

**Warning**: TenTackle is NOT a general purpose software. Do not download if you are not aware of its intended usage.

## Function

- Plotting of stress/strain curve
    - Select curve(s) from one or more file
    - Automatically creates legends according to file name
- Customization of plotting
    - Specify unit for each axis
    - Plot all curves in one image, or in individual image
- Data analysis
    - UTS (Ultimate Tensile Strength)
    - Young's Modulus

## Deploy

### Dependency

- Python 3+
- NumPy
- Matplotlib
- Git (optional)

### Installation

1. Install Python3.
2. Open command prompt, install NumPy:

``` pip install numpy ```

3. Install Matplotlib:

``` pip install matplotlib```

4. Clone this repository to local, or download zip of this repository.
5. Now TenTackle is ready to use. Run in command prompt:

```
python3 main.py [-h] [-f FILE] [-i] [-v] [-l] [-c COMPOSE_MODE] [-s SELECT] [-r SLOPE_RANGE]
```

## Usage

### Command line mode

In command line mode, TenTackle takes one file, run once and quit. Suitable for single-shot tasks, or embedding TenTackle as a part of an automation process.

Simply run `main.py` with python3 as you would do to run another python script, with necessary command line parameters:

```
python3 main.py [-f FILE] ...
```

### Command line arguments

- Mandatory arguments
    - `-f FILE`, `--file FILE`: Specifies the .csv file to be processed


- Optional arguments:
    - `-h`, `--help`: show help message and exit
    - `-v`, `--verbose`: Increase output verbosity, for debugging purpose
    - `-l`, `--legend`: Switch on legends.
    - `-c COMPOSE_MODE`, `--compose_mode COMPOSE_MODE`: Specifies how to organize plotted curves of different samples. Available options:
        - `combined`: plot every curve in one image
        - `alone`: plot each curve in individual image
        - Default: `combined`
    - `-s SELECT`, `--select SELECT`: Specifies which samples are to be plotted. 
        - Format: batch-subbatch(-truncate_percentage),batch-subbatch
        - Default: All curves will be selected
    - `-r SLOPE_RANGE`, `--slope_range SLOPE_RANGE`: Specifies the range of data for slope/modulus measurement. Format: start_strain,end_strain

### Examples

Plot all curves in `test.csv`:
```
python3 main.py -f test.csv
```
Plot all curves in `test.csv`, with legends:
```
python3 main.py -f test.csv -l
```

Plot 1st, 3rd curve of batch 1 in `test.csv`, and truncate 3rd curve at 75% length:
```
python3 main.py -f test.csv -s 1-1,1-3-75
```

Plot the 1st, 3rd curve of batch 1 in `test.csv`, and use strain=0.001~0.01 as the range of modulus measurement:
```
python3 main.py -f test.csv -s 1-1,1-3 -r 0.001,0.01
```

### Interactive mode

For more complex tasks, like combining curves from multiple files, or previewing curves before plotting, you may wish to use interactive mode.

```
python3 main.py -i
```

Then follow the instructions on screen.

**Note**: All command line arguments, excluding `-v` will be ignored if parameter `-i` is given.

## Todo
- Add slope range selection to config file
- Add slope range selection for interactive mode

## Disclaimer

TenTackle comes with **ABSOLUTELY NO WARRANTY**. Use at your own risk.



