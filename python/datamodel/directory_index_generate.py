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
os.environ['DR'] = (pathlib.Path('../').resolve()).as_posix()
release_version = 'DR2'

dr_base_path = '/g/ghez/data/dr/dr2/'

class directory_index_generator(object):
    """ Class for generating index files for directory indexes

    """
    
    dir_deque = deque()
    
    def __init__(self,
            base_html_path = f'{dr_base_path}/data_model/docs',
            base_yaml_path = f'{dr_base_path}/data_model/products/yaml',
        ):
        
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
    
    
