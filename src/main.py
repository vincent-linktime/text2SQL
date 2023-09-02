import json
import gradio as gr
from interactive import text2sql
from utils import convert_table_info

def reset_user_input():
    return gr.update(value='')

TABLE_INFO_PATH = "./data/spider/tables.json"
DB_PATH = "./database"

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
    (db_list, dbs_info) = load_data_by_db_id(TABLE_INFO_PATH)

    gr.HTML("""<h1 align="center">Text2SQL Demo</h1>""")
    progress_output = gr.HTML("")  # Placeholder for displaying progress information

    with gr.Row():
        with gr.Column(scale=4):
            with gr.Column(scale=12):
                user_input = gr.Textbox(show_label=False, placeholder="Question...", lines=10).style(
                    container=False)
            
            # Dropdown component to select a db_id
            db_id_dropdown = gr.Dropdown(db_list, label="Select a database")

            with gr.Column(min_width=32, scale=1):
                submitBtn = gr.Button("Submit", variant="primary")

        with gr.Column(scale=1):
            gr.HTML(
                f"<h3 class='data-dictionary-header'>Data Dictionary</h3>"
                f"<div style='height: 350px; overflow: auto;'>"
                f"<pre>{json.dumps(dbs_info, indent=2)}</pre>"
                f"</div>"
            )

    def update_progress(progress_message):
        # Update the progress information displayed in the UI
        progress_output.set_html(progress_message)

    def predict_with_db_id(user_input, db_id_dropdown):
        selected_db_id = db_id_dropdown.value

        # Use the selected_db_id in your prediction logic
        sql_list = text2sql(user_input, selected_db_id, TABLE_INFO_PATH, DB_PATH, update_progress)

        # Construct the SQL statement as a single string
        sql_stmt = ';'.join(sql_list)

        # Update the response textbox with the SQL statement
        response_textbox.set_content(sql_stmt)

    submitBtn.click(predict_with_db_id, [user_input, db_id_dropdown])

    # Textbox to display the response of the input
    response_textbox = gr.Textbox(show_label=False, placeholder="SQL...", lines=5).style(
        container=False)

demo.queue().launch(share=False, inbrowser=True)
