# !/usr/bin/env python
# -*- coding: utf-8 -*-
#

import argparse
import yaml
import os
import pathlib
import sys
from astropy.io import fits
from astropy.table import Table
from jinja2 import Environment, FileSystemLoader
from collections import deque

# example environment path to some data
os.environ['DR1'] = (pathlib.Path('../').resolve()).as_posix()
release_version = 'DR1'

class directory_index_generator(object):
    """ Class for generating index files for directory indexes

    """
    
    dir_deque = deque()
    
    def __init__(self,
            base_html_path = '/g/ghez/data/dr/dr1/data_model/docs',
            base_yaml_path = '/g/ghez/data/dr/dr1/data_model/products/yaml'):
        
        self.base_html_path = base_html_path
        self.base_yaml_path = base_yaml_path
        
        self.setup_jinja2()
        
        self.setup_initial_deque()
        
    def setup_jinja2(self):
        """ Set up the Jinja2 template enviroment """
        loader = FileSystemLoader("templates")
        self.environment = Environment(loader=loader, trim_blocks=True, lstrip_blocks=True)
        
    
    def setup_initial_deque(self):
        """ Set up initial deque with the top level directories
        """
        
        top_level_scan = os.scandir(self.base_yaml_path)
        
        for cur_item in top_level_scan:
            if cur_item.is_dir():
                dir_path = f'{self.base_yaml_path}/{cur_item.name}'
                self.dir_deque.append(dir_path)
        
        return
    
    def process_all_directories(self):
        """ Process all directories in the dir deque
        """
        
        # Process the dir deque, until none remain
        
        while len(self.dir_deque) > 0:
            cur_dir = self.dir_deque.popleft()
            
            self.process_directory(cur_dir)
        
        return
    
    def process_directory(self, directory):
        """ Process directory to determine all files and subdirectories
        """
        
        print(f'Dir: {directory}')
        
        # Trim the base path to generate heirarchy
        trim_prefix = self.base_yaml_path
        if trim_prefix[-1] != os.sep:
            trim_prefix = trim_prefix + os.sep
        
        trimmed_path = directory.replace(trim_prefix, '')
        
        file_heirarchy = trimmed_path.split(os.sep)
        
        dir_name = file_heirarchy[-1]
        
        file_heirarchy = file_heirarchy[:-1]
        
        # Scan the current directory for all contents
        dir_scan = os.scandir(directory)
        
        # Empty lists for all content directories and files
        cont_dirs = []
        cont_files = []
        
        # Go through each content item
        for cur_item in dir_scan:
            if cur_item.name == 'index.yaml':
                continue
            
            if cur_item.is_dir():
                cont_dirs.append(cur_item.name)
            elif cur_item.is_file():
                cont_files.append(cur_item.name)
        
        # Alphabetize each list
        cont_dirs.sort()
        cont_files.sort()
        
        # Add each directory to the dir deque
        if len(cont_dirs) > 0:
            for new_dir in cont_dirs:
                dir_path = f'{directory}/{new_dir}'
                self.dir_deque.append(dir_path)
        
        # Process each content file
        cont_file_names = []
        
        if len(cont_files) > 0:
            for cur_file in cont_files:
                with open(f'{directory}/{cur_file}', 'r') as yaml_file:
                    cur_yaml = yaml.load(yaml_file,
                                         Loader=yaml.FullLoader)
                
                cur_file_name = cur_yaml['general']['name']
                print(f'* {cur_file_name}')
            
                cont_file_names.append(cur_file_name)
                
                yaml_file.close()
        
        
        # Create index yaml for the directory
        out_dict = {}
        
        # Add general info
        out_dict['general'] = {'name': dir_name,
                               'file_heirarchy': file_heirarchy,
                              }
        
        if len(cont_dirs) > 0:
            directories_dict = {}
            
            for dir in cont_dirs:
                directories_dict[dir] = {'name': dir, 'dir': dir}
            
            out_dict['directories'] = directories_dict
        
        if len(cont_files) > 0:
            files_dict = {}
            
            for (file, file_name) in zip(cont_files, cont_file_names):
                files_dict[file_name] = {'name': file_name,
                                         'file': file.replace('.yaml', '')}
            
            out_dict['file_species'] = files_dict
        
        out_yaml = f'{directory}/index.yaml'
        with open(out_yaml, 'w') as out_yaml_file:
            yaml.dump(out_dict, out_yaml_file)
        
        
        # Create an html file from the index yaml
        self.create_html_output(out_yaml, trimmed_path)
            
        return
    
    def create_html_output(self, out_yaml, trimmed_path):
        """ Create an html output file from the output yaml and jinja template
        """
        
        out_html = self.base_html_path + os.sep + trimmed_path + os.sep + 'index.html'
        
        # Get the appropriate HTML template
        self.template = self.environment.get_template('index.html')
        
        # Read the YAML contents
        with open(out_yaml, 'r') as file:
            yaml_content = yaml.load(file, Loader=yaml.FullLoader)
        
        # Render the YAML contents into the HTML file and write it out
        self.content = self.template.render(content=yaml_content)
        
        with open(out_html, 'w') as out_html_file:
            out_html_file.write(self.content)
        
        return
    
    
    # def generate(self, species: str = 'test',
