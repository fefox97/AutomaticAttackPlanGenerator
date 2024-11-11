import re
import pandas as pd
from html2text import html2text as h2t
import bleach

class Converter:

    def tuple_list_to_dict(self, tuple_list: list):
        if tuple_list is None:
            return None
        else:
            return {k: v for k, v in tuple_list}

    def string_to_list(self, string: str, sepator=r'[ ,]+'):
        if string is None:
            return None
        else:
            return re.split(sepator, string)

    def string_to_int_list(self, string: str, sepator=r'[ ,]+'):
        string = f"{string}"
        if string in [None, '', 'None']:
            return None
        else:
            return [int(x) for x in re.split(sepator, string)]
        
    def sub_string(self, string):
        if string is None:
            return None
        elif type(string) is list:
            for i, s in enumerate(string):
                string[i] = self.sub_string(s)
            return string
        else:
            subs = {'*': '', '#': ''}
            string = h2t(str(string))   # convert html in certain columns to text
            string = string.translate(str.maketrans(subs))
            string = re.sub(r'(\S)\n(\S)', r'\1 \2', string)
            string = string.replace('\n', '')
            return string

    def list_to_string(self, list: list, sepator=', '):
        if list is None:
            return None
        else:
            return sepator.join(list)
    
    def dict_to_string(self, dict: dict):
        if dict is None:
            return None
        else:
            if type(list(dict.values())[0]) is list:
                return '\n\n'.join([f"{k}: {', '.join(v)}" for k, v in dict.items()])
            return '\n\n'.join([f"{k}: {v}" for k, v in dict.items()])
    
    def string_to_dict(self, string: str):
        if string is None:
            return None
        else:
            string = string.replace('{', '').replace('}', '')
            out_dict = {k.strip(): v.strip() for k, v in [x.split(':') for x in string.split(',')]}
            out_dict = {k.removeprefix("'").removeprefix('"').removesuffix('"').removesuffix("'"): v.removeprefix("'").removeprefix('"').removesuffix('"').removesuffix("'") for k, v in out_dict.items()}
            return out_dict

    def convert_column_to_text(self, df: pd.DataFrame):
        # for column in ['Can Follow Refs', 'Domains', 'Object Marking Refs', 'Prerequisites', 'Alternate Terms', 'Can Precede Refs', 'Resources Required', 'Example Instances']:
        for column in ['Can_Follow_Refs', 'Domains', 'Object_Marking_Refs', 'Prerequisites', 'Alternate_Terms', 'Can_Precede_Refs', 'Resources_Required', 'Example_Instances']:
            df[column] = df[column].apply(lambda x: self.list_to_string(x))

        # for column in ['Description', 'Extended Description', 'Example Instances', 'Resources Required']:
        for column in ['Description', 'Extended_Description', 'Example_Instances', 'Resources_Required']:
            df[column] = df[column].apply(lambda x: self.sub_string(x))

        for column in ['Consequences', 'Skills_Required']:
            df[column] = df[column].apply(lambda x: self.dict_to_string(x))

        return df

    def convert_ids_to_capec_ids(self, df: pd.DataFrame):
        df['capec_id'] = df['external_references'].apply(lambda x: int(x[0]['external_id'].split('-')[1]) if x[0]['source_name'] == 'capec' else None)
        df['capec_children_id'] = df['x_capec_parent_of_refs'].apply(lambda ids: [int(df.loc[id]['capec_id']) for id in ids] if ids is not None or [] else None)
        df['capec_parents_id'] = df['x_capec_child_of_refs'].apply(lambda ids: [int(df.loc[id]['capec_id']) for id in ids] if ids is not None or [] else None)
        df['x_capec_peer_of_refs'] = df['x_capec_peer_of_refs'].apply(lambda ids: [int(df.loc[id]['capec_id']) for id in ids] if ids is not None or [] else None)
        return df
    
    def convert_column_names(self, df: pd.DataFrame):
        # position the index column to the first column
        new_columns = []
        for column in df.columns:
            column = column.replace('x_capec_', '')
            column = column.title()
            column = column.replace('Id', 'ID')
            new_columns.append(column)
        df.columns = new_columns
        return df
    
    def escape_script(self, html: str):
        html = bleach.clean(html, tags=['table', 'tr', 'td', 'th', 'tbody', 'thead', 'tfoot', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'b', 'i', 'u', 'br', 'a'], attributes=['style', 'class', 'id', 'href'], strip=True)
        return html