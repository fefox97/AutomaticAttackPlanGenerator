import json
from stix2 import FileSystemStore, FileSystemSource
import os
import pandas as pd
import numpy as np
from neo4j import Result
import re
import uuid
from apps.api.utils import APIUtils
from apps.my_modules.converter import Converter
from neo4j import GraphDatabase
import sqlalchemy
from sqlalchemy import inspect, select, func, and_
from sqlalchemy.orm import sessionmaker
from apps.databases.models import PentestPhases, ThreatCatalogue, Capec, CapecThreatRel, ToolCatalogue, CapecToolRel, Macm, AttackView, ToolAssetRel, MacmUser, ToolPhaseRel
from flask_login import (
    current_user
)
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
        print("\nLoading threat catalogue...\n")
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
        df['AllowedOutputExtensions'] = df['AllowedOutputExtensions'].apply(lambda x: self.converter.string_to_list(x))
        df['CapecID'] = df['CapecID'].apply(lambda x: self.converter.string_to_list(x))
        df['PhaseID'] = df['PhaseID'].apply(lambda x: self.converter.string_to_int_list(x))
        return df

    def load_pentest_phases(self):
        print("\nLoading pentest phases...\n")
        df = pd.read_excel(self.file_path, sheet_name="Pentest Phases", header=0)
        df.replace(np.nan, None, inplace=True)
        df['PhaseID'] = df['PhaseID'].apply(lambda x: int(x) if x is not None else None)
        df['IsSubPhaseOf'] = df['IsSubPhaseOf'].apply(lambda x: int(x) if x is not None else None)
        print(df)
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

    def create_database(self, database):
        self.driver.execute_query(f"CREATE DATABASE `{database}`")
    
    def delete_database(self, database):
        self.driver.execute_query(f"DROP DATABASE `{database}`")

    def get_greatest_component_id(self, database='macm'):
        query = "MATCH (asset) RETURN max(toInteger(asset.component_id)) as max_id"
        max_id = self.driver.execute_query(query, database_=database, result_transformer_=Result.to_df).iloc[0]['max_id']
        return max_id if max_id is not None else 0
    
    def get_macm_info(self, database='macm'):
        appID = Macm.query.filter_by(App_ID=database).with_entities(Macm.App_ID).distinct().all()
        appID = [app[0] for app in appID]
        appID = appID[0] if appID else None
        applicationName = Macm.query.filter_by(App_ID=database).with_entities(Macm.Application).distinct().all()
        applicationName = [app[0] for app in applicationName]
        applicationName = applicationName[0] if applicationName else None
        maxID = self.get_greatest_component_id(database)
        return appID, applicationName, maxID


    def read_macm(self, database='macm'):
        macm_df: pd.DataFrame = self.driver.execute_query("MATCH (asset) RETURN asset.component_id, asset.application, asset.name, asset.type, asset.app_id, asset.parameters, labels(asset)", database_=database, result_transformer_=Result.to_df)
        macm_df.rename(columns={'asset.component_id': 'Component_ID', 'asset.application': 'Application', 'asset.name': 'Name', 'asset.type': 'Type', 'asset.app_id': 'App_ID', 'asset.parameters': 'Parameters', 'labels(asset)': 'Labels'}, inplace=True)
        macm_df['Parameters'] = macm_df['Parameters'].apply(lambda x: json.loads(x) if x is not None else None)
        return macm_df

    def upload_macm(self, query, database='macm'):
        try:
            self.clear_database(database)
        except:
            print(f"Database {database} does not exist: creating it...")
            self.create_database(database)
        self.driver.execute_query("CREATE CONSTRAINT key IF NOT EXISTS FOR (asset:service) REQUIRE asset.component_id IS UNIQUE", database_=database)
        self.driver.execute_query(query, database_=database)

    def update_macm(self, query, database='macm'):
        try:
            with self.driver.session(database=database) as neo4j_session:
                with neo4j_session.begin_transaction() as transaction:
                    for query in query.split(';'):
                        transaction.run(query)
                    transaction.commit()
                    transaction.close()
            self.delete_macm(database, delete_neo4j=False)
            Utils().upload_databases('Macm', neo4j_db=database)
        except Exception as error:
            print(f"Error updating MACM: {error}")
            raise error

    def delete_macm_component(self, database, component_id):
        try:
            self.driver.execute_query(f"MATCH (asset {{component_id: '{component_id}'}}) DETACH DELETE asset", database_=database)
            self.delete_macm(database, delete_neo4j=False)
            Utils().upload_databases('Macm', neo4j_db=database)
            return True
        except:
            print(f"Error deleting component {component_id} from MACM {database}", exc_info=True)
            return False

    def delete_macm(self, app_id, delete_neo4j=True):
        try:
            Macm.query.filter_by(App_ID=app_id).delete()
            MacmUser.query.filter_by(AppID=app_id).delete()
            ToolAssetRel.query.filter_by(AppID=app_id).delete()
            if delete_neo4j:
                self.delete_database(app_id)
            db.session.commit()
            return True
        except:
            print(f"Error deleting MACM {app_id}")
            return False

    def tool_asset_type_rel(self, database='macm'):
        queries = ToolCatalogue.query.with_entities(ToolCatalogue.ToolID, ToolCatalogue.CypherQuery).all()
        tool_asset_type_df = pd.DataFrame(columns=['ToolID', 'ComponentID'])
        for query in queries:
            if query.CypherQuery is not None:
                component_id = [element['component_id'] for element in self.driver.execute_query(query.CypherQuery, database_=database).records]
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
                session.execute('SET FOREIGN_KEY_CHECKS=0')
                session.commit()
                mapper.__table__.drop(self.engine)
                session.commit()
                session.execute('SET FOREIGN_KEY_CHECKS=1')
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
    
    def laod_tool_phases_relations(self, df: pd.DataFrame):
        print("\nExtracting ToolCatalog-PentestPhases relations to database...\n")
        relations_df = pd.DataFrame(columns=['ToolID', 'PhaseID'])
        for _, tool in df.iterrows():
            if tool['PhaseID'] is not None:
                for phase in tool['PhaseID']:
                    if phase is not None:
                        relations_df.loc[len(relations_df)] = {'ToolID': tool['ToolID'], 'PhaseID': phase}
        relations_df.drop_duplicates(inplace=True)
        relations_df.index.name = 'Id'
        return relations_df

    def upload_databases(self, database, neo4j_db='macm'):
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
            pentest_phases_df = self.tool_catalog_utils.load_pentest_phases()
            capec_tool_relations = self.load_capec_tool_relations(tool_catalog_df)
            tool_phases_relations = self.laod_tool_phases_relations(tool_catalog_df)
            self.save_dataframe_to_database(pentest_phases_df, PentestPhases)
            self.save_dataframe_to_database(tool_catalog_df, ToolCatalogue)
            self.save_dataframe_to_database(capec_tool_relations, CapecToolRel)
            self.save_dataframe_to_database(tool_phases_relations, ToolPhaseRel)
        elif database == 'Macm':
            macm_df = self.macm_utils.read_macm(database=neo4j_db)
            tool_asset_type_df = self.macm_utils.tool_asset_type_rel(database=neo4j_db)
            app_name = macm_df['Application'].iloc[0]
            macm_user_df = pd.DataFrame({'UserID': current_user.id, 'AppID': neo4j_db, 'AppName': app_name}, index=[0])
            
            macm_df['App_ID'] = neo4j_db
            tool_asset_type_df['AppID'] = neo4j_db
            
            self.save_dataframe_to_database(macm_df, Macm, replace=False)
            self.save_dataframe_to_database(tool_asset_type_df, ToolAssetRel, replace=False)
            self.save_dataframe_to_database(macm_user_df, MacmUser, replace=False)

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
                    ToolCatalogue.Command,
                    ToolCatalogue.Description.label("Tool_Description"),
                    Capec.Capec_ID,
                    Capec.Name.label("Attack_Pattern"), 
                    Capec.Execution_Flow, 
                    Capec.Description.label("Capec_Description"), 
                    ThreatCatalogue.TID.label("Threat_ID"), 
                    ThreatCatalogue.Asset.label("Asset_Type"), 
                    ThreatCatalogue.Threat, 
                    ThreatCatalogue.Description.label("Threat_Description"), 
                    Macm.Component_ID, 
                    Macm.Name.label("Asset"), 
                    Macm.Parameters,
                    Macm.App_ID.label("AppID"),
                    PentestPhases.PhaseID.label("PhaseID"),
                    PentestPhases.PhaseName.label("PhaseName")
                ).select_from(Macm).join(ThreatCatalogue, Macm.Type==ThreatCatalogue.Asset).join(CapecThreatRel).join(Capec).join(CapecToolRel).join(ToolCatalogue).join(ToolAssetRel, and_(Macm.Component_ID==ToolAssetRel.ComponentID, ToolAssetRel.ToolID==ToolCatalogue.ToolID, Macm.App_ID==ToolAssetRel.AppID)).join(ToolPhaseRel, ToolCatalogue.ToolID==ToolPhaseRel.ToolID).join(PentestPhases, ToolPhaseRel.PhaseID==PentestPhases.PhaseID).add_columns(row_number_column)
        compiled = query.compile(compile_kwargs={"literal_binds": True})
        response = {'query': str(compiled)}
        
        return response
            

    # def test_function(self):
    #     response = {}
    #     attack_data = AttackView.query.all()
    #     response['output'] = str(attack_data)
    #     return response

