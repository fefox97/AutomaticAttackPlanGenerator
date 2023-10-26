from stix2 import FileSystemStore, FileSystemSource
import os
import pandas as pd
import numpy as np
from neo4j import Result
import re
from apps.my_modules.converter import Converter
from neo4j import GraphDatabase
import sqlalchemy
from sqlalchemy import inspect, select, func, and_
from sqlalchemy.orm import sessionmaker
from apps.databases.models import ThreatCatalogue, Capec, CapecThreatRel, ToolCatalogue, CapecToolRel, Macm, AttackView, ToolAssetTypeRel
from apps.config import Config
from sqlalchemy_schemadisplay import create_schema_graph
from apps import db

class AttackPatternUtils:
    
    converter = Converter()
    
    def __init__(self):
        self.base_path = Config.DBS_PATH
        self.stix_path = f"{self.base_path}/capec_stix"
        self.attack_pattern_path = f'{self.stix_path}/attack-pattern'
        self.fs = FileSystemStore(stix_dir=self.stix_path, bundlify=False)
        self.fs_source = FileSystemSource(stix_dir=self.stix_path)
        # self.attack_pattern_df = self.load_attack_patterns()

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

        for column in ['description', 'x_capec_extended_description', 'x_capec_example_instances', 'x_capec_resources_required']:
            attack_pattern_df[column] = attack_pattern_df[column].apply(lambda x: self.converter.sub_string(x))
        
        # prettier column names
        attack_pattern_df = self.converter.convert_column_names(attack_pattern_df)
        return attack_pattern_df
    

class ThreatCatalogUtils:
    
    converter = Converter()

    def __init__(self):
        self.base_path = Config.DBS_PATH
        self.file_path = f"{self.base_path}/{Config.THREAT_CATALOG_FILE_NAME}"
        # self.threat_catalog_df = self.load_threat_catalog()

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

class ToolCatalogUtils:

    converter = Converter()

    def __init__(self):
        self.base_path = Config.DBS_PATH
        self.file_path = f"{self.base_path}/{Config.THREAT_CATALOG_FILE_NAME}"
        # self.tools_catalog_df = self.load_tools_catalog()

    def load_tools_catalog(self):
        print("\nLoading tools catalog...\n")
        df = pd.read_excel(self.file_path, sheet_name="Tools", header=0)
        df.replace(np.nan, None, inplace=True) # replace NaN with None
        df['CapecID'] = df['CapecID'].apply(lambda x: self.converter.string_to_list(x))
        return df

class MacmUtils:

    converter = Converter()

    def __init__(self):
        # neo4j setup
        # self.URI_NEO4J = Config.URI_NEO4J
        # self.USER_NEO4J = Config.USER_NEO4J
        # self.PASS_NEO4J = Config.PASS_NEO4J

        self.URI_NEO4J  = os.getenv('URI_NEO4J'     , None)
        self.USER_NEO4J = os.getenv('USER_NEO4J'    , None)
        self.PASS_NEO4J = os.getenv('PASS_NEO4J'    , None)

        self.driver = GraphDatabase.driver(self.URI_NEO4J, auth=(self.USER_NEO4J, self.PASS_NEO4J))
        self.driver.verify_connectivity()

    def clear_database(self, database):
        self.driver.execute_query("MATCH (n) DETACH DELETE n", database_=database)

    def read_macm(self, database='macm'):
        macm_df: pd.DataFrame = self.driver.execute_query("MATCH (asset) RETURN asset.component_id, asset.application, asset.name, asset.type, asset.app_id, asset.parameters", database_=database, result_transformer_=Result.to_df)
        macm_df.rename(columns={'asset.component_id': 'Component_ID', 'asset.application': 'Application', 'asset.name': 'Name', 'asset.type': 'Type', 'asset.app_id': 'App_ID', 'asset.parameters': 'Parameters'}, inplace=True)
        macm_df['Parameters'] = macm_df['Parameters'].apply(lambda x: self.converter.string_to_dict(x))
        return macm_df

    def upload_macm(self, query, database='macm'):
        self.clear_database(database)
        self.driver.execute_query(query, database_=database)

    def tool_asset_type_rel(self, database='macm'):
        queries = ToolCatalogue.query.with_entities(ToolCatalogue.ToolID, ToolCatalogue.CypherQuery).all()
        tool_asset_type_df = pd.DataFrame(columns=['ToolID', 'ComponentID'])
        for query in queries:
            if query.CypherQuery is not None:
                component_id = [element['component_id'] for element in self.driver.execute_query(query.CypherQuery, database_='macm').records]
                tool_asset_type_df = pd.concat([tool_asset_type_df, pd.DataFrame({'ToolID': query.ToolID, 'ComponentID': component_id})], ignore_index=True)
        tool_asset_type_df.drop_duplicates(inplace=True)
        return tool_asset_type_df

