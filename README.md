**Steps to process data before pushing to DB:** 
>Remember to always check the ER diagram under Changing Room > Database > [ER_diagram](https://gitlab.com/changing-room/database/-/blob/master/ER_diagram.jpeg)

- Create 2 tables for clothing products:
    - **_clothes_** table (from what we scrapped before)     
    - **_item_has_material_** table
- Linked with 3 stable table:
    - **_materials_** table
    - **_shape_** table
    - **_part_component_value_** table
> See detailed code and comment: Changing Room > Scoring Algorithm > [database_fastfashion.ipynb](https://gitlab.com/changing-room/scoring-algorithm/-/blob/master/database_fastfashion.ipynb)
1. **_clothes_ table**
    - **(1) Low-level category**
        - **Step 1**: 
            - If no low-level categories in scrapped df: We extract low-level category from product name through regexes.
            - If there is a low-level category column in df: We map it into standardized name in our list.
            - We get low-level category from regexes: [LowLevelCatagoryRegex](https://docs.google.com/spreadsheets/d/1ZsPxx9SoYrFcHwzJ9MDM8CQWwkMT0n-c0r1fgNPyxZs/edit#gid=0)
            - **Function**: see Changing Room > Scoring Algorithm > [database_fastfashion.ipynb](https://gitlab.com/changing-room/scoring-algorithm/-/blob/master/database_fastfashion.ipynb) -> process_cat(df)
            - First column is the standardized low-level categories that we want to store in the database. The rest cells of each row are the regexes associated with the category in the first cell. 
        - **Step 2**:
            - Take a look at "other" category to see whether there are new categories appearing. 
            - If so, work with the environmental research team to figure out necessary new categories. 
                - **Steps when new low-level categories appear:**
                    - Add new low-level & high-level categories to sheet: [HighLevelCatagory-LowLevelCatagory](https://docs.google.com/spreadsheets/d/1stVKDOak9F7wtlvju-NyHQe9iJDlIdYUNG04tO7Yv4I/edit#gid=0)
                    - Add new low-level categories to sheet: [LowLevelCatagoryRegex](https://docs.google.com/spreadsheets/d/1ZsPxx9SoYrFcHwzJ9MDM8CQWwkMT0n-c0r1fgNPyxZs/edit#gid=0)
                    - Add new low-level & high-level categories to sheet: [Part Component Values*](https://docs.google.com/spreadsheets/d/1pT5pSm74hnRtHHeLPJUSwKS9HXPW7kDcv6qmZE_TyLI/edit#gid=1998384389)
                        - New weights of each part need to be filled in when calculating environmental score (working with environmental research team)
        - **Step 3**:
            - After the category regexes are updated, rematch to the standardize low_level category to store. (Go to Step 1)
    - **(2) clothing_id**
        - **Function**: see Changing Room > Scoring Algorithm > [database_fastfashion.ipynb](https://gitlab.com/changing-room/scoring-algorithm/-/blob/master/database_fastfashion.ipynb) -> get_id(df)


2. **_item_has_material_ table**
    - e.g. see example of how [_item_has_material_](https://docs.google.com/spreadsheets/d/1eRuBCB8TNwe-ug484QYrm-0UJsrykE5abgtEiW0InDo/edit#gid=437472551) table is like
    - (1) First, get _item_has_material_ table from function: Changing Room > Scoring Algorithm > [database_fastfashion.ipynb](https://gitlab.com/changing-room/scoring-algorithm/-/blob/master/database_fastfashion.ipynb) -> get_item_has_material(df)
    - (2) Then, map part into standaidized part name
        - **Step 1**：
            - We get parts from regexes: [PartsRegex](https://docs.google.com/spreadsheets/d/1LnYL6rxlwycu63Ugk1kkcrkoDWeH10xIdV88feLo_KY/edit#gid=0)
            - **Function**: see Changing Room > Scoring Algorithm > [database_fastfashion.ipynb](https://gitlab.com/changing-room/scoring-algorithm/-/blob/master/database_fastfashion.ipynb) -> get_part(df) & get_mapped_part()
            - First column is the standardized part that we want to store in the database. The rest cells of each row are the regexes associated with the part in the first cell. 
        - **Step 2**:
            - Take a look at "other" part to see whether there are new parts appearing. 
            - **Steps when new parts appear:**
                - Add new parts to sheet: [PartsRegex](https://docs.google.com/spreadsheets/d/1LnYL6rxlwycu63Ugk1kkcrkoDWeH10xIdV88feLo_KY/edit#gid=0)
                - Add new parts to sheet: [Part Component Values*](https://docs.google.com/spreadsheets/d/1pT5pSm74hnRtHHeLPJUSwKS9HXPW7kDcv6qmZE_TyLI/edit#gid=1998384389)
                    - New weights of each part need to be filled in when calculating environmental score (working with environmental research team)
        - **Step 3**:
            - After the part regexes are updated, rematch to the standardize part name to store. (Go to Step 1)
            
    - (3) Then, map material into standaidized material id
        - **Step 1**:
            - We get material id from regexes: [MaterialProxy](https://docs.google.com/spreadsheets/d/1AEjSK2dpowBYWC_BEANHyT1lhQSeAxL1nl5PkHgJPBE/edit#gid=0)
            - **Function**: see Changing Room > Scoring Algorithm > [database_fastfashion.ipynb](https://gitlab.com/changing-room/scoring-algorithm/-/blob/master/database_fastfashion.ipynb) -> get_materialid(df) & get_mapped_mid()
            - First column is the material id that we want to store in the database. Second column is the backend-higg name. The rest cells of each row are the regexes associated with the material in first cell.
        - **Step 2**:
            - Take a look at "other" material to see whether there are new materials appearing.
            - Work with the environmental research team to figure out new materials with sheet [MaterialsMatching](https://docs.google.com/spreadsheets/d/1PrqIjYwsVY8ktdw45vnnUn1k75eb45JMTTQ2WUnDKt0/edit#gid=0).
            - If new materials need to be added:
            - **Steps when new materials appear:**
                - We remove materials that cannot be added for now: [MaterialsMatching](https://docs.google.com/spreadsheets/d/1PrqIjYwsVY8ktdw45vnnUn1k75eb45JMTTQ2WUnDKt0/edit#gid=0)
        - **Step 3**:
            - After the materials regexes are updated, rematch to the material id to store. (Go to Step 1)
             
