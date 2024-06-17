import base64
from xml.etree import ElementTree as ET
from copy import deepcopy

class CountySelector():
    def __init__(self):
        """County selection with animation. Coding by Mao-Huan Hsu."""
        map_image_path = './static/images/taiwan_map.svg'
        self.xml_root = ET.parse(map_image_path).getroot()
        self.svg_prefix = '{http://www.w3.org/2000/svg}'
        self.counties = self.get_county_names()
        
    def get_county_names(self):
        elem_county = self.xml_root.find(f"{self.svg_prefix}g[@id='county']")
        counties = [e.text for e in elem_county.iter(f"{self.svg_prefix}title")]

        return counties

    def copy_map(self, root=None):
        if root:
            copied_map = deepcopy(root)
        else:
            copied_map = deepcopy(self.xml_root)
            
        return copied_map

    def update_map(self, root, rand_id):
        elem_county = root.find(f"{self.svg_prefix}g[@id='county']")
        counties = [e for e in elem_county.iter(f"{self.svg_prefix}path")]
        counties[rand_id].set('fill', '#fc3d3d')

        return self.show_map(root)
    
    def save_map(self, root, fixed_id):
        elem_county = root.find(f"{self.svg_prefix}g[@id='county']")
        counties = [e for e in elem_county.iter(f"{self.svg_prefix}path")]
        counties[fixed_id].set('fill', '#f7da36')

        return root

    def show_map(self, root):
        xml_string = ET.tostring(root, encoding='utf-8', method='xml')
        image_url = 'data:image/svg+xml;base64,' + base64.b64encode(xml_string).decode('utf-8')

        return image_url
    