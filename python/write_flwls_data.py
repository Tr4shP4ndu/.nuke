DATA = {
    "SELECT": {
        "write_node": "",
        "filetypes": [" "],
        "input_names": "",
        "digits": "",
        "input_positions": [],
        "color": "513a00ff",
        "actions": ["invisible", ["WriteGroupBegin", "write_tab", "write_geo_tab", "smartvector_tab", "copycat_tab", "progress_tab"]]
    },
    "PREPGEO": {
        "write_node": "WriteGeo",
        "name_node": "geo",
        "filetypes": [" ", "ABC", "OBJ", "FBX"],
        "input_names": "INPUT_GEO",
        "digits": ".%06d",
        "color": "3B7A57ff",
        "actions": ["visible", ["WriteGroupBegin", "write_geo_tab"]]
    },
    "COPYCAT": {
        "write_node": "CopyCat",
        "name_node": "copycat",
        "filetypes": [" ", "CAT"],
        "input_names": ["INPUT_COPYCAT", "GROUNDTRUTH"],
        "digits": "",
        "color": "B84A46ff",
        "actions": ["visible", ["WriteGroupBegin", "copycat_tab", "progress_tab"]]
    },
    "SMARTVECTOR": {
        "write_node": ["SmartVector", "Write"],
        "name_node": ["smartvector_flw", "Write"],
        "filetypes": [" ", "EXR"],
        "input_names": ["INPUT_SMARTVECTOR", "MATTE"],
        "digits": ".%06d",
        "color": "ffffffff",
        "actions": ["visible", ["WriteGroupBegin", "write_tab", "smartvector_tab"]]
    },
    "PREPCOMP": {
        "write_node": "Write",
        "name_node": "Write",
        "filetypes": [" ", "EXR", "JPEG", "PNG", "CIN", "DPX", "MOV", "HDR", "TARGA", "TIFF"],
        "input_names": "INPUT_PREPCOMP",
        "digits": ".%06d",
        "color": "E3A300ff",
        "actions": ["visible", ["WriteGroupBegin", "write_tab"]]
    },
    "FLOATING_FACE": {
        "write_node": "Write",
        "name_node": "Write",
        "filetypes": [" ", "EXR"],
        "input_names": "INPUT_FLOATING_FACE",
        "digits": ".%06d",
        "color": "E3A300ff",
        "actions": ["visible", ["WriteGroupBegin", "write_tab"]]
    },
    "REVIEW_EXR": {
        "write_node": "Write",
        "name_node": "Write",
        "filetypes": [" ", "EXR"],
        "input_names": "INPUT_REVIEW_EXR",
        "digits": ".%06d",
        "color": "E3A300ff",
        "actions": ["visible", ["WriteGroupBegin", "write_tab"]]
    },
    "REVIEW_MOV": {
        "write_node": "Write",
        "name_node": "Write",
        "filetypes": [" ", "MOV"],
        "input_names": "INPUT_REVIEW_MOV",
        "digits": ".%06d",
        "color": "E3A300ff",
        "actions": ["visible", ["WriteGroupBegin", "write_tab"]]
    },
    "WRITE_FLWLS_TABS": {
        "all_tabs": ["write_tab", "write_geo_tab", "smartvector_tab", "copycat_tab", "progress_tab"]
    }
}