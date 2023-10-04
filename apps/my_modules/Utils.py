from stix2 import FileSystemStore, FileSystemSource
import os
import pandas as pd
import numpy as np
from neo4j import Result
import re
from apps.my_modules.converter import Converter
from neo4j import GraphDatabase
import sqlalchemy
from sqlalchemy import MetaData
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from apps.databases.models import ThreatCatalog, Capec

class AttackPatternUtils:
    
    converter = Converter()
    
    def __init__(self):
        self.base_path = "/Users/fefox/Desktop/Web3/apps/static/assets/dbs"
        self.stix_path = f"{self.base_path}/capec_stix"
        self.attack_pattern_path = f'{self.stix_path}/attack-pattern'
        self.fs = FileSystemStore(stix_dir=self.stix_path, bundlify=False)
        self.fs_source = FileSystemSource(stix_dir=self.stix_path)
        
        self.attack_pattern_df = self.load_attack_patterns()

    def load_attack_patterns(self):
        print("\nLoading attack patterns...\n")
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
        # attack_pattern_df.set_index('capec_id', inplace=True)

        # drop columns
        attack_pattern_df.drop(['x_capec_parent_of_refs', 'x_capec_child_of_refs', 'type', 'revoked'], axis=1, inplace=True)

        # remove html header from x_capec_execution_flow
        attack_pattern_df['x_capec_execution_flow'] = attack_pattern_df['x_capec_execution_flow'].apply(lambda x: re.sub(r'<h2>(.*?)</h2>', r'', x) if x is not None else None)
        
        # prettier column names
        attack_pattern_df = self.converter.convert_column_names(attack_pattern_df)
        return attack_pattern_df
    

class ThreatCatalogUtils:
    
    converter = Converter()

    def __init__(self):
        self.base_path = "/Users/fefox/Desktop/Web3/apps/static/assets/dbs"
        self.file_path = f"{self.base_path}/ThreatCatalogComplete.xlsx"
        self.threat_catalog_df = self.load_threat_catalog()

    def load_threat_catalog(self):
        print("\nLoading threat catalog...\n")
        df = pd.read_excel(self.file_path, sheet_name="Threat Components", header=0)
        df.replace(np.nan, None, inplace=True) # replace NaN with None
        # df.set_index('TID', inplace=True)
        df = df.astype('str')
        columns_to_convert = ['CapecMeta', 'CapecStandard', 'CapecDetailed']
        for column in columns_to_convert:
            df[column] = df[column].apply(lambda x: self.converter.string_to_list(x))
        return df

class MacmUtils:

    def __init__(self):
        # neo4j setup
        #URI_NEO4J = "neo4j://192.168.1.6:7687"
        self.URI_NEO4J = "neo4j://192.168.40.4:7787"
        self.USER_NEO4J = "neo4j"
        self.PASS_NEO4J = "neo4j#1234"
        self.base_path = "/Users/fefox/Desktop/Web3/apps/static/assets/dbs"
        
        self.driver = GraphDatabase.driver(self.URI_NEO4J, auth=(self.USER_NEO4J, self.PASS_NEO4J))
        self.driver.verify_connectivity()

    def clear_database(self, database):
        self.driver.execute_query("MATCH (n) DETACH DELETE n", database_=database)

    def read_macm(self, database='macm'):
        macm_df: pd.DataFrame = self.driver.execute_query("MATCH (asset) RETURN asset.component_id, asset.application, asset.name, asset.type, asset.app_id", database_=database, result_transformer_=Result.to_df)
        macm_df.rename(columns={'asset.component_id': 'Component_ID', 'asset.application': 'Application', 'asset.name': 'Name', 'asset.type': 'Type', 'asset.app_id': 'App_ID'}, inplace=True)
        # macm_df['Component_ID'] = macm_df['Component_ID'].astype('int')
        macm_df.set_index('Component_ID', inplace=True)
        return macm_df

    def upload_macm_to_database(self):
        print("\nLoading macm to database...\n")
        engine = sqlalchemy.create_engine('sqlite:///apps/db.sqlite3')
        df = self.read_macm()
        df.to_sql('Macm', engine, if_exists='replace', index=True, index_label="Component_ID", dtype={"Component_ID": sqlalchemy.types.INTEGER, "App_ID": sqlalchemy.types.INTEGER})

    def upload_macm(self, query, database='macm'):
        self.clear_database(database)
        self.driver.execute_query(query, database_=database)
        self.upload_macm_to_database()


class Utils:

    def __init__(self):
        self.attack_pattern_utils = AttackPatternUtils()
        self.threat_catalog_utils = ThreatCatalogUtils()
        self.attack_pattern_df = self.attack_pattern_utils.attack_pattern_df
        self.threat_catalog_df = self.threat_catalog_utils.threat_catalog_df
        self.engine = sqlalchemy.create_engine('sqlite:///apps/db.sqlite3')

    def save_dataframe_to_database(self, df: pd.DataFrame, mapper, replace=True):
        print(f"\nLoading dataframe {mapper.__name__} to database...\n")
        Session = sessionmaker(bind=self.engine)
        session = Session()
        if replace:
            session.query(mapper).delete()
        session.bulk_insert_mappings(mapper, df.to_dict(orient="records", index=True), render_nulls=True)
        session.commit()
        session.close()

    def upload_databases(self, database):
        if database == 'Capec':
            self.save_dataframe_to_database(self.attack_pattern_df, Capec)
        elif database == 'ThreatCatalog':
            self.save_dataframe_to_database(self.threat_catalog_df, ThreatCatalog)