#                  path: str = '$DR1/{version}/test-{id}.fits',
#                  keys: dict = {'version': 'v1', 'id': '123'},
#                  is_table=False, table_kwargs=None,
#                  skip_yaml=False):
#         """ Generate a datamodel for a species of data product
#
#         Generate a YAML datamodel for a species of data product.  To generate a datamodel file,
#         provide the name of the file species, an abstract path template to the file, and a
#         dictionary of keyword values to be substituted into the abstract path template.
#
#         Parameters
#         ----------
#         species : str, optional
#             The name of the product file species, by default 'test'
#         path : str, optional
#             The abstract path to the file, by default '$TEST_REDUX/{version}/test-{id}.fits'
#         keys : dict, optional
#             Example keywords to build an example filepath, by default {'version': 'v1', 'id': '123'}
#         is_table : bool, optional
#             If True, makes writes column names when writing yaml, by default False
#         skip_yaml : bool, optional
#             If True, skips the yaml generation step, by default False
#         """
#
#         # set relevant information for the data product
#         self.file_species = species
#         self.abstract_path = path
#         self.env_label = path.split(os.sep)[0][1:]
#
#         # Derive file heirarchy
#         self.file_heirarchy = path.split(os.sep)[1:-1]
#         self.file_heirarchy_path = os.sep.join(self.file_heirarchy) + os.sep
#
#         self.is_table = is_table
#         self.table_kwargs = table_kwargs
#
#         # create the example filepath
#         self.keywords = keys
#         self.release = release_version
#         self.example = path.format(**keys)
#         self.filepath = pathlib.Path(os.path.expandvars(self.example))
#         self.filename = self.filepath.name
#
#         # create the output yaml and md datamodel directories
#         os.makedirs(f'products/yaml/{self.file_heirarchy_path}', exist_ok=True)
#         os.makedirs(f'products/md/{self.file_heirarchy_path}', exist_ok=True)
#         os.makedirs(f'products/html/{self.file_heirarchy_path}', exist_ok=True)
#
#         self.output_yaml = f'products/yaml/{self.file_heirarchy_path}/{self.file_species}.yaml'
#         self.output_md = f'products/md/{self.file_heirarchy_path}/{self.file_species}.md'
#         self.output_html = f'products/html/{self.file_heirarchy_path}/{self.file_species}.html'
#
#         # generate the yaml datamodel file
#         if not skip_yaml:
#             self.generate_yaml_from_stub()
#
#
#     def generate_yaml_from_stub(self):
#         """ Generate a yaml datamodel file for a species of data product
#
#         Generates a YAML datamodel file for a given data product species.  The initial YAML
#         file is generated using the stub.yaml template, and populated with content about
#         the file species and information extracted from the example FITS file.
#
#         By default, fields requiring human-editable content are initially set with
#         "replace me" text, indicating that field should be replaced by the user.  After
#         customizing the YAML content, the user can regenerate the markdown file
#         using the generate_md_from_yaml() method.
#
#         """
#
#         # get the yaml template
#         self.template = self.environment.get_template('stub.yaml')
#
#         # generate initial content
#         self.content = {
#             'file_species': self.file_species,
#             'filetype': self.filepath.suffix.upper()[1:],
#             'filename': self.filename,
#             'file_heirarchy': self.file_heirarchy,
#             'file_heirarchy_path': self.file_heirarchy_path,
#             'template': self.abstract_path,
#             'releases': [self.release],
#             'environments': [self.env_label],
#         }
#
#         # check if it's a FITS file so we can add its header keywords
#         if self.content['filetype'] == 'FITS':
#             # extract FITS content and add to yaml
#             self.add_fits_content()
#
#         # If filetype is a table file, add table content
#         if self.is_table:
#             self.add_table_content()
#
#         # render content into the yaml stub, convert to dictionary and
#         # format it to a string for writing to file
#         yaml_out = yaml.load(self.template.render(self.content), Loader=yaml.FullLoader)
#         self.content = yaml.dump(yaml_out, sort_keys=False)
#
#         # write out yaml file
#         print('yaml output: '+self.output_yaml)
#         self.write(self.output_yaml)
#
#     def generate_html_from_yaml(self):
#         """ Generate a final html file for a species of data product
#
#         Converts the YAML datamodel into a markdown file for display on
#         Github or integration into other web content.  Renders the YAML datamodel content
#         using a stub.md template file.  If the content of the YAML
#         datamodel file changes, or the md stub template changes, simply rerun this method to
#         regenerate the markdown file.
#
#         """
#
#         # get the markdown template
#         self.template = self.environment.get_template('stub.html')
#
#         # construct the output markdown filepath
#         if not self.output_yaml or not os.path.exists(self.output_yaml):
#             raise AttributeError('No output yaml filepath set.  Make sure you generate a yaml file first.')
#         #self.output_md = self.output_yaml.replace('yaml', 'md')
#
#         # read the YAML contents
#         with open(self.output_yaml, 'r') as file:
#             yaml_content = yaml.load(file, Loader=yaml.FullLoader)
#
#         # render the YAML contents into the markdown and write it out
#         if os.path.splitext(self.filepath)[1].upper() == '.FITS':
#             hdus = yaml_content['releases'][self.release]['hdus']
#             self.content = self.template.render(content=yaml_content, hdus=hdus, selected_release=self.release)
#         elif self.is_table:
#             columns = yaml_content['releases'][self.release]['columns']
#             self.content = self.template.render(content=yaml_content, columns=columns, selected_release=self.release)
#         else:
#             self.content = self.template.render(content=yaml_content,selected_release=self.release)
#         self.output = f'products/md/{self.file_species}.html'
#         self.write(self.output_html)
#
#     def generate_md_from_yaml(self):
#         """ Generate a final markdown file for a species of data product
#
#         Converts the YAML datamodel into a markdown file for display on
#         Github or integration into other web content.  Renders the YAML datamodel content
#         using a stub.md template file.  If the content of the YAML
#         datamodel file changes, or the md stub template changes, simply rerun this method to
#         regenerate the markdown file.
#
#         """
#
#         # get the markdown template
#         self.template = self.environment.get_template('stub.md')
#
#         # construct the output markdown filepath
#         if not self.output_yaml or not os.path.exists(self.output_yaml):
#             raise AttributeError('No output yaml filepath set.  Make sure you generate a yaml file first.')
#         #self.output_md = self.output_yaml.replace('yaml', 'md')
#
#         # read the YAML contents
#         with open(self.output_yaml, 'r') as file:
#             yaml_content = yaml.load(file, Loader=yaml.FullLoader)
#
#         # render the YAML contents into the markdown and write it out
#         if os.path.splitext(self.filepath)[1].upper() == '.FITS':
#             hdus = yaml_content['releases'][self.release]['hdus']
#             self.content = self.template.render(content=yaml_content, hdus=hdus, selected_release=self.release)
#         elif self.is_table:
#             columns = yaml_content['releases'][self.release]['columns']
#             self.content = self.template.render(content=yaml_content, columns=columns, selected_release=self.release)
#         else:
#             self.content = self.template.render(content=yaml_content, selected_release=self.release)
#         self.output = f'products/md/{self.file_species}.md'
#         self.write(self.output_md)
#
#     def write(self, output: str):
#         """ Write content to a file """
#
#         with open(output, 'w') as f:
#             f.write(self.content)
#
#     def add_table_content(self):
#         """ Add content form an example table file.
#
#         Creates a new entry in the YAML file for the given data product release
#         of a file species. Provides some basic information on the abstract path,
#         example used, environment variable label, along with Table column names.
#
#         New releases of the data product would go in the same datamodel file, but as
#         a new entry in the "releases" section of the YAML file.  This way you can keep
#         track of changes in data products over time/releases.
#
#         """
#         # Get the overall filesize
#         self.content['filesize'] = self._format_bytes(self.filepath.stat().st_size)
#
#         # create an entry for the current release of data
#         self.content['release_content'] = {}
#         self.content['release_content'][self.release] = {
#             'path': self.abstract_path,
#             'example': self.example,
#             'environment': self.env_label,
#             'columns': {}
#         }
#
#         # Extract table column headers
#         cols = {}
#
#         if self.table_kwargs != None:
#             in_table = Table.read(self.filepath, **self.table_kwargs)
#         else:
#             in_table = Table.read(self.filepath, format='ascii')
#
#
#         for col_number, col_name in enumerate(in_table.colnames, start=1):
#
#             # generate column number
#             col_id = f'col{col_number}'
#
#             column = (in_table[col_name])
#
#             col_row = {
#                 'name': col_name,
#                 'type': str(column.dtype),
#                 'unit': self._nonempty_string(column.unit),
#                 'description': self._nonempty_string()}
#
#             cols[col_id] = col_row
#
#         self.content['release_content'][self.release]['columns'] = cols
#
#
#     def add_fits_content(self):
#         """ Add content from an example FITS file
#
#         Creates a new entry in the YAML file for the given data product release
#         of a file species. Provides some basic information on the abstract path, example
#         used, environment variable label, along with information extract from the FITS
#         HDUs.
#
#         New releases of the data product would go in the same datamodel file, but as
#         a new entry in the "releases" section of the YAML file.  This way you can keep
#         track of changes in data products over time/releases.
#
#         """
#
#         # get the overall filesize
#         self.content['filesize'] = self._format_bytes(self.filepath.stat().st_size)
#
#         # create an entry for the current release of data
#         self.content['release_content'] = {}
#         self.content['release_content'][self.release] = {
#             'path': self.abstract_path,
#             'example': self.example,
#             'environment': self.env_label,
#             'hdus': {}
#         }
#
#         # extract and add HDU content
#         hdus = {}
#         with fits.open(self.filepath) as hdulist:
#             for hdu_number, hdu in enumerate(hdulist):
#                 # convert an HDU to a dictionary
#                 row = self._convert_hdu_to_dict(hdu)
#
#                 # generate HDU extension number
#                 extno = f'hdu{hdu_number}'
#                 hdus[extno] = row
#         self.content['release_content'][self.release]['hdus'] = hdus
#
#     def _convert_hdu_to_dict(self, hdu: fits.hdu.base._BaseHDU,
#                              description: str = None) -> dict:
#         """ Convert an HDU into a dictionary entry
#
#         Converts an Astropy FITS HDU extension into a dictionary entry
#         for the YAML file.  The dictionary contains general information such
#         as the name and description of the HDU, the extension size, and whether it's
#         an image or a table extension.  For image HDUs, it outputs the header keywords
#         and values.  For table HDUs, it outputs the binary table columns.
#
#         Parameters
#         ----------
#             hdu : fits.hdu.base._BaseHDU
#                 Any Astropy HDU object
#             description : str
#                 A description of the HDU
#
#         Returns
#         -------
#         dict
#             A dictionary representation of the HDU
#         """
#         # get the HDU header
#         header = hdu.header
#
#         # create a new dictionary entry
#         row = {
#             'name': hdu.name,
#             'description': description or 'replace me description',
#             'is_image': hdu.is_image,
#             'size': self._format_bytes(hdu.size),
#         }
#
#         # add the extension content
#         if hdu.is_image:
#             # add header keywords for image HDUs
#             row['header'] = []
#             for key, value in header.items():
#                 if self._is_header_keyword(key=key):
#                     column = {"key": key, "value": value, "comment": header.comments[key]}
#                     row['header'].append(column)
#         else:
#             # add table columns for table HDUs
#             row['columns'] = {}
#             for column in hdu.columns:
#                 row['columns'][column.name] = self._generate_column_dict(column)
#         return row
#
#     def _generate_column_dict(self, column: fits.Column) -> dict:
#         """ Generates a dictionary entry for an Astropy binary table column
#
#         Returns a dictionary representation of an Astropy binary table column,
#         containing the column name, data type, unit, and optional description.
#
#         Parameters
#         ----------
#         column : fits.Column
#             An astropy FITS binary table column
#
#         Returns
#         -------
#         dict
#             A dictionary entry for the column
#         """
#         return {'name': column.name.upper(),
#                 'type': self._format_type(column.format),
#                 'unit': self._nonempty_string(column.unit),
#                 'description': self._nonempty_string()}
#
#     @staticmethod
#     def _is_header_keyword(key: str = None) -> bool:
#         """Test for hdu header keyword
#
#         Returns
#         -------
#         bool
#             ``True`` if `key` does *not* contain 'TFORM' or 'TTYPE'.
#         """
#         return tuple(key.find(f) for f in ("TFORM", "TTYPE")) == (-1, -1)
#
#     @staticmethod
#     def _nonempty_string(value: str = None) -> str:
#         """Jinja2 Filter to map the format value to a string.
#
#         Parameters
#         ----------
#         value : str?
#             Not sure what type this is supposed to have.
#
#         Returns
#         -------
#         string: str
#             The string.
#         """
#         return f"{value}" if value else 'replace me - with content'
#
#     @staticmethod
#     def _format_type(value: str = None) -> str:
#         """Jinja2 Filter to map the format type to a data type.
#
#         Parameters
#         ----------
#         value : str?
#             Not sure what type this is supposed to have.
#
#         Returns
#         -------
#         str
#             The data type.
#         """
#         fmap = {"A": "char", "I": "int16", "J": "int32", "K": "int64", "E": "float32",
#                 "D": "float64", "B": "bool", "L": "bool"}
#         out = [
#             val if value.isalpha() else "{0}[{1}]".format(val, value[:-1])
#             for key, val in fmap.items()
#             if key in value
#         ]
#         return out[0]
#
#     @staticmethod
#     def _format_bytes(value: int = None) -> str:
#         """Convert an integer to human-readable format.
#
#         Parameters
#         ----------
#         value : int
#             An integer representing number of bytes.
#
#         Returns
#         -------
#         str
#             Size of the file in human-readable format.
#         """
#
#         try:
#             value = int(value)
#         except:
#             value = 0
#
#         for unit in ("bytes", "KB", "MB", "GB"):
#             if value < 1024:
#                 return "{0:d} {1}".format(int(value), unit)
#             else:
#                 value /= 1024.0
#
#         return "{0:3.1f} {1}".format(value, "TB")
#
#
# #
# # Command line interface
# #
# parser = argparse.ArgumentParser(description='Generate a datamodel for a FITS file')
# parser.add_argument('-f', '--file_species', help='The name of the file species', type=str, required=True)
# parser.add_argument('-p', '--path', help='The abstract path to the file', type=str, required=True)
# parser.add_argument("-k,", "--keywords", nargs="*", help="Keyword values that points to an example file", required=True)
# parser.add_argument('-m', '--markdown-only', help='Regenerate a markdown after customizing a yaml', action="store_true", required=False)
#
#
# def dmgen(args):
#     """ Command-line datamodel generator """
#     opts = parser.parse_args()
#
#     keys = dict([i.split('=') for i in opts.keywords])
#
#     dm = DatamodelGenerator()
#     dm.generate(species=opts.file_species, path=opts.path, keys=keys, skip_yaml=opts.markdown_only)
#     dm.generate_md_from_yaml()
#     dm.generate_html_from_yaml()
#
# if __name__ == '__main__':
#     dmgen(sys.argv[1:])
