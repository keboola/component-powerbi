Each extractor configuration can only exported `one` dataset to PowerBI. Writer will be using the data_type defined in metadata in Keboola Storage. If data_type is not configured for the input table, writer will automatically assign that column as `string`.

## PowerBI API Limitations

To POST Rows

1. 75 max columns
2. 75 max tables
3. 10,000 max rows per single POST rows request
4. 1,000,000 rows added per hour per dataset
5. 120 POST rows requests per minute per dataset
6. If table has 250,000 or more rows, 120 POST rows requests per hour per dataset
7. 200,000 max rows stored per table in FIFO dataset
8. 5,000,000 max rows stored per table in 'none retention policy' dataset
9. 4,000 characters per value for string column in POST rows operation

## Parameters

1. Workspace
    - The workspace where the user wants to output their dataset.
    - Please leave this blank if the user is exporting the dataset into the signed in account's "My Workspace"

2. Dataset - Required
    - Name or ID of the dataset the user wish to name this configuration
    ## WARNING
        1. If the same dataset name exists in the same Workspace with a different schema, writer will drop the existing dataset in the Workspace and re-create a new one with the input dataset name
        2. If the ID of the dataset is specified, users are required to ensure the input schema matches with the destinated table's schema in PowerBI
        3. If input dataset name is found multiple times in the same Workspace, writer will ask users to specify the dataset ID instead and terminate the current run
        4. If specified dataset ID is not found, the writer will fail with an error message

3. Incremental load
    - *In Development*

4. Table Relationships
    - User are required to configure this Relationship table if user is hoping to link tables via primary keys and foreign keys. Writer will fail if relationship is not configured properly.
    - Required Parameters:
        1. Primary Key Table
            - The name of the source table
        2. Primary Key Column Name
            - Primary key of the source table
            - Input format: ```string```
        3. Foreign Key Table
            - The name of the target table
        4. Foreign Key Column Name
            - Primary key of the target table
            - Input format: ```string```

        ### Example

        Tables|Primary Key
        -|-
        `Order`|order_id
        `Order-Item`|order_item_id

        `Order` table contains a list of invoices; `Order-Item` contains the items that are purchased. Every `Order-Item` should have an `Order`'s order_id attached to it.

        ### Relationship

        `Order`|-|`Order-Item`
        -|-|-
        One|to|Many

        ### Sample Relationship Configuration

        Primary Key Table|Primary Key Column Name|Foreign Key Table|Foreign Key Column Name
        -|-|-|-
        `Order`|order_id|`Order-Item`|order_id

For more details, please visit [here](https://bitbucket.org/kds_consulting_team/kds-team.wr-powerbi/src/master/README.md).


        