class Utils:

    def __init__(self):
        self.attack_pattern_utils = AttackPatternUtils()
        self.threat_catalog_utils = ThreatCatalogUtils()
        self.tool_catalog_utils = ToolCatalogUtils()
        self.macm_utils = MacmUtils()
        self.engine = sqlalchemy.create_engine(Config.SQLALCHEMY_DATABASE_URI)

    def save_dataframe_to_database(self, df: pd.DataFrame, mapper, replace=True):
        print(f"\nLoading dataframe {mapper.__name__} to database...\n")
        Session = sessionmaker(bind=self.engine)
        session = Session()
        if inspect(self.engine).has_table(mapper.__tablename__):
            if replace:
                mapper.__table__.drop(self.engine)
                session.commit()
        mapper.metadata.create_all(self.engine)
        session.bulk_insert_mappings(mapper, df.to_dict(orient="records", index=True), render_nulls=True)
        session.commit()
        session.close()

    def load_capec_threat_relations(self, df: pd.DataFrame):
        print("\nExtracting Capec-ThreatCatalog relations to database...\n")
        relations_df = pd.DataFrame(columns=['Capec_ID', 'TID'])
        for _, threat in df.iterrows():
            for capec in threat['CapecMeta'] + threat['CapecStandard'] + threat['CapecDetailed']:
                if capec is not None and capec != 'None':
                    relations_df.loc[len(relations_df)] = {'Capec_ID': int(capec), 'TID': threat['TID']}
        relations_df.drop_duplicates(inplace=True)
        relations_df.index.name = 'Id'
        return relations_df

    def load_capec_tool_relations(self, df: pd.DataFrame):
        print("\nExtracting Capec-ToolCatalog relations to database...\n")
        relations_df = pd.DataFrame(columns=['Capec_ID', 'ToolID'])
        for _, tool in df.iterrows():
            if tool['CapecID'] is not None:
                for capec in tool['CapecID']:
                    if capec is not None and capec != 'None':
                        relations_df.loc[len(relations_df)] = {'Capec_ID': int(capec), 'ToolID': tool['ToolID']}
        relations_df.drop_duplicates(inplace=True)
        relations_df.index.name = 'Id'
        return relations_df

    def upload_databases(self, database):
        if database == 'Capec':
            attack_pattern_df = self.attack_pattern_utils.load_attack_patterns()
            self.save_dataframe_to_database(attack_pattern_df, Capec)
        elif database == 'ThreatCatalog':
            threat_catalog_df = self.threat_catalog_utils.load_threat_catalog()
            relations = self.load_capec_threat_relations(threat_catalog_df)
            self.save_dataframe_to_database(threat_catalog_df, ThreatCatalogue)
            self.save_dataframe_to_database(relations, CapecThreatRel)
        elif database == 'ToolCatalog':
            tool_catalog_df = self.tool_catalog_utils.load_tools_catalog()
            relations = self.load_capec_tool_relations(tool_catalog_df)
            self.save_dataframe_to_database(tool_catalog_df, ToolCatalogue)
            self.save_dataframe_to_database(relations, CapecToolRel)
        elif database == 'Macm':
            macm_df = self.macm_utils.read_macm()
            tool_asset_type_df = self.macm_utils.tool_asset_type_rel()
            self.save_dataframe_to_database(macm_df, Macm)
            self.save_dataframe_to_database(tool_asset_type_df, ToolAssetTypeRel)
            AttackView.metadata.create_all(self.engine)

    # def test_function(self):
    #     response = {}
    #     # engine = sqlalchemy.create_engine('sqlite:///apps/db.sqlite3')
    #     # Session = sessionmaker(bind=engine)
    #     # session = Session()
    #     search_keys = ['SQL', 'SQL Injection']
    #     search_cols = [Capec.Name, Capec.Description]
    #     search_args = [or_(and_(col.ilike(f"%{key}%") for key in search_keys) for col in search_cols)]
    #     query = Capec.query.filter(*search_args).with_entities(Capec.Name, Capec.Description)
    #     compiled = query.statement.compile(compile_kwargs={"literal_binds": True})
    #     response['query'] = str(compiled)
    #     output = query.all()
    #     response['output'] = str(output)
    #     # session.close()
    #     return response
    
    # def test_function(self):
        
    #     er_diagram_filename = 'er_diagram.png'
    #     er_diagram_path = f'{Config.DBS_PATH}/images/{er_diagram_filename}'
    #     graph = create_schema_graph(metadata=db.metadata, show_datatypes=True, show_indexes=True, rankdir='LR', font='Helvetica', concentrate=False)
    #     graph.write_png(er_diagram_path)
    #     response = {'message': 'ER diagram generated successfully'}
    #     return response

    def test_function(self):
        row_number_column = func.row_number().over(order_by=Macm.Component_ID).label('Attack_Number')
        query = select(
                    ToolCatalogue.ToolID.label("Tool_ID"), 
                    ToolCatalogue.Name.label("Tool_Name"), 
                    ToolCatalogue.Command, ToolCatalogue.Description, 
                    Capec.Capec_ID, Capec.Name.label("Attack_Pattern"), 
                    Capec.Execution_Flow, 
                    Capec.Description.label("Capec_Description"), 
                    ThreatCatalogue.TID.label("Threat_ID"), 
                    ThreatCatalogue.Asset.label("Asset_Type"), 
                    ThreatCatalogue.Threat, 
                    ThreatCatalogue.Description.label("Threat_Description"), 
                    Macm.Component_ID, 
                    Macm.Name.label("Asset"), 
                    Macm.Parameters
                ).select_from(Macm).join(ThreatCatalogue, Macm.Type==ThreatCatalogue.Asset).join(CapecThreatRel).join(Capec).join(CapecToolRel).join(ToolCatalogue).join(ToolAssetTypeRel, and_(Macm.Component_ID==ToolAssetTypeRel.ComponentID, ToolAssetTypeRel.ToolID==ToolCatalogue.ToolID)).add_columns(row_number_column)
        compiled = query.compile(compile_kwargs={"literal_binds": True})
        response = {'query': str(compiled)}
        
        return response