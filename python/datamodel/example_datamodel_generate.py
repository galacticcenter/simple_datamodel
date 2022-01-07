# !/usr/bin/env python
# -*- coding: utf-8 -*-
#

import argparse
import yaml
import os
import pathlib
from astropy.io import fits
from jinja2 import Environment, FileSystemLoader


# example environment path to some data
os.environ['TEST_REDUX'] = (pathlib.Path('.').resolve() / 'data').as_posix()


class DatamodelGenerator(object):
    
    def __init__(self):
        self.output_yaml = None
        self.setup_jinja2()
        
    def __repr__(self):
        return '<DatamodelGenerator ()>'
    
    def setup_jinja2(self):
        """ Set up the Jinja2 template enviroment """
        loader = FileSystemLoader("templates")
        self.environment = Environment(loader=loader, trim_blocks=True, lstrip_blocks=True)

    def generate(self, species: str = 'test', path: str = '$TEST_REDUX/{version}/test-{id}.fits', 
                 keys: dict = {'version': 'v1', 'id': '123'}):
        """ Generate a data product species """
        
        self.file_species = species
        self.abstract_path = path
        self.env_label = path.split(os.sep)[0][1:]
        self.keywords = keys
        self.release = self.keywords['version']
        self.example = path.format(**keys)
        self.filepath = pathlib.Path(os.path.expandvars(self.example))

        self.output_yaml = f'products/yaml/{self.file_species}.yaml'
        self.output_md = f'products/md/{self.file_species}.md'
        
        self.generate_yaml_from_stub() 
             
    def generate_yaml_from_stub(self):
        """ Generate a base yaml file for a species of data product """ 

        # get the yaml template
        self.template = self.environment.get_template('stub.yaml')

        # generate initial content
        self.content = {'file_species': self.file_species, 
                   'filetype': self.filepath.suffix.upper()[1:], 
                   'releases': [self.release], 
                   'environments': [self.env_label]}

        # extract FITS content and add to yaml
        self.add_fits_content()

        # render content into the yaml stub, convert to dictionary and
        # format it to a string for writing to file
        yaml_out = yaml.load(self.template.render(self.content), Loader=yaml.FullLoader)
        self.content = yaml.dump(yaml_out, sort_keys=False)

        # write out yaml file
        self.write(self.output_yaml)
    
    def generate_md_from_yaml(self):
        """ Generate a final markdown file for a species of data product """ 

        # get the markdown template
        self.template = self.environment.get_template('stub.md')

        # construct the output markdown filepath
        if not self.output_yaml or not os.path.exists(self.output_yaml):
            raise AttributeError('No output yaml filepath set.  Make sure you generate a yaml file first.')
        #self.output_md = self.output_yaml.replace('yaml', 'md')

        # read the YAML contents
        with open(self.output_yaml, 'r') as file:
            yaml_content = yaml.load(file, Loader=yaml.FullLoader)

        # render the YAML contents into the markdown and write it out
        hdus = yaml_content['releases'][self.release]['hdus']
        self.content = self.template.render(content=yaml_content, hdus=hdus, selected_release=self.release)
        self.output = f'products/md/{self.file_species}.md'
        self.write(self.output_md)

    def write(self, output: str):
        """ Write content to a file """
        with open(output, 'w') as f:
            f.write(self.content)
     
    def add_fits_content(self):
        """ Add content from an example FITS file """

        # get the overall filesize
        self.content['filesize'] = self._format_bytes(self.filepath.stat().st_size)

        # create an entry for the current release of data
        self.content['release_content'] = {}
        self.content['release_content'][self.release] = {
            'path': self.abstract_path,
            'example': self.example,
            'environment': self.env_label,
            'hdus': {}
        }
        
        # extract and add HDU content
        hdus = {}
        with fits.open(self.filepath) as hdulist:
            for hdu_number, hdu in enumerate(hdulist):
                # convert an HDU to a dictionary
                row = self._convert_hdu_to_dict(hdu)

                # generate HDU extension number
                extno = f'hdu{hdu_number}'
                hdus[extno] = row
        self.content['release_content'][self.release]['hdus'] = hdus

    def _convert_hdu_to_dict(self, hdu: fits.hdu.base._BaseHDU, description: str = None) -> dict:
        """ Convert an HDU into a dictionary entry
        
        
        
        """
        header = hdu.header
                
        # create a new one
        row = {
            'name': hdu.name,
            'description': description or 'replace me description',
            'is_image': hdu.is_image,
            'size': self._format_bytes(hdu.size),
        }

        if hdu.is_image:
            row['header'] = []
            for key, value in header.items():
                if self._is_header_keyword(key=key):
                    column = {"key": key, "value": value, "comment": header.comments[key]}
                    row['header'].append(column)
        else:
            row['columns'] = {}
            for column in hdu.columns:
                row['columns'][column.name] = self._generate_column_dict(column)
        return row

    def _generate_column_dict(self, column: fits.Column) -> dict:
        """ Generates a dictionary entry for an Astropy binary table column """
        return {'name': column.name.upper(),
                'type': self._format_type(column.format),
                'unit': self._nonempty_string(column.unit),
                'description': self._nonempty_string()} 

    @staticmethod
    def _is_header_keyword(key: str = None) -> bool:
        """Test for hdu header keyword

        Returns
        -------
        bool
            ``True`` if `key` does *not* contain 'TFORM' or 'TTYPE'.
        """
        return tuple(key.find(f) for f in ("TFORM", "TTYPE")) == (-1, -1)

    @staticmethod
    def _nonempty_string(value: str = None) -> str:
        """Jinja2 Filter to map the format value to a string.

        Parameters
        ----------
        value : str?
            Not sure what type this is supposed to have.

        Returns
        -------
        string: str
            The string.
        """
        return f"{value}" if value else 'replace me - with content'

    @staticmethod
    def _format_type(value: str = None) -> str:
        """Jinja2 Filter to map the format type to a data type.

        Parameters
        ----------
        value : str?
            Not sure what type this is supposed to have.

        Returns
        -------
        str
            The data type.
        """
        fmap = {"A": "char", "I": "int16", "J": "int32", "K": "int64", "E": "float32",
                "D": "float64", "B": "bool", "L": "bool"}
        out = [
            val if value.isalpha() else "{0}[{1}]".format(val, value[:-1])
            for key, val in fmap.items()
            if key in value
        ]
        return out[0]  
    
    @staticmethod
    def _format_bytes(value: int = None) -> str:
        """Convert an integer to human-readable format.

        Parameters
        ----------
        value : int
            An integer representing number of bytes.

        Returns
        -------
        str
            Size of the file in human-readable format.
        """

        try:
            value = int(value)
        except:
            value = 0

        for unit in ("bytes", "KB", "MB", "GB"):
            if value < 1024:
                return "{0:d} {1}".format(int(value), unit)
            else:
                value /= 1024.0

        return "{0:3.1f} {1}".format(value, "TB")       
