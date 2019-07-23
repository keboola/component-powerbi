Each extractor configuration can only exported `one` dataset to PowerBI. Writer will be using the data_type defined in metadata in Keboola Storage. If data_type is not configured for the input table, writer will automatically assign that column as `string`.

## Parameters

1. Workspace
    - The workspace where the user wants to output their dataset.
    - Please leave this blank if the user is exporting the dataset into the signed in account's "My Workspace"

2. Dataset - Required
    - Name or ID of the dataset the user wish to name this configuration
    - If same dataset name exist in the Workspace, the writer will ask user to specify the dataset ID instead and terminte the current run
    - If specified dataset ID is not found, the writer will fail with an error message

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


        
