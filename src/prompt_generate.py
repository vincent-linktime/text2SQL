import json
import argparse

def parse_option():
    parser = argparse.ArgumentParser("command line arguments for generate prompt")
    parser.add_argument("--input_dataset_path", type=str)
    parser.add_argument("--output_dataset_path", type=str)

    opt = parser.parse_args()

    return opt

def generate_prompt(input_dataset_path, output_dataset_path):
    with open(input_dataset_path) as f:
        data_all = json.load(f)
    temp = []
    for id, data in enumerate(data_all):
        data['input_sequence'] = "### Complete sqlite SQL query only and with no explanation, and do not select extra columns that are not explicitly requested in the query. " \
                        "\n ### Sqlite SQL tables, with their properties: \n#\n"
        schema = ""
        for tab, cols in data['schema'].items():
            schema += '# ' + tab + ' ( '
            for i, col in enumerate(cols):
                schema += col
                schema += ', '
            schema = schema[:-2] + ' )\n'
        data['input_sequence'] += schema[:-1]
        for fk in data['fk']:
            data['input_sequence'] += '\n# ' + fk
        data['input_sequence'] += '\n#\n### ' + data['question'] + '\nSELECT'
    with open(output_dataset_path, 'w') as f:
        json.dump(data_all, f, indent=2)


if __name__ == "__main__":
    opt = parse_option()
    generate_prompt(opt.input_dataset_path, opt.output_dataset_path)
