'''
Template Component main class.

'''

import logging
import logging_gelf.handlers
import logging_gelf.formatters
import os
import sys
import json
from datetime import datetime  # noqa
import time
import pandas as pd
import requests

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

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)-8s : [line:%(lineno)3s] %(message)s',
    datefmt="%Y-%m-%d %H:%M:%S")

if 'KBC_LOGGER_ADDR' in os.environ and 'KBC_LOGGER_PORT' in os.environ:

    logger = logging.getLogger()
    logging_gelf_handler = logging_gelf.handlers.GELFTCPSocketHandler(
        host=os.getenv('KBC_LOGGER_ADDR'), port=int(os.getenv('KBC_LOGGER_PORT')))
    logging_gelf_handler.setFormatter(
        logging_gelf.formatters.GELFFormatter(null_character=True))
    logger.addHandler(logging_gelf_handler)

    # remove default logging to stdout
    logger.removeHandler(logger.handlers[0])


APP_VERSION = '0.0.6'


class Component(KBCEnvHandler):

    def __init__(self, debug=False):
        KBCEnvHandler.__init__(self, MANDATORY_PARS)
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

        data = config["oauth_api"]["credentials"]
        data_encrypted = json.loads(
            config["oauth_api"]["credentials"]["#data"])
        client_id = data["appKey"]
        client_secret = data["#appSecret"]
        refresh_token = data_encrypted["refresh_token"]

        url = "https://login.microsoftonline.com/common/oauth2/token"
        header = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        payload = {
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "refresh_token",
            "resource": "https://analysis.windows.net/powerbi/api",
            "refresh_token": refresh_token
        }

        response = requests.post(
            url=url, headers=header, data=payload)

        if response.status_code != 200:
            logging.error(
                "Unable to refresh access token. Please reset the account authorization.")
            sys.exit(1)

        data_r = response.json()
        token = data_r["access_token"]

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
            name = table["full_path"]  # noqa
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
        # Handling input error
        if len(in_table_names) == 0:
            logging.error(
                "No tables are found in input mapping to export into PowerBI.")
            sys.exit(1)

        # Activate when oauth in KBC is ready
        # Get Authorization Token
        authorization = self.configuration.get_authorization()
        oauth_token = self.get_oauth_token(authorization)

        # Configuration parameters
        params = self.cfg_params  # noqa
        # Error handler, if there is nothing in the configuration
        if params == {}:
            logging.error("There are no inputs in the configurations. Please configure.")
            sys.exit(1)
        workspace = params["workspace"]
        dataset_array = params["dataset"]
        # Handling input error
        if len(dataset_array) == 0:
            logging.error(
                "Dataset configuration is missing. Please specify dataset.")
            sys.exit(1)

        dataset_type = dataset_array[0]["dataset_type"]
        dataset = dataset_array[0]["dataset_input"]
        table_relationship = params["table_relationship"]
        # TEMP authorization method
        # oauth_token = params["#access_token"]

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
            all_tables = _PowerBI.get_tables() # noqa
            drop_file_bool = True
            """for file in _PowerBI.input_table_columns:
                logging.info("FILE: {}".format(file))
                if file not in all_tables:
                    drop_file_bool = False
                    if dataset_type != "ID":
                        logging.info("DELETE DATASET")
                        _PowerBI.dataset_found = False
                        _PowerBI.delete_dataset()
                    else:
                        logging.error(
                            "Schema does not match. Please create a new dataset or modify the input tables to match "
                            + "the input dataset_id's schema")
                        sys.exit(1)"""

            if drop_file_bool:
                for file in _PowerBI.input_table_columns:
                    _PowerBI.delete_rows(file)

        # Creating dataset is not found
        if not _PowerBI.dataset_found:
            logging.info("Creating new dataset: {}".format(dataset))
            _PowerBI.create_dataset()
            # Search loop until the dataset is created
            while not _PowerBI.dataset_found:
                _PowerBI.dataset_found = _PowerBI.search_datasetid()

        # API limits parameters
        start_time = time.time()
        one_min_in_sec = 60
        num_of_post_request = 0
        for file in _PowerBI.input_table_columns:
            logging.info("Loading table: {0}".format(file))

            for chunk in pd.read_csv(DEFAULT_TABLE_SOURCE+file+'.csv', dtype=str, chunksize=10000):
                rows = chunk.to_json(orient='records')
                if (int(time.time())-start_time) <= one_min_in_sec and num_of_post_request <= 120:
                    _PowerBI.post_rows(file, rows)
                    num_of_post_request += 1
                else:
                    wait_sec = one_min_in_sec - (int(time.time())-start_time)
                    if wait_sec > 0:
                        time.sleep(wait_sec)
                    start_time = time.time()
                    _PowerBI.post_rows(file, rows)
                    num_of_post_request = 1

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
