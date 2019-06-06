# TenTackle

Tensile data analysis assisting tool for Shimazu.

## Introduction

TenTackle assists with analysis of raw tensile data from certain models of Shimazu universal testing machine.

Warning: TenTackle can only handle one specific format of raw data file. Do not download if you don't know what this is for.

## Function

- Plotting of stress/strain curve
    - Select curve(s) from one or more file
    - Automatically creates legends according to file name
- Data analysis
    - UTS (Ultimate Tensile Strength)
    - Young's Modulus

## Deploy

### Requisite

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
5. Now TenTackle is ready to use.

## Usage

```
main.py [-h] [-f FILE] [-i] [-v] [-l] [-c COMPOSE_MODE] [-s SELECT]
               [-r SLOPE_RANGE]

optional arguments:
  -h, --help            show this help message and exit
  -f FILE, --file FILE  Specifies the .csv file to be processed
  -i, --interactive     Use interactive mode
  -v, --verbose         Increase output verbosity
  -l, --legend          Switch on/off legends
  -c COMPOSE_MODE, --compose_mode COMPOSE_MODE
                        Specifies how to organize plotted curves of different
                        samples. Available options: combined, alone, sub
  -s SELECT, --select SELECT
                        Specifies which samples are to be plotted. Format:
                        batch-subbatch(-truncate_percentage),batch-subbatch
  -r SLOPE_RANGE, --slope_range SLOPE_RANGE
                        Specifies the range of data for slope/modulus
                        measurement. Format: start_strain,end_strain

```

## Disclaimer

TenTackle comes with **ABSOLUTELY NO WARRANTY**. Use at your own risk.



