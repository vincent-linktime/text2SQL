import json, openai, os, time

openai.api_key = os.environ["OPENAI_KEY"]

def openai_completion(input, sc_num):
    retries = 3
    retry_cnt = 0
    backoff_time = 3
    while retry_cnt <= retries:
        try:
        #Make your OpenAI API request here
            completions = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=input,
                # top_p=0.5
                temperature=0.7,
                n=sc_num
                # stop=["Q:"]
            )
            return completions
        except openai.error.Timeout as e:
            #Handle timeout error, e.g. retry or log
            print(f"OpenAI API request timed out: {e}")        
        except openai.error.APIError as e:
            #Handle API error, e.g. retry or log
            print(f"OpenAI API returned an API Error: {e}")
        except openai.error.APIConnectionError as e:
            #Handle connection error, e.g. check network or log
            print(f"OpenAI API request failed to connect: {e}")
        except openai.error.InvalidRequestError as e:
            #Handle invalid request error, e.g. validate parameters or log
            print(f"OpenAI API request was invalid: {e}")
        except openai.error.AuthenticationError as e:
            #Handle authentication error, e.g. check credentials or log
            print(f"OpenAI API request was not authorized: {e}")
        except openai.error.PermissionError as e:
            #Handle permission error, e.g. check scope or log
            print(f"OpenAI API request was not permitted: {e}")
        except openai.error.RateLimitError as e:
            #Handle rate limit error, e.g. wait or log
            print(f"OpenAI API request exceeded rate limit: {e}")
        
        print(f"Retrying in {backoff_time} seconds...")
        time.sleep(backoff_time)
        backoff_time *= 1.5

    return None


def convert_table_info(original_json):
    # Initialize an empty list to store the reformatted data
    reformatted_data = []

    # Iterate through the original JSON data and reformat it
    for item in original_json:
        table_info = {
            "db_id": item["db_id"],
            "tables": []
        }

        # Create a mapping from table index to table name
        table_index_to_name = {i: name for i, name in enumerate(item["table_names_original"])}

        # Initialize a dictionary to store columns for each table
        table_columns = {}

        table_columns_info = {}
        # Iterate through the columns and format them
        for i, column_info in enumerate(item["column_names_original"]):
            table_index, column_name_original = column_info
            column_type = item["column_types"][i]
            table_name_original = table_index_to_name.get(table_index)

            if not table_name_original or column_name_original == '*':
                continue  # Skip dummy columns and columns without a corresponding table

            # Create or append to the list of columns for the current table
            if table_name_original not in table_columns:
                table_columns[table_name_original] = []

            table_columns[table_name_original].append({
                "column_name_original": column_name_original,
                "column_type": column_type
            })
            table_columns_info[i] = table_name_original + "." + column_name_original

        # Convert the table_columns dictionary to the desired format
        for table_name, columns in table_columns.items():
            table_info["tables"].append({
                "table_names_original": table_name,
                "columns": columns
            })

        # Extract primary keys
        primary_keys = [{"pk": table_columns_info[i]}
                        for i in table_columns_info.keys()
                        if i in item["primary_keys"]]
        table_info["primary_keys"] = primary_keys

        # Extract foreign keys
        foreign_keys = []
        for (i, i_ref) in item["foreign_keys"]:
            foreign_keys.append({"fk": table_columns_info[i] + "=" + table_columns_info[i_ref]})
        table_info["foreign_keys"] = foreign_keys

        reformatted_data.append(table_info)
        
    return reformatted_data
