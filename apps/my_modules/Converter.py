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
        if string in [None, '', 'None']:
            return None
        else:
            return [int(x) for x in re.split(sepator, string)]
        
    def sub_string(self, string):
        if string is None:
            return None
        else:
            subs = {'*': '', '#': ''}
            string = h2t(str(string))   # convert html in certain columns to text
            string = string.translate(str.maketrans(subs))
            string = re.sub(r'(\S)\n(\S)', r'\1 \2', string)
            string = string.replace('\n ', '\n')
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
            out_dict = {k.removeprefix("'").removesuffix("'"): v.removeprefix("'").removesuffix("'") for k, v in out_dict.items()}
            return out_dict
        
    def external_references_to_html(self, list: list):
        output = ''
        if list is None:
            return None
        else:
            for reference in list:
                if reference.get('url') is not None:
                    if reference.get('external_id') is not None:
                        output += f"<a class='link' href='{reference['url']}'>{reference['source_name'].capitalize()}: {reference['external_id']}</a><br>"
                    else:
                        output += f"<a class='link' href='{reference['url']}'>{reference['source_name'].capitalize()}: {reference['description']}</a><br>"
            return output

    def convert_column_to_text(self, df: pd.DataFrame):
        # for column in ['Can Follow Refs', 'Domains', 'Object Marking Refs', 'Prerequisites', 'Alternate Terms', 'Can Precede Refs', 'Resources Required', 'Example Instances']:
        for column in ['Can_Follow_Refs', 'Domains', 'Object_Marking_Refs', 'Prerequisites', 'Alternate_Terms', 'Can_Precede_Refs', 'Resources_Required', 'Example_Instances']:
            df[column] = df[column].apply(lambda x: self.list_to_string(x))

        # for column in ['Description', 'Extended Description', 'Example Instances', 'Resources Required']:
        for column in ['Description', 'Extended_Description', 'Example_Instances', 'Resources_Required']:
            df[column] = df[column].apply(lambda x: self.sub_string(x))

        for column in ['Consequences', 'Skills_Required']:
            df[column] = df[column].apply(lambda x: self.dict_to_string(x))

        for column in ['External_References']:
            df[column] = df[column].apply(lambda x: self.external_references_to_html(x))

        return df

    def convert_ids_to_capec_ids(self, df: pd.DataFrame):
        df['capec_id'] = df['external_references'].apply(lambda x: int(x[0]['external_id'].split('-')[1]) if x[0]['source_name'] == 'capec' else None)
        df['capec_childs_id'] = df['x_capec_parent_of_refs'].apply(lambda ids: [int(df.loc[id]['capec_id']) for id in ids] if ids is not None or [] else None)
        df['capec_parents_id'] = df['x_capec_child_of_refs'].apply(lambda ids: [int(df.loc[id]['capec_id']) for id in ids] if ids is not None or [] else None)
        df['x_capec_peer_of_refs'] = df['x_capec_peer_of_refs'].apply(lambda ids: [int(df.loc[id]['capec_id']) for id in ids] if ids is not None or [] else None)
        return df
        
    def dataframe_to_str(self, df: pd.DataFrame):
        df_str = df.copy() # copy the dataframe
        df_str = self.convert_column_to_text(df_str) # convert all columns to text
        df_str = df_str.astype(str).copy() # convert all columns to string
        return df_str
    
    def capec_abstraction_sort(self, df: pd.DataFrame):
        if df is None: return None
        sorter = ['Meta', 'Standard', 'Detailed']
        df['Abstraction'] = pd.Categorical(df['Abstraction'], categories=sorter, ordered=True)
        df = df.sort_values(['Abstraction', 'Capec_ID'], ascending=[True, True])
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
    
    # HTML converters
    
    def replace_index_with_column(self, df: pd.DataFrame):
        df.columns.name = df.index.name
        df.index.name = None
        return df
    
    def add_footer_to_html(self, df:pd.DataFrame, df_html:str):
        idx = df_html.rfind('</table>')
        headers = [x for x in df.columns]
        headers.insert(0, df.columns.name)
        df_html = df_html[:idx] + "<tfoot><tr>" + " ".join(["<th>"+ i +"</th>" for i in headers])+"</tr> </tfoot>" + df_html[idx:]
        return df_html

    def escape_script(self, html: str):
        html = bleach.clean(html, tags=['table', 'tr', 'td', 'th', 'tbody', 'thead', 'tfoot', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'b', 'i', 'u', 'br', 'a'], attributes=['style', 'class', 'id', 'href'], strip=True)
        return html

    def attack_pattern_to_html(self, df: pd.DataFrame, classes=None, table_id=None, escape=True, footer=True):
        df = self.convert_column_to_text(df)
        df = df.replace('\n', '<br>', regex=True)
        df = self.replace_index_with_column(df)
        df_html = df.to_html(classes=classes, table_id=table_id, escape=escape)
        if footer:
            df_html = self.add_footer_to_html(df, df_html)
        df_html = self.escape_script(df_html)
        return df_html
    
    def threat_catalog_to_html(self, df: pd.DataFrame, classes=None, table_id=None, escape=True, footer=True):
        df = df.copy()
        df = df.replace('\n', '<br>', regex=True)
        df = self.replace_index_with_column(df)
        df_html = df.to_html(classes=classes, table_id=table_id, escape=escape)
        if footer:
            df_html = self.add_footer_to_html(df, df_html)
        return df_html
    
    def macm_to_html(self, df: pd.DataFrame, classes=None, table_id=None, escape=True, footer=True):
        df = df.copy()
        df = df.replace('\n', '<br>', regex=True)
        df = self.replace_index_with_column(df)
        df_html = df.to_html(classes=classes, table_id=table_id, escape=escape)
        if footer:
            df_html = self.add_footer_to_html(df, df_html)
        return df_html

