# Keboola PowerBI Writer

PowerBI is a business analytics solution that aims to provide interactive visualization and share insights across your organization.
PowerBI writer's purpose is strive to aid users defining designated table relationships and exporting structured and enriched tables into PowerBI business analytics platform.

## PowerBI API Limitations

1. 75 max columns
2. 1,000,000 rows added per hour per dataset
3. 120 POST rows requests per minute per dataset
4. 200,000 max rows stored per table in FIFO dataset
5. 5,000,000 max rows stored per table
6. 4,000 characters per value for string column

## Configurations

Each extractor configuration can only exported `one` dataset to PowerBI. Writer will be using the data_type defined in metadata in Keboola Storage. If data_type is not configured for the input table, writer will automatically assign that column as `string`.

1. Access Token - Required
    - TEMPORARY: users are required to manually fetch the access_token via the Microsoft PowerBI focus mode until the Oauth2 is setup accordingly for this component
    - The temporary token will stay active for one hour
    - How to:
        1. Follow this [Link](https://docs.microsoft.com/en-us/rest/api/power-bi/pushdatasets/datasets_postrowsingroup#code-try-0)
        2. Click on "Try it"
        3. Login
        4. Fetch the token via the "Request Preview". 
            - ```Authorization: Bearer *TOKEN*```
        5. Copy ```*TOKEN*``` and paste into the Access Token Configuration

2. Workspace
    - The workspace where the user wants to output their dataset.
    - Please leave this blank if the user is exporting the dataset into the signed in account's "My Workspace"

3. Dataset - Required
    - Name or ID of the dataset the user wish to name this configuration
    - If same dataset name exist in the Workspace, the writer will ask user to specify the dataset ID instead and terminte the current run
    - If specified dataset ID is not found, the writer will fail with an error message

4. Incremental load
    - *In Development*

5. Table Relationships
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
