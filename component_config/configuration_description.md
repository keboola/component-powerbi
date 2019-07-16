Each extractor configuration can only exported `one` dataset to PowerBI.

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
