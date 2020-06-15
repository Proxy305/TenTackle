# TenTackle

![Preview](https://github.com/Proxy305/TenTackle/blob/gh-pages/main.png?raw=true)

Tensile data analysis assisting tool for Shimazu EZ series.

## Introduction

TenTackle assists with analysis of raw tensile data from certain models of Shimazu universal testing machine (namely, Shimazu EZ series).

**Warning**: TenTackle is NOT a general purpose software. Only download if you are authorized and are well aware of its intended usage.

## Function

- Raw data (.csv) processing
- Plotting of stress/strain curve
    - Select curve(s) from one or more file
    - Automatically creates curve labels base on file name
- Customization of plotting
    - Specify unit for each axis
    - Plot all curves in one image, or in individual image
- Simple Data analysis
    - UTS (Ultimate Tensile Strength), and strain at UTS
    - Young's Modulus
    - Toughness (Experimental)

## Deploy

### Dependency

- Python 3+
- NumPy
- Matplotlib
- wxPython (optional, GUI mode only)
- Git (optional, but recommended)

### Installation

1. Install [Python3](https://www.python.org/downloads/).
2. Open command prompt, install NumPy and matplotlib:

``` pip3 install numpy matplotlib ```

3. Install wxpython if you wish to use GUI mode. (Optional)

``` pip3 install wxpython ```

4. Clone this repository to local (recommended) (suppose you have git installed), 

``` git clone https://github.com/Proxy305/TenTackle.git ```

or download zip of this repository.

5. Now TenTackle is ready to use. Run in command prompt:

Single shot CLI mode:

```
python3 main.py [-h] [-f FILE] [-i] [-v] [-l] [-c COMPOSE_MODE] [-s SELECT] [-r SLOPE_RANGE]
```

Interactive CLI mode:

```
python3 main.py -i
```

GUI mode:

```
python3 tentackle-gui.py
```


## Usage

### GUI Mode (Experimental)

An experimental GUI is under development. To use the experimental GUI, execute `tentackle_gui.py`.

A brief introduction of toolbar tools can be found in [project wiki](https://github.com/Proxy305/TenTackle/wiki/GUI-Toolbar-tools).

### Single Shot command line mode

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

## Glossary

You may want to read about the [glossary](https://github.com/Proxy305/TenTackle/wiki/Glossary) of TenTackle before you get started. 

## Disclaimer

TenTackle comes with **ABSOLUTELY NO WARRANTY**. Use at your own risk. TenTackle is currently in pre-alpha quality, therefore, always backup important data, and cross-check the results with another general purpose tool (MS Excel, Origin Pro, etc.).



