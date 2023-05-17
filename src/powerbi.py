import logging
import sys
import os
from pathlib import Path
import json
import csv
import requests
import backoff
from requests.exceptions import ReadTimeout, ConnectionError


# Default Table Output Destination
DEFAULT_TABLE_SOURCE = os.path.join(Path(os.getcwd()).parent, "data/in/tables/")


class PowerBI:

    def __init__(self, oauth_token, workspace, dataset_type, dataset, input_tables, table_relationship):

        self.oauth_token = oauth_token
        self.workspace = workspace
        if workspace != "":
            self.workspace_url = "groups/{0}/".format(workspace)
        else:
            self.workspace_url = ""
        self.dataset_type = dataset_type
        self.dataset = dataset
        self.input_tables = input_tables
        self.input_table_columns = self.fetch_table_columns()
        self.dataset_payload = {
            "name": dataset,
            "defaultMode": "Push",
            "tables": self.construct_table_metadata(),
            "relationships": self.construct_relationship(table_relationship)
        }
        self.dataset_id = ''
        self.dataset_found = self.search_datasetid()

    @backoff.on_exception(backoff.expo, ReadTimeout, max_tries=5)
    def get_request(self, url, header, params):
        '''
        Basic GET request
        '''

        response = requests.get(url=url, params=params, headers=header)

        return response

    @backoff.on_exception(backoff.expo, (ReadTimeout, ConnectionError), max_tries=5)
    def post_request(self, url, header, payload):
        '''
        Basic POST request
        '''

        response = requests.post(
            url=url, headers=header, data=json.dumps(payload))

        return response

    def search_datasetid(self):
        '''
        Searching for dataset_id
        '''

        url = "https://api.powerbi.com/v1.0/myorg/{}datasets".format(
            self.workspace_url)
        header = {
            "Content-Type": "application/json",
            "Authorization": "Bearer "+self.oauth_token
        }
        response = self.get_request(url, header, {})
        if response.status_code != 200:
            if response.status_code == 400:
                logging.error(
                    "{} - Malformed request. Please contact support.".format(response.status_code))
            elif response.status_code == 401 or response.status_code == 403:
                logging.error(
                    "{0} - Authorization failed. Please check account privileges.".format(response.status_code))
            elif response.status_code == 500:
                logging.error(
                    "{} - Internal error. Please try again".format(
                        response.status_code)
                )
            sys.exit(1)

        response_json = response.json()
        datasets = response_json["value"]
        # logging.info("ALL DATASETS: {}".format(datasets))

        dataset_found = False
        dataset_id = ''
        for dataset in datasets:
            if self.dataset_type == 'Name':
                if dataset["name"] == self.dataset and dataset_found:
                    logging.error(
                        "Duplicated dataset name found. Please enter different dataset name or specify the dataset ID.")
                    sys.exit(1)
                if dataset["name"] == self.dataset and not dataset_found:
                    logging.info("Matching dataset found.")
                    dataset_id = dataset["id"]
                    dataset_found = True
            if self.dataset_type == 'ID':
                if dataset["id"] == self.dataset:
                    dataset_id = dataset["id"]
                    dataset_found = True

        if self.dataset_type == 'ID' and not dataset_found:
            logging.error(
                "Input dataset ID is not found. Please verify input value.")
            sys.exit(1)

        self.dataset_id = dataset_id
        if dataset_id != '':
            logging.info("Dataset: {} - {}".format(self.dataset, dataset_id))

        return dataset_found

    def create_dataset(self):
        '''
        Creating new dataset
        '''

        url = "https://api.powerbi.com/v1.0/myorg/{}datasets".format(
            self.workspace_url)
        header = {
            "Content-Type": "application/json",
            "Authorization": "Bearer {}".format(self.oauth_token)
        }

        response = self.post_request(url, header, self.dataset_payload)
        if response.status_code != 201:
            logging.error(
                "{0} - {1}".format(response.status_code, response.json()))
            sys.exit(1)

        dataset = response.json()
        self.dataset_id = dataset["id"]
        logging.info(f"Dataset created: {self.dataset_id}")

    def get_tables(self):
        '''
        Fetching available tables in the datasets
        '''

        url = "https://api.powerbi.com/v1.0/myorg/{0}datasets/{1}/tables".format(
            self.workspace_url, self.dataset_id)
        header = {
            "Content-Type": "application/json",
            "Authorization": "Bearer {}".format(self.oauth_token)
        }

        response = self.get_request(url, header, {})
        data = response.json()
        # logging.info("GET_TABLES: {}".format(data))
        all_tablenames = []
        try:
            for i in data["value"]:
                all_tablenames.append(i["name"])
        except Exception:
            pass

        return all_tablenames

    def put_table(self, tablename, payload):
        '''
        Creating new table within the dataset
        '''

        url = "https://api.powerbi.com/v1.0/myorg/{0}datasets/{1}/tables/{2}".format(
            self.workspace_url, self.dataset_id, tablename)
        header = {
            "Content-Type": "application/json",
            "Authorization": "Bearer {}".format(self.oauth_token)
        }

        response = requests.put(
            url=url, headers=header, data=payload)

        if response.status_code != 200:
            logging.error("Table creation failed. Please contact support.")
            sys.exit(1)

    def construct_relationship(self, config):
        '''
        Constructing relationship array
        '''

        relationship = []
        for link in config:
            relat_temp = {
                "crossFilteringBehavior": "Automatic",
                "name": "{0} - {1}".format(link["foreign_key_table"], link["primary_key_table"]),
                "fromColumn": link["foreign_key_column_name"],
                "fromTable": link["foreign_key_table"],
                "toColumn": link["primary_key_column_name"],
                "toTable": link["primary_key_table"]
            }
            relationship.append(relat_temp)

        return relationship

    def fetch_table_columns(self):
        '''
        Fetching column headers from manifest
        '''

        table_columns = {}

        for table in self.input_tables:
            with open(DEFAULT_TABLE_SOURCE+table+'.manifest') as json_file:
                manifest = json.load(json_file)
                table_columns[manifest["name"]] = manifest["columns"]

        return table_columns

    def _define_datatype(self, metadata_list):
        '''
        Defining input column datatype
        '''
        selected = False
        for meta in metadata_list:
            if meta["key"] == "KBC.datatype.basetype":
                if meta["value"] == "STRING":
                    return "String"
                elif meta["value"] == "DATE":
                    return "DateTime"
                elif meta["value"] == "TIMESTAMP":
                    return "DateTime"
                elif meta["value"] == "INTEGER":
                    return "Int64"
                elif meta["value"] == "FLOAT":
                    return "Decimal"
                elif meta["value"] == "NUMERIC":
                    return "Decimal"
                elif meta["value"] == "BOOLEAN":
                    return "Boolean"
                selected = True

        if not selected:
            return "String"

    def construct_table_metadata(self):
        '''
        Defining table columns' type
        '''

        table_definition = []
        for table in self.input_tables:
            with open(DEFAULT_TABLE_SOURCE+table+'.manifest') as json_file:
                manifest = json.load(json_file)

            table_def = {
                "name": manifest["name"],
                "columns": []
            }

            column_metadata = manifest["column_metadata"]
            for column in column_metadata:
                column_def = {
                    "name": column,
                    "dataType": self._define_datatype(column_metadata[column])
                }
                table_def["columns"].append(column_def)

            table_definition.append(table_def)
        return table_definition

    def convert_csv_to_rows(self, table_name):
        column_headers = self.input_table_columns[table_name]
        with open(DEFAULT_TABLE_SOURCE+table_name+'.csv', 'r') as file_in:
            reader = csv.DictReader(file_in, column_headers)
            headers = next(reader, None)  # noqa
            out = json.dumps([row for row in reader])

        return out

    def post_rows(self, tablename, rows):
        '''
        Posting rows
        '''

        url = f"https://api.powerbi.com/v1.0/myorg/{self.workspace_url}datasets/" \
              f"{self.dataset_id}/tables/{tablename}/rows"
        header = {"Authorization": f"Bearer {self.oauth_token}"}
        payload = {"rows": json.loads(rows)}

        try:
            response = self.post_request(url, header, payload)
        except ConnectionError:
            logging.error("Connection error while posting rows, backoff strategy applied.")
            sys.exit(1)

        if not response:
            logging.error("Failed to get response from Power BI API when posting dataset rows.")
            sys.exit(1)

        if response.status_code == 200:
            return

        if response.status_code == 429:
            logging.error("Posting rows issues occured. Please check the limitations of push datasets API")
            sys.exit(1)

        error_message = response.json()
        error_text = error_message.get("error", {}).get("message", "")
        if error_text:
            logging.error(
                f"{response.status_code} - Posting rows error has occured. Please contact support - {error_text}")
        else:
            logging.error(
                f"{response.status_code} - Unknown error happened during Posting rows. Please contact support "
                f"- {error_message}")

        sys.exit(1)

    def delete_rows(self, tablename):
        '''
        Removing rows from table
        '''

        logging.info("Dropping rows in table: {}".format(tablename))
        url = "https://api.powerbi.com/v1.0/myorg/{0}datasets/{1}/tables/{2}/rows".format(
            self.workspace_url, self.dataset_id, tablename)
        header = {
            "Authorization": "Bearer {}".format(self.oauth_token)
        }
        response = requests.delete(url, headers=header)
        if response.status_code != 200:
            error_message = response.json()
            logging.error(
                "{} - {}".format(response.status_code, error_message["error"]["message"]))
            sys.exit(1)

    def delete_dataset(self):
        '''
        Removing rows from table
        '''

        logging.info("Dropping datasets: {}".format(self.dataset_id))
        url = "https://api.powerbi.com/v1.0/myorg/{0}datasets/{1}".format(
            self.workspace_url, self.dataset_id)
        header = {
            "Authorization": "Bearer {}".format(self.oauth_token)
        }
        response = requests.delete(url, headers=header)
        if response.status_code != 200:
            logging.error(
                "{} - {}".format(response.status_code, response.json()))
