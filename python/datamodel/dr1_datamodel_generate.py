# !/usr/bin/env python
# -*- coding: utf-8 -*-
#

import argparse
import yaml
import os
import pathlib
import sys
from astropy.io import fits
from jinja2 import Environment, FileSystemLoader


# example environment path to some data
os.environ['DR1'] = (pathlib.Path('../').resolve()).as_posix()
release_version = 'DR1'

class DatamodelGenerator(object):
    """ Class for generating datamodel for FITS files

    """
    
    def __init__(self):
        self.output_yaml = None
        self.setup_jinja2()
        
    def __repr__(self):
        return '<DatamodelGenerator ()>'
    
    def setup_jinja2(self):
        """ Set up the Jinja2 template enviroment """
        loader = FileSystemLoader("templates")
        self.environment = Environment(loader=loader, trim_blocks=True, lstrip_blocks=True)

    def generate(self, species: str = 'test', path: str = '$DR1/{version}/test-{id}.fits', 
                 keys: dict = {'version': 'v1', 'id': '123'}, skip_yaml=False):
        """ Generate a datamodel for a species of data product 

        Generate a YAML datamodel for a species of data product.  To generate a datamodel file, 
        provide the name of the file species, an abstract path template to the file, and a 
        dictionary of keyword values to be substituted into the abstract path template.  
        
        Parameters
        ----------
        species : str, optional
            The name of the product file species, by default 'test'
        path : str, optional
            The abstract path to the file, by default '$TEST_REDUX/{version}/test-{id}.fits'
        keys : dict, optional
            Example keywords to build an example filepath, by default {'version': 'v1', 'id': '123'}
        skip_yaml : bool, optional
            If True, skips the yaml generation step, by default False
        """
        
        # set relevant information for the data product
        self.file_species = species
        self.abstract_path = path
        self.env_label = path.split(os.sep)[0][1:]
        
        # create the example filepath
        self.keywords = keys
        self.release = release_version
        self.example = path.format(**keys)
        self.filepath = pathlib.Path(os.path.expandvars(self.example))
        self.filename = self.filepath.name
        
        # create the output yaml and md datamodel directories
        os.makedirs('products/yaml/', exist_ok=True)
        os.makedirs('products/md/', exist_ok=True)
        os.makedirs('products/html/', exist_ok=True)
        
        self.output_yaml = f'products/yaml/{self.file_species}.yaml'
        self.output_md = f'products/md/{self.file_species}.md'
        self.output_html = f'products/html/{self.file_species}.html'        
        
        # generate the yaml datamodel file
        if not skip_yaml:
            self.generate_yaml_from_stub()
            
             
    def generate_yaml_from_stub(self):
        """ Generate a yaml datamodel file for a species of data product
        
        Generates a YAML datamodel file for a given data product species.  The initial YAML
        file is generated using the stub.yaml template, and populated with content about
        the file species and information extracted from the example FITS file.  
        
        By default, fields requiring human-editable content are initially set with 
        "replace me" text, indicating that field should be replaced by the user.  After
        customizing the YAML content, the user can regenerate the markdown file
        using the generate_md_from_yaml() method.
        
        """ 

        # get the yaml template
        self.template = self.environment.get_template('stub.yaml')

        # generate initial content
        self.content = {'file_species': self.file_species, 
                   'filetype': self.filepath.suffix.upper()[1:], 
                   'filename': self.filename,
                   'template': self.abstract_path,
                   'releases': [self.release], 
                   'environments': [self.env_label]}

        # check if it's a FITS file so we can add its header keywords
        if self.content['filetype'] == 'FITS':
            # extract FITS content and add to yaml
            self.add_fits_content()

        # render content into the yaml stub, convert to dictionary and
        # format it to a string for writing to file
        yaml_out = yaml.load(self.template.render(self.content), Loader=yaml.FullLoader)
        self.content = yaml.dump(yaml_out, sort_keys=False)

        # write out yaml file
        print('yaml output: '+self.output_yaml)
        self.write(self.output_yaml)
    
    def generate_html_from_yaml(self):
        """ Generate a final html file for a species of data product 
        
        Converts the YAML datamodel into a markdown file for display on
        Github or integration into other web content.  Renders the YAML datamodel content
        using a stub.md template file.  If the content of the YAML
        datamodel file changes, or the md stub template changes, simply rerun this method to 
        regenerate the markdown file. 
        
        """ 

        # get the markdown template
        self.template = self.environment.get_template('stub.html')

        # construct the output markdown filepath
        if not self.output_yaml or not os.path.exists(self.output_yaml):
            raise AttributeError('No output yaml filepath set.  Make sure you generate a yaml file first.')
        #self.output_md = self.output_yaml.replace('yaml', 'md')

        # read the YAML contents
        with open(self.output_yaml, 'r') as file:
            yaml_content = yaml.load(file, Loader=yaml.FullLoader)

        # render the YAML contents into the markdown and write it out
        if os.path.splitext(self.filepath)[1].upper() == '.FITS':        
            hdus = yaml_content['releases'][self.release]['hdus']
            self.content = self.template.render(content=yaml_content, hdus=hdus, selected_release=self.release)
        else:
            self.content = self.template.render(content=yaml_content,selected_release=self.release)
        self.output = f'products/md/{self.file_species}.html'
        self.write(self.output_html)

    def generate_md_from_yaml(self):
        """ Generate a final markdown file for a species of data product 
        
        Converts the YAML datamodel into a markdown file for display on
        Github or integration into other web content.  Renders the YAML datamodel content
        using a stub.md template file.  If the content of the YAML
        datamodel file changes, or the md stub template changes, simply rerun this method to 
        regenerate the markdown file. 
        
        """ 

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
        if os.path.splitext(self.filepath)[1].upper() == '.FITS':
            hdus = yaml_content['releases'][self.release]['hdus']
            self.content = self.template.render(content=yaml_content, hdus=hdus, selected_release=self.release)
        else:
            self.content = self.template.render(content=yaml_content, selected_release=self.release)            
        self.output = f'products/md/{self.file_species}.md'
        self.write(self.output_md)
        
    def write(self, output: str):
        """ Write content to a file """

        with open(output, 'w') as f:
            f.write(self.content)
     
    def add_fits_content(self):
        """ Add content from an example FITS file
        
        Creates a new entry in the YAML file for the given data product release
        of a file species. Provides some basic information on the abstract path, example
        used, environment variable label, along with information extract from the FITS
        HDUs.
        
        New releases of the data product would go in the same datamodel file, but as
        a new entry in the "releases" section of the YAML file.  This way you can keep
        track of changes in data products over time/releases.
        
        """

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
        
        Converts an Astropy FITS HDU extension into a dictionary entry 
        for the YAML file.  The dictionary contains general information such
        as the name and description of the HDU, the extension size, and whether it's
        an image or a table extension.  For image HDUs, it outputs the header keywords
        and values.  For table HDUs, it outputs the binary table columns.
        
        Parameters
        ----------
            hdu : fits.hdu.base._BaseHDU
                Any Astropy HDU object
            description : str
                A description of the HDU

        Returns
        -------
        dict
            A dictionary representation of the HDU    
        """
        # get the HDU header
        header = hdu.header
                
        # create a new dictionary entry
        row = {
            'name': hdu.name,
            'description': description or 'replace me description',
            'is_image': hdu.is_image,
            'size': self._format_bytes(hdu.size),
        }

        # add the extension content
        if hdu.is_image:
            # add header keywords for image HDUs
            row['header'] = []
            for key, value in header.items():
                if self._is_header_keyword(key=key):
                    column = {"key": key, "value": value, "comment": header.comments[key]}
                    row['header'].append(column)
        else:
            # add table columns for table HDUs
            row['columns'] = {}
            for column in hdu.columns:
                row['columns'][column.name] = self._generate_column_dict(column)
        return row

    def _generate_column_dict(self, column: fits.Column) -> dict:
        """ Generates a dictionary entry for an Astropy binary table column 
        
        Returns a dictionary representation of an Astropy binary table column,
        containing the column name, data type, unit, and optional description.
        
        Parameters
        ----------
        column : fits.Column
            An astropy FITS binary table column
        
        Returns
        -------
        dict
            A dictionary entry for the column
        """
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


#
# Command line interface
#
parser = argparse.ArgumentParser(description='Generate a datamodel for a FITS file')
parser.add_argument('-f', '--file_species', help='The name of the file species', type=str, required=True)
parser.add_argument('-p', '--path', help='The abstract path to the file', type=str, required=True)
parser.add_argument("-k,", "--keywords", nargs="*", help="Keyword values that points to an example file", required=True)
parser.add_argument('-m', '--markdown-only', help='Regenerate a markdown after customizing a yaml', action="store_true", required=False)


def dmgen(args):
    """ Command-line datamodel generator """
    opts = parser.parse_args()

    keys = dict([i.split('=') for i in opts.keywords])

    dm = DatamodelGenerator()
    dm.generate(species=opts.file_species, path=opts.path, keys=keys, skip_yaml=opts.markdown_only)
    dm.generate_md_from_yaml()
    dm.generate_html_from_yaml()    

if __name__ == '__main__':
    dmgen(sys.argv[1:])
