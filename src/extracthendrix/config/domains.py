import numpy as np

"""
A domain can be defined by coordinates (lat/lon) or indices on the grid of the model.

Indices are only valid for AROME and AROME_SURFACE for the moment.

If indices and coordinates are given, indices will be prioritized.
"""

domains_descriptions = {
        # alp
        'alp': {'first_i': np.intp(900), 'last_i': np.intp(1075), 'first_j': np.intp(525), 'last_j': np.intp(750),
                'lon_llc': 5.0144, 'lat_llc': 43.88877, 'lon_urc': 8.125426, 'lat_urc': 46.395446},
        # pyr
        'pyr': {'first_i': np.intp(480), 'last_i': np.intp(785), 'first_j': np.intp(350), 'last_j': np.intp(475),
                'lon_llc': -1.65953, 'lat_llc': 41.825578, 'lon_urc': 3.139407, 'lat_urc':43.3406425},
        # test_alp
        'test_alp': {'first_i': np.intp(1090), 'last_i': np.intp(1100), 'first_j': np.intp(740), 'last_j': np.intp(750),
                     'lon_llc': 8.36517, 'lat_llc': 46.26501, 'lon_urc': 8.5477, 'lat_urc': 46.3719},
        # jesus
        'jesus': {'first_i': np.intp(551), 'last_i': np.intp(593), 'first_j': np.intp(414), 'last_j': np.intp(435),
                  'lon_llc': -0.582946, 'lat_llc': 42.60378, 'lon_urc': 0.074149, 'lat_urc': 42.8626},
        # switzerland
        'switzerland': {'first_i': np.intp(931), 'last_i': np.intp(1211), 'first_j': np.intp(671),
                        'last_j': np.intp(899), 'lon_llc': 5.609121, 'lat_llc': 45.5642, 'lon_urc': 10.6848,
                        'lat_urc': 47.97167},
        # corsica
        'corsica': {'first_i': np.intp(1124), 'last_i': np.intp(1197), 'first_j': np.intp(314), 'last_j': np.intp(482),
                    'lon_llc': 8.33922, 'lat_llc': 41.26144, 'lon_urc': 9.718, 'lat_urc': 43.14122}
}
