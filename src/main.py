import json, os, time
import gradio as gr
from interactive import text2sql
from utils import convert_table_info
from knowledge_base import Knowledge_Base

def reset_user_input():
    return gr.update(value='')

TABLE_INFO_PATH = "./data/tables.json"
output_path = "./generate_datasets"
isExist = os.path.exists(output_path)
if not isExist:
   os.makedirs(output_path)

KB_INPUT_FILE = "./data/QA_SQL.json"
KB_OUTPUT_FILE = "./generate_datasets/QA_SQL.json"
# load knowledge base, which is a list of question-sql pairs.
kb = Knowledge_Base()
kb.load_data(KB_INPUT_FILE) 

with gr.Blocks() as demo:
    # Function to read JSON file and extract data by db_id
    def load_data_by_db_id(file_path):
        list = []
        with open(file_path, 'r') as json_file:
            data_list = json.load(json_file)
        for item in data_list:
            list.append(item["db_id"])
        return (list, convert_table_info(data_list))

    # Load data from the JSON file
    (db_list, dbs_dict) = load_data_by_db_id(TABLE_INFO_PATH)

    gr.HTML("""<h1 align="center">Text2SQL Demo</h1>""")
    with gr.Row():
        with gr.Column(scale=1.5):
            user_input = gr.Textbox(show_label=False, placeholder="Question...", lines=10).style(
                container=False)

            # Dropdown component to select a db_id
            db_id_dropdown = gr.Dropdown(db_list, label="Select a database")

            # Submit button
            submitBtn = gr.Button("Submit", variant="primary")

        with gr.Column(scale=1):
            # Non-interactive textbox to display the "Data Dictionary" content
            data_dict_textbox = gr.Textbox(show_label=True, label="Database Info", placeholder="Select a database first...", lines=15).style(
                container=False)

    # progress 
    #progress_textbox = gr.Textbox(show_label=False, placeholder="Progress will be shown here...", lines=10).style(
    #    container=False)

    #def update_progress(progress_message):
    #    content = progress_textbox.value
    #    # Update the progress information displayed in the UI
    #    progress_textbox.update(value = content + "\n" + progress_message)

    def update_data_dictionary(selected_db_id):
        # Update the content of the "Data Dictionary" based on the selected database
        data_dictionary = dbs_dict[selected_db_id]
        updated_content = json.dumps(data_dictionary, indent=4)
        return data_dict_textbox.update(value=updated_content)

    def on_submit_click(user_input, db_id_dropdown):
        # search knowledge base to find questions with 95% similarity 
        start_time = time.time()
        sql_stmt = kb.search_data(user_input, db_id_dropdown, 0.90)
        if sql_stmt is None:
            

            # Use the selected_db_id in your prediction logic
            sql_list = text2sql(user_input, db_id_dropdown, TABLE_INFO_PATH)

            # Construct the SQL statement as a single string
            sql_stmt = ';'.join(sql_list)
            kb.insert_data(user_input, db_id_dropdown, sql_stmt)
            kb.dump_data(KB_OUTPUT_FILE)
        process_time = "processing time: %s seconds" % (time.time() - start_time)
        return process_time + "\n\n" + sql_stmt

    # Textbox to display the response of the input
    response_textbox = gr.Textbox(show_label=False, placeholder="SQL...", lines=5).style(
        container=False)

    submitBtn.click(on_submit_click, inputs=[user_input, db_id_dropdown], outputs=[response_textbox])

    db_id_dropdown.change(fn=update_data_dictionary, inputs=db_id_dropdown, outputs=data_dict_textbox)

demo.queue().launch(share=False, inbrowser=True)