class ThreatAgentUtils():
    converter = Converter()

    def __init__(self):
        self.base_path = Config.DBS_PATH
        self.file_path = f"{self.base_path}/{Config.THREAT_CATALOG_FILE_NAME}"
        # self.threat_catalog_df = self.load_threat_catalog()

    def load_threat_agent_category_df(self):
        print("\nLoading threat agents info...\n")
        df = pd.read_excel(self.file_path, sheet_name="ThreatAgentCategory", header=0)
        #df.replace(np.nan, None, inplace=True) # replace NaN with None
        df = df.astype('str')
        columns_to_convert = ['Reply', 'Attribute']
        for column in columns_to_convert:
            df[column] = df[column].apply(lambda x: self.converter.string_to_list(x))
        return df

    def load_threat_agent_questions(self):
        print("\nLoading threat questions info...\n")
        df = pd.read_excel(self.file_path, sheet_name="ThreatAgentQuestions", header=0)
        df = df.astype('str')
        columns_to_convert = ['Replies']
        for column in columns_to_convert:
            df[column] = df[column].apply(lambda x: self.converter.string_to_list(x))
        return df

    def load_threat_agent_replies(self):
        print("\nLoading threat replies info...\n")
        df = pd.read_excel(self.file_path, sheet_name="ThreatAgentReply", header=0)
        df = df.astype('str')
        return df

    def load_threat_agent_attributes(self):
        print("\nLoading threat agent attributes info...\n")
        df = pd.read_excel(self.file_path, sheet_name="ThreatAgentAttribute", header=0)
        df = df.astype('str')
        return df