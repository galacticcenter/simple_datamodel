# simple_datamodel
Example of a simple datamodel generator

- [simple_datamodel](#simple_datamodel)
  - [Dependencies](#dependencies)
  - [Structure](#structure)
    - [File Species](#file-species)
    - [Abstract Paths](#abstract-paths)
    - [Keywords](#keywords)
  - [Example Usage](#example-usage)
    - [Python Usage](#python-usage)
    - [Command-line Usage](#command-line-usage)
    - [YAML datamodel structure](#yaml-datamodel-structure)
    - [Markdown structure](#markdown-structure)
  - [Missing in this example](#missing-in-this-example)

## Dependencies

This example requires a few python libraries to run.  To install them, run:

```bash
pip install -r requirements.txt
```

It needs the following:

- **astropy** - for reading FITS files
- **pyyaml** - for reading and writing yaml files
- **jinja2** - for parsing and populating templated files

## Structure

This section describes the structure and organization of this datamodel example, along with definitions of terms and required inputs to the code.  Some definitions are:

- **file_species** - a name of a group of similar files
- **abstract_path** - a abstracted path with templated variables that points to a given file species
- **environment_variabel label** - an environment variable label used to define the absolute location of your data products
- **keyword variables** - a set of keyword variables to define an example filepath to an individual product

### File Species

A Datamodel is a representation of similar types of data files, referred to here as `file_species`.  A datamodel is generated for each unique `file_species`, not for individual files.  For example, say you have a software pipeline that produces an output data product for multiple target ids.  You change or update the software, and rerun the pipeline.    

Software Version 1:
- /software/output/path/data/v1/test-123.fits
- /software/output/path/data/v1/test-abc.fits

Software Version 2:
- /software/output/path/data/v2/test-123.fits
- /software/output/path/data/v2/test-abc.fits

These files are fundamentally the same, with the same FITS structure and represent the same type of file. They can be grouped together into a single `file_species`. 
The `file_species` name can be anything that refers generally to the type of data file but should be easily understood by users, and simpler is better.  In this case the `file_species` name might be `test`.  
### Abstract Paths

An abstract path is a generalized path that represents the path to the `file_species`, and can be resolved to an example of any individual file of that `file_species`.  To generalize a filepath, first replace any specific parameters in a filepath with general keywords that represent those parameters.  For example, with the above 4 paths we replace the following specific parameters:

- software versions v1 & v2 with the keyword `version`
- the target ids 123 and abc with the keyword `id`

The path becomes `/software/output/path/data/{version}/test-{id}.fits`.  We use bracket notation `{}` when specifying keyword variables inside of paths, similar to python f-strings or older string formatting syntax.  

Sometimes copies of data products live on different machines, or products are moved around into different directories.  In these cases, the absolute path `/software/output/path/data/` to the data products can change.  To generalize this, we define an **environment_variable label** to represent the absolute location of the file.  Let's define the output directory of our software reduction pipeline as the environment variable `TEST_REDUX=/software/output/path/data`.  To reference envvars use the `$` symbol, e.g. `$TEST_REDUX`.  If we ever move the files we only need to change the definition of `TEST_REDUX` and nothing else.  

Our final abstract path definition is then `$TEST_REDUX/{version}/test-{id}.fits`.  
### Keywords

We now have a general path that can be resolved to any particular data file in any location by changing `TEST_REDUX`, or supplying the keyword variables `version`, and `id`.

```python
i = '$TEST_REDUX/{version}/test-{id}.fits'

i.format(version='v1', id='123')
'$TEST_REDUX/v1/test-123.fits'

i.format(version='v2', id='abc')
'$TEST_REDUX/v2/test-abc.fits'
```

One our machine if we have the enviroment variable `TEST_REDUX` set to `/software/output/path/data`, we can easily resolve the full path in Python using `os.path.expandvars` or `pathlib.Path().resolve`.

```python
os.path.expandvars(i.format(version='v2', id='abc'))
'/software/output/path/data/v2/test-abc.fits'

pathlib.Path(i.format(version='v2', id='abc')).resolve()
'/software/output/path/data/v2/test-abc.fits'
```

## Example Usage

This code produces a machine-readable datamodel as a YAML format, as well as a markdown-format version. 
  
Test data file located at `/data/v1/test-123.fits`, and required inputs are the following:

- **file_species** name: `test`
- **environment variable label**: `TEST_REDUX`
- **abstract path**: `$TEST_REDUX/{version}/test-{id}.fits`
- **keyword variables**: 
  - version: `v1`
  - id: `123`

Given the above input, the code builds a path to the example FITS file, automatically reads in the file content, and populates the content into output datamodels using the following template files:

- **stub.yaml** - Jinja2 YAML datamodel template
- **stub.md** - Jinja2 markdown template

Run the following steps from the top of the repo

1. `cd` into `python/datamodel`
2. Run the following command: 

```bash
python example_datamodel_generate.py -f test -p '$TEST_REDUX/{version}/test-{id}.fits' -k version=v1 id=123
```
This command produces two files: a YAML datamodel for the file_species `test` located at `products/yaml/test.yaml` and a markdown version at `products/md/test.md`

3. Locate the datamodel `products/yaml/test/yaml`. See [YAML Struture](#yaml-datamodel-structure) for details on the file structure. Fields that should be replaced with human-edited content are indicated with the text `replace-me`.  Let's update the text for the `short` and `description` fields
4. Replace the `short` text with "this is a test file"
5. Replace the `description` text with "this is a longer description of what this file is.
6. To regenerate a markdown file with the newly edited YAML content, run the following command:

```bash
python example_datamodel_generate.py -f test -p '$TEST_REDUX/{version}/test-{id}.fits' -k version=v1 id=123 -m
```
7.  The markdown file has now been updated with your human-curated content.


### Python Usage

```python

# import the generator class
from example_datamodel_generate import DatamodelGenerator

# create the datamodel generator
dm = DatamodelGenerator()

# generate a datamodel for the default test example
dm.generate()

# (re)generate the markdown file
dm.generate_md_from_yaml()
```
Manually edit the YAML file with custom human-edited content, and then rerun the `dm.generate_md_from_yaml()` method to update the markdown file with your custom content.

### Command-line Usage

Run the command initially to generate a YAML datamodel file.

```bash
python example_datamodel_generate.py -f test -p '$TEST_REDUX/{version}/test-{id}.fits' -k version=v1 id=123
```

Manually edit the YAML file with custom human-edited content.  Rerun the script with the `-m` or `--markdown-only` keyword argument.

```bash
python example_datamodel_generate.py -f test -p '$TEST_REDUX/{version}/test-{id}.fits' -k version=v1 id=123 -m
```

### YAML datamodel structure

The YAML file has is structured as a dictionary with the following sections:

- **general** - basic information on the data product
- **changelog** - an automaticallly populated dictionary of differences between FITS files
- **releases** - an automatically populated dictionary of the example HDU content for a given file from a given release of data

The YAML file contains fields with the text `replace me`.  These indicate fields that should be replaced with human-curated content, to customize the datamodel. 

During datamodel genereation, the `releases` section, will get populated with an `hdus` key containing an entry
for every HDU extension in the example FITS file. 

### Markdown structure

The markdown file has the following structure:

- **Basic Information** - basic product information pulled from the general YAML section
- **Changelog** - the YAML changelog section, if any
- **Example HDU** - an HDU of an example file of the specified version

## Missing in this example

- YAML validation
- Changelog
- YAML caching