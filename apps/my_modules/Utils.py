from stix2 import FileSystemStore, FileSystemSource
import os
import pandas as pd
import numpy as np
from neo4j import Result
from functools import reduce
import re
from apps.my_modules.Converter import Converter
from neo4j import GraphDatabase

class AttackPattern:
    
    converter = Converter()
    
    def __init__(self):
        self.base_path = "/Users/fefox/Desktop/Web2/apps/static/assets/dbs"
        self.stix_path = f"{self.base_path}/capec_stix"
        self.attack_pattern_path = f'{self.stix_path}/attack-pattern'
        self.fs = FileSystemStore(stix_dir=self.stix_path, bundlify=False)
        self.fs_source = FileSystemSource(stix_dir=self.stix_path)
        
        self.attack_pattern_df = self.read_attack_patterns()
        # self.attack_pattern_df_str = self.converter.convert_column_to_text(self.attack_pattern_df)

    def save_attack_patterns(self, df: pd.DataFrame):
        df.to_pickle(f'{self.base_path}/attack_patterns.pickle')

    def read_attack_patterns(self):
        if os.path.exists(f'{self.base_path}/attack_patterns.pickle'):
            df = pd.read_pickle(f'{self.base_path}/attack_patterns.pickle')
        else:
            df = self.load_attack_patterns()
            self.save_attack_patterns(df)
        return df

    def load_attack_patterns(self):
        print("\n\n\nLoading attack patterns...\n\n\n")
        attack_pattern_list = []
        for attack_pattern in [x.removesuffix(".json") for x in os.listdir(self.attack_pattern_path)]:
            ap = self.fs.get(attack_pattern)
            attack_pattern_list.append(ap)
        attack_pattern_df = pd.DataFrame(attack_pattern_list)
        
        # replace NaN with None
        attack_pattern_df.replace(np.nan, None, inplace=True)
        
        # replace stix ids with capec ids
        attack_pattern_df.set_index('id', inplace=True)
        attack_pattern_df = self.converter.convert_ids_to_capec_ids(attack_pattern_df)
        attack_pattern_df.set_index('capec_id', inplace=True)

        # drop columns
        attack_pattern_df.drop(['x_capec_parent_of_refs', 'x_capec_child_of_refs', 'type', 'revoked'], axis=1, inplace=True)

        # remove html header from x_capec_execution_flow
        attack_pattern_df['x_capec_execution_flow'] = attack_pattern_df['x_capec_execution_flow'].apply(lambda x: re.sub(r'<h2>(.*?)</h2>', r'', x) if x is not None else None)

        # sort by capec_id and make it categorical
        attack_pattern_df.index = pd.CategoricalIndex(attack_pattern_df.index, sorted(attack_pattern_df.index.to_list(), key=lambda x: int(x)))
        
        # prettier column names
        attack_pattern_df = self.converter.convert_column_names(attack_pattern_df)
        return attack_pattern_df

    def get_child_attack_patterns_by_id(self, parent_id, attack_pattern_df: pd.DataFrame):
        try:
            return attack_pattern_df.loc[parent_id].get('Capec Childs ID') or []
        except:
            return None

    def get_child_attack_patterns_recursive(self, parent_id, attack_pattern_df: pd.DataFrame) -> list:
        childs = self.get_child_attack_patterns_by_id(parent_id, attack_pattern_df)
        if childs is None:
            return []
        else:
            for child in childs:
                childs += self.get_child_attack_patterns_recursive(child, attack_pattern_df)
            return childs

    def get_child_attack_patterns(self, parent_ids, attack_pattern_df: pd.DataFrame, show_tree=False):
        if type(parent_ids) is not list: parent_ids = [parent_ids]
        childs = [parent_id for parent_id in parent_ids]
        if show_tree:
            childs += [child for parent_id in parent_ids for child in self.get_child_attack_patterns_recursive(parent_id, attack_pattern_df)]
        childs = list(set(childs))
        return childs # return only the ids, not the dataframe

    def query_attack_patterns(self, attack_pattern_df: pd.DataFrame, keywords, search_columns:list=['description'], ap_type:list=['Meta', 'Standard', 'Detailed'], query_type='or'):
        if query_type == 'or':
            keywords = '|'.join(keywords)
        elif query_type == 'and':
            keywords = r'(?=.*' + r')(?=.*'.join(keywords) + r')'
        else:
            raise Exception('query_type must be "or" or "and"')
        inds = [attack_pattern_df[x].str.lower().str.contains(keywords.lower()) for x in search_columns]
        type_inds = [attack_pattern_df['x_capec_abstraction'].isin([x]) for x in ap_type]
        response = attack_pattern_df[(reduce(lambda x, y: x | y, inds)) & (reduce(lambda x, y: x | y, type_inds))].sort_values(by=['x_capec_abstraction'])
        return response

class ThreatCatalog:
    
    converter = Converter()

    def __init__(self):
        self.base_path = "/Users/fefox/Desktop/Web2/apps/static/assets/dbs"
        self.threat_catalog_df = self.load_threat_catalog(f"{self.base_path}/ThreatCatalogComplete.xlsx")

    def load_threat_catalog(self, filename):
        print("\n\n\nLoading threat catalog...\n\n\n")
        df = pd.read_excel(filename, sheet_name="Threat Components", header=0)
        df.replace(np.nan, None, inplace=True) # replace NaN with None
        df.set_index('TID', inplace=True)
        df = df.astype('str')
        columns_to_convert = ['CapecMeta', 'CapecStandard', 'CapecDetailed']
        for column in columns_to_convert:
            df[column] = df[column].apply(lambda x: self.converter.string_to_list(x))
        df['Asset'] = df['Asset'].apply(lambda x: x.replace('.', '_'))
        return df

class Macm:

    def __init__(self):
        # neo4j setup
        #URI_NEO4J = "neo4j://192.168.1.6:7687"
        self.URI_NEO4J = "neo4j://192.168.40.4:7787"
        self.USER_NEO4J = "neo4j"
        self.PASS_NEO4J = "neo4j#1234"
        self.base_path = "/Users/fefox/Desktop/Web2/apps/static/assets/dbs"
        
        self.driver = GraphDatabase.driver(self.URI_NEO4J, auth=(self.USER_NEO4J, self.PASS_NEO4J))
        self.driver.verify_connectivity()

    def clear_database(self, database):
        self.driver.execute_query("MATCH (n) DETACH DELETE n", database_=database)

    def read_macm(self, database='macm'):
        macm_df = self.driver.execute_query("MATCH (asset) RETURN asset.component_id, asset.application, asset.name, asset.type, asset.app_id", database_=database, result_transformer_=Result.to_df)
        macm_df.columns = ['Component ID', 'Application', 'Name', 'Type', 'App ID']
        return macm_df

    def upload_macm(self, query, database='macm'):
        self.clear_database(database)
        self.driver.execute_query(query, database_=database)

class Utils:

    def __init__(self):
        self.allowed_extensions = None

    def init_app(self, app):
        self.allowed_extensions = app.config['ALLOWED_EXTENSIONS']

    def allowed_file(self, filename, allowed_extensions=None):
        if allowed_extensions is None:
            allowed_extensions = self.allowed_extensions
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions