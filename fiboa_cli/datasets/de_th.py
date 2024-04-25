from ..convert_utils import convert as convert_

import re
import pandas as pd

URI = "https://www.geoproxy.geoportal-th.de/download-service/opendata/agrar/DGK_Thue.zip"

ID = "de_th"
TITLE = "Field boundaries for Thuringia, Germany"
DESCRIPTION = """For use in the application procedure of the Integrated Administration and Control System (IACS), digital data layers are required that represent the current situation of agricultural use with the required accuracy. The field block is a contiguous agricultural area of one or more farmers surrounded by permanent boundaries. The field block thus contains information on the geographical location of the outer boundaries of the agricultural area. Reference parcels are uniquely numbered throughout Germany (Feldblockident - FBI). They also have a field block size (maximum eligible area) and a land use category.

The following field block types exist:

- Utilized agricultural area (UAA)
- Landscape elements (LE)
- Special use areas (SF)
- Forest areas (FF)

The field blocks are classified separately according to the main land uses of arable land (`AL`), grassland (`GL`), permanent crops (`DA`, `OB`, `WB`), including agroforestry systems with an approved utilization concept and according to the BNK for no "agricultural land" (`NW`, `EF` and `PK`) and others.

Landscape elements (LE) are considered part of the eligible agricultural area under defined conditions. In Thuringia, these permanent conditional features are designated as a separate field block (FB) and are therefore part of the Thuringian area reference system (field block reference). They must have a clear reference to an UAA (agricultural land), i.e. they are located within an arable, permanent grassland or permanent crop area or border directly on it.

To produce the DGK-Lw, (official) orthophotos from the Thuringian Land Registry and Surveying Administration (TLBG) and orthophotos from the TLLLR's own aerial surveys are interpreted. The origin of this image data is 50% of the state area each year, so that up-to-date image data is available for the entire Thuringian state area every year."""

# Taken from http://osmtipps.lefty1963.de/2008/10/bundeslnder.html
BBOX = [9.8778443239,50.2042330625,12.6531964048,51.6490678544]

PROVIDER_NAME = "Thüringer Landesamt für Landwirtschaft und Ländlichen Raum"
PROVIDER_URL = "https://geomis.geoportal-th.de/geonetwork/srv/ger/catalog.search#/metadata/D872F2D6-60BC-11D6-B67D-00E0290F5BA0"
ATTRIBUTION = "© GDI-Th"
LICENSE = "dl-de/by-2-0"

EXTENSIONS = [
    "https://fiboa.github.io/flik-extension/v0.1.0/schema.yaml"
]

COLUMNS = {
    'geometry': 'geometry',
    'BEZUGSJAHR': 'valid_year',
    'FBI': 'flik',
    'FBI_KURZ': 'id',
    'FB_FLAECHE': 'area',
    'FBI_VJ': 'flik_last_year',
    'FB_FL_VJ': 'area_last_year',
    'TK10': 'tk10',
    'AFO': 'afo',
# Don't add LF, all values are 'LF' after the filter below
#   'LF': 'lf',
    'BNK': 'bnk',
    'KOND_LE': 'kond_le',
    'AENDERUNG': 'change',
    'GEO_UPDAT': 'determination_datetime'
}

delim = re.compile(r'\s*,\s*')
COLUMN_MIGRATIONS = {
    'AFO': lambda column: column.map({'J': True}).fillna(value=False),
    'KOND_LE': lambda column: column.map({'J': True}).fillna(value=False),
    'AENDERUNG': lambda column: column.map({'Geaendert': True, 'Unveraendert': False, 'Neu': None}),
    'FBI_VJ': lambda column: column.str.split(delim, regex = True)
}

def migrate(gdf):
    col = "GEO_UPDAT"
    gdf[col] = pd.to_datetime(gdf[col], format = "%d.%m.%Y", utc = True)
    return gdf

MIGRATION = migrate

COLUMN_FILTERS = {
    "LF": lambda col: col == "LF"
}

# Schemas for the fields that are not defined in fiboa
# Keys must be the values from the COLUMNS dict, not the keys
MISSING_SCHEMAS = {
    'required': [
        'valid_year',
        'area_last_year',
        'tk10',
        'bnk'
    ],
    'properties': {
        'valid_year': {
            # could also be uint16 or string
            'type': 'int16'
        },
        'flik_last_year': {
            'type': 'array',
            'items': {
                # as define in the flik extension schema
                'type': 'string',
                'minLength': 16,
                'maxLength': 16,
                'pattern': "^[A-Z]{2}[A-Z0-9]{2}[A-Z0-9]{2}[A-Z0-9]{10}$"
            }
        },
        'area_last_year': {
            # as define in the area schema
            'type': 'float',
            'exclusiveMinimum': 0,
            'maximum': 100000
        },
        'tk10': {
            'type': 'string'
        },
        'afo': {
            'type': 'boolean'
        },
        'bnk': {
            'type': 'string'
        },
        'kond_le': {
            'type': 'boolean'
        },
        'change': {
            'type': 'boolean'
        }
    }
}


# Conversion function, usually no changes required
def convert(output_file, cache_file = None, source_coop_url = None, collection = False):
    """
    Converts the field boundary datasets to fiboa.

    For reference, this is the order in which the conversion steps are applied:
    0. Read GeoDataFrame from file
    1. Run global migration (if provided through MIGRATION)
    2. Run filters to remove rows that shall not be in the final data
       (if provided through COLUMN_FILTERS)
    3. Run column migrations (if provided through COLUMN_MIGRATIONS)
    4. Duplicate columns (if an array is provided as the value in COLUMNS)
    5. Rename columns (as provided in COLUMNS)
    6. Remove columns (if column is not present as value in COLUMNS)
    7. Create the collection
    8. Change data types of the columns based on the provided schemas
    (fiboa spec, extensions, and MISSING_SCHEMAS)
    9. Write the data to the Parquet file

    Parameters:
    output_file (str): Path where the Parquet file shall be stored.
    cache_file (str): Path to a cached file of the data. Default: None.
                      Can be used to avoid repetitive downloads from the original data source.
    source_coop_url (str): URL to the (future) Source Cooperative repository. Default: None
    collection (bool): Additionally, store the collection separate from Parquet file. Default: False
    kwargs: Additional keyword arguments for GeoPandas read_file() function.
    """
    convert_(
        output_file,
        cache_file,
        URI,
        COLUMNS,
        ID,
        TITLE,
        DESCRIPTION,
        BBOX,
        migration=MIGRATION,
        provider_name=PROVIDER_NAME,
        provider_url=PROVIDER_URL,
        source_coop_url=source_coop_url,
        extensions=EXTENSIONS,
        missing_schemas=MISSING_SCHEMAS,
        column_migrations=COLUMN_MIGRATIONS,
        column_filters=COLUMN_FILTERS,
        attribution=ATTRIBUTION,
        store_collection=collection,
        license=LICENSE
    )
