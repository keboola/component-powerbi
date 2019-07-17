'''
Template Component main class.

'''

import logging
import sys
import json
from datetime import datetime  # noqa
import pandas as pd

from kbc.env_handler import KBCEnvHandler
from kbc.result import KBCTableDef  # noqa
from kbc.result import ResultWriter  # noqa

from powerbi import PowerBI


# configuration variables
KEY_DATASET = 'dataset'
KEY_WORKSPACE = 'workspace'
KEY_INCREMENTAL = 'incremental'
KEY_TABLE_RELATIONSHIP = 'table_relationship'

MANDATORY_PARS = [
    KEY_DATASET,
    KEY_WORKSPACE,
    KEY_INCREMENTAL,
    KEY_TABLE_RELATIONSHIP
]
MANDATORY_IMAGE_PARS = []

# Default Table Output Destination
DEFAULT_TABLE_SOURCE = "/data/in/tables/"

APP_VERSION = '0.0.1'


class Component(KBCEnvHandler):

    def __init__(self, debug=False):
        KBCEnvHandler.__init__(self, MANDATORY_PARS)
        # override debug from config
        if self.cfg_params.get('debug'):
            debug = True

        self.set_default_logger('DEBUG' if debug else 'INFO')
        logging.info('Running version %s', APP_VERSION)
        logging.info('Loading configuration...')

        try:
            self.validate_config()
            self.validate_image_parameters(MANDATORY_IMAGE_PARS)
        except ValueError as e:
            logging.error(e)
            exit(1)

    def get_oauth_token(self, config):
        """
        Extracting OAuth Token out of Authorization
        """

        data = json.loads(config["oauth_api"]["credentials"]["#data"])
        token = data["oauth_token"]

        return token

    def get_tables(self, tables, mapping):
        """
        Evaluate input and output table names.
        Only taking the first one into consideration!
        mapping: input_mapping, output_mappings
        """
        # input file
        table_list = []
        for table in tables:
            name = table["full_path"] # noqa
            if mapping == "input_mapping":
                destination = table["destination"]
            elif mapping == "output_mapping":
                destination = table["source"]
            table_list.append(destination)

        return table_list

    def run(self):
        '''
        Main execution code
        '''

        # Get proper list of tables
        in_tables = self.configuration.get_input_tables()
        in_table_names = self.get_tables(in_tables, 'input_mapping')
        logging.info("IN tables mapped: "+str(in_table_names))

        # Activate when oauth in KBC is ready
        # Get Authorization Token
        # authorization = self.configuration.get_authorization()
        # oauth_token = self.get_oauth_token(authorization)

        # Configuration parameters
        params = self.cfg_params  # noqa
        workspace = params["workspace"]
        dataset_array = params["dataset"]
        dataset_type = dataset_array[0]["dataset_type"]
        dataset = dataset_array[0]["dataset_input"]
        table_relationship = params["table_relationship"]
        # TEMP authorization method
        oauth_token = params["#access_token"]

        _PowerBI = PowerBI(
            oauth_token=oauth_token,
            workspace=workspace,
            dataset_type=dataset_type,
            dataset=dataset,
            input_tables=in_table_names,
            table_relationship=table_relationship
        )

        # Dropping rows in table
        # will find better ways to load incrementally
        # currently have issues to load the same table consecutively
        if _PowerBI.dataset_found:
            for file in _PowerBI.input_table_columns:
                _PowerBI.delete_rows(file)

        # Creating dataset is not found
        if not _PowerBI.dataset_found:
            logging.info("Creating new dataset: {}".format(dataset))
            _PowerBI.create_dataset()
            # Search loop until the dataset is created
            while not _PowerBI.dataset_found:
                _PowerBI.dataset_found = _PowerBI.search_datasetid()

        for file in _PowerBI.input_table_columns:
            logging.info("Loading dataset: {0}".format(file))

            for chunk in pd.read_csv(DEFAULT_TABLE_SOURCE+file+'.csv', dtype=str, chunksize=1000):
                rows = chunk.to_json(orient='records')
                _PowerBI.post_rows(file, rows)

        logging.info("Extraction finished")


"""
        Main entrypoint
"""
if __name__ == "__main__":
    if len(sys.argv) > 1:
        debug = sys.argv[1]
    else:
        debug = True
    comp = Component(debug)
    comp.run()
