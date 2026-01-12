import json
import traceback
from stix2 import FileSystemStore, FileSystemSource
import os
import pandas as pd
import numpy as np
from neo4j import Result
import re

from apps.celery_module.tasks import test_celery
from apps.exception.MACMCheckException import MACMCheckException
from apps.my_modules.converter import Converter
from neo4j import GraphDatabase
import sqlalchemy
from sqlalchemy import inspect, func, text
from sqlalchemy.orm import sessionmaker
from apps.databases.models import App, AssetTypes, MacmChecks, MethodologyCatalogue, MethodologyView, PentestPhases, Protocols, Settings, ThreatAgentAttribute, ThreatAgentAttributesCategory, ThreatAgentCategory, ThreatAgentQuestion, ThreatAgentQuestionReplies, ThreatAgentReply, ThreatAgentReplyCategory, ThreatCatalogue, Capec, CapecThreatRel, ThreatModel, ToolCatalogue, CapecToolRel, Macm, AttackView, Attack, MacmUser, ToolPhaseRel, ThreatAgentRiskScores, StrideImpactRecord, RiskRecord
from flask_login import current_user
from apps.config import Config
from apps import db
from flask import g

from apps.notifications.notify import create_notification, create_send_notification, send_notification


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

	@staticmethod
	def get_catalog_filename():
		from flask import current_app as app
		with app.app_context():
			setting = Settings.query.filter_by(key='catalogs_filename').first()
			return setting.value if setting else None

	@property
	def file_path(self):
		filename = self.get_catalog_filename()
		return f"{self.base_path}/{filename}" if filename else None

	def load_threat_catalog(self):
		file_path = self.file_path
		if not file_path or not os.path.exists(file_path):
			raise FileNotFoundError("Catalog file not found")
		print("\nLoading threat catalogue...\n")
		df = pd.read_excel(file_path, sheet_name="Threat Components", header=0)
		df.replace(np.nan, None, inplace=True) # replace NaN with None
		# df = df.astype('str')
		columns_to_convert = ['EasyOfDiscovery', 'EasyOfExploit', 'Awareness', 'IntrusionDetection', 'LossOfConfidentiality', 'LossOfIntegrity', 'LossOfAvailability', 'LossOfAccountability']
		# column as string except for colums_to_convert
		for column in df.columns:
			if column not in columns_to_convert:
				df[column] = df[column].astype('str')
		columns_to_convert = ['CapecMeta', 'CapecStandard', 'CapecDetailed']
		for column in columns_to_convert:
			df[column] = df[column].apply(lambda x: self.converter.string_to_list(x))
		return df

class ToolCatalogUtils:

	converter = Converter()

	def __init__(self):
		self.base_path = Config.DBS_PATH

	@staticmethod
	def get_catalog_filename():
		from flask import current_app as app
		with app.app_context():
			setting = Settings.query.filter_by(key='catalogs_filename').first()
			return setting.value if setting else None

	@property
	def file_path(self):
		filename = self.get_catalog_filename()
		return f"{self.base_path}/{filename}" if filename else None

	def load_tools_catalog(self):
		file_path = self.file_path
		if not file_path or not os.path.exists(file_path):
			raise FileNotFoundError("Catalog file not found")
		print("\nLoading tools catalog...\n")
		df = pd.read_excel(file_path, sheet_name="Tools", header=0)
		df.replace(np.nan, None, inplace=True) # replace NaN with None
		df['AllowedReportExtensions'] = df['AllowedReportExtensions'].apply(lambda x: self.converter.string_to_list(x))
		df['CapecID'] = df['CapecID'].apply(lambda x: self.converter.string_to_list(x))
		df['PhaseID'] = df['PhaseID'].apply(lambda x: self.converter.string_to_int_list(x))
		return df

	def load_pentest_phases(self):
		file_path = self.file_path
		if not file_path or not os.path.exists(file_path):
			raise FileNotFoundError("Catalog file not found")
		print("\nLoading pentest phases...\n")
		df = pd.read_excel(file_path, sheet_name="Pentest Phases", header=0)
		df.replace(np.nan, None, inplace=True)
		df['PhaseID'] = df['PhaseID'].apply(lambda x: int(x) if x is not None else None)
		df['IsSubPhaseOf'] = df['IsSubPhaseOf'].apply(lambda x: int(x) if x is not None else None)
		print(df)
		return df

class AssetTypesCatalogUtils:

	converter = Converter()

	def __init__(self):
		self.base_path = Config.DBS_PATH

	@staticmethod
	def get_catalog_filename():
		from flask import current_app as app
		with app.app_context():
			setting = Settings.query.filter_by(key='catalogs_filename').first()
			return setting.value if setting else None

	@property
	def file_path(self):
		filename = self.get_catalog_filename()
		return f"{self.base_path}/{filename}" if filename else None

	def load_asset_types_catalog(self):
		file_path = self.file_path
		if not file_path or not os.path.exists(file_path):
			raise FileNotFoundError("Catalog file not found")
		print("\nLoading Asset Types catalog...\n")
		df = pd.read_excel(file_path, sheet_name="AssetTypes", header=0)
		df.rename(columns={'ID': 'AssetTypeID', 'Primary Label': 'PrimaryLabel', 'Secondary Label': 'SecondaryLabel'}, inplace=True)
		df.replace(np.nan, None, inplace=True) # replace NaN with None
		return df

class ProtocolsCatalogUtils:

	converter = Converter()

	def __init__(self):
		self.base_path = Config.DBS_PATH

	@staticmethod
	def get_catalog_filename():
		from flask import current_app as app
		with app.app_context():
			setting = Settings.query.filter_by(key='catalogs_filename').first()
			return setting.value if setting else None

	@property
	def file_path(self):
		filename = self.get_catalog_filename()
		return f"{self.base_path}/{filename}" if filename else None

	def load_protocols_catalog(self):
		file_path = self.file_path
		if not file_path or not os.path.exists(file_path):
			raise FileNotFoundError("Catalog file not found")
		print("\nLoading Protocols catalog...\n")
		df = pd.read_excel(file_path, sheet_name="Protocols", header=0)
		df.rename(columns={'Extended Name': 'ExtendedName', 'Layer': 'ISOLayer'}, inplace=True)
		# df['Ports'] = df['Ports'].apply(lambda x: self.converter.string_to_int_list(x))
		df.replace(np.nan, None, inplace=True) # replace NaN with None
		return df
	
class MethodologyCatalogUtils:

	converter = Converter()

	def __init__(self):
		self.base_path = Config.DBS_PATH

	@staticmethod
	def get_catalog_filename():
		from flask import current_app as app
		with app.app_context():
			setting = Settings.query.filter_by(key='catalogs_filename').first()
			return setting.value if setting else None

	@property
	def file_path(self):
		filename = self.get_catalog_filename()
		return f"{self.base_path}/{filename}" if filename else None

	def load_methodology_catalog(self):
		file_path = self.file_path
		if not file_path or not os.path.exists(file_path):
			raise FileNotFoundError("Catalog file not found")
		print("\nLoading methodology catalog...\n")
		df = pd.read_excel(file_path, sheet_name="Methodologies", header=0)
		df.replace(np.nan, None, inplace=True) # replace NaN with None
		return df

class MACMCheckCatalogUtils:

	converter = Converter()

	def __init__(self):
		self.base_path = Config.DBS_PATH

	@staticmethod
	def get_catalog_filename():
		from flask import current_app as app
		with app.app_context():
			setting = Settings.query.filter_by(key='catalogs_filename').first()
			return setting.value if setting else None

	@property
	def file_path(self):
		filename = self.get_catalog_filename()
		return f"{self.base_path}/{filename}" if filename else None

	def load_macm_checks_catalog(self):
		file_path = self.file_path
		if not file_path or not os.path.exists(file_path):
			raise FileNotFoundError("Catalog file not found")
		print("\nLoading MACM Checks catalog...\n")
		df = pd.read_excel(file_path, sheet_name="MACMChecks", header=0)
		df.replace(np.nan, None, inplace=True) # replace NaN with None
		return df

class MacmUtils:

	converter = Converter()

	def __init__(self):
		self.URI_NEO4J  = os.getenv('URI_NEO4J'     , None)
		self.USER_NEO4J = os.getenv('USER_NEO4J'    , None)
		self.PASS_NEO4J = os.getenv('PASS_NEO4J'    , None)

		self.driver = GraphDatabase.driver(self.URI_NEO4J, auth=(self.USER_NEO4J, self.PASS_NEO4J), initial_retry_delay=10)
		# self.driver.verify_connectivity()

	def clear_database(self, database):
		self.driver.execute_query("MATCH (n) DETACH DELETE n", database_=database)

	def create_database(self, database):
		self.driver.execute_query(f"CREATE DATABASE `{database}`")
	
	def delete_database(self, database):
		self.driver.execute_query(f"DROP DATABASE `{database}`")

	def make_query(self, query, database='macm'):
		try:
			output = self.driver.execute_query(query, database_=database, result_transformer_=Result.to_df)
			return output
		except Exception as error:
			print(f"Error executing query {query}: {error}")
			return None

	def check_database_exists(self, database):
		try:
			output = self.driver.execute_query(f"SHOW DATABASE {database}", result_transformer_=Result.to_df)
			if output.empty:
				print(f"Database {database} does not exist.")
				return False
			return True
		except Exception as error:
			print(f"Error checking if database {database} exists: {error}")
			return False

	def get_greatest_component_id(self, database='macm'):
		query = "MATCH (asset) RETURN max(toInteger(asset.component_id)) as max_id"
		max_id = self.driver.execute_query(query, database_=database, result_transformer_=Result.to_df).iloc[0]['max_id']
		return max_id if max_id is not None else 0
	
	def get_macm_info(self, database='macm'):
		app = App.query.filter_by(AppID=database).with_entities(App.AppID, App.Name).first()
		maxID = self.get_greatest_component_id(database)
		return app.AppID, app.Name, maxID

	def read_macm(self, database='macm'):
		macm_df: pd.DataFrame = self.driver.execute_query("MATCH (asset) RETURN asset.component_id, asset.name, asset.type, asset.app_id, asset.parameters, labels(asset)", database_=database, result_transformer_=Result.to_df)
		macm_df.rename(columns={'asset.component_id': 'Component_ID', 'asset.name': 'Name', 'asset.type': 'Type', 'asset.app_id': 'App_ID', 'asset.parameters': 'Parameters', 'labels(asset)': 'Labels'}, inplace=True)
		macm_df['Parameters'] = macm_df['Parameters'].apply(lambda x: json.loads(x) if x is not None else None)
		return macm_df

	def upload_macm(self, query, app_name, database='macm'):
		try:
			self.clear_database(database)
		except:
			print(f"Database {database} does not exist: creating it...")
			self.create_database(database)
		# self.driver.execute_query("CREATE CONSTRAINT key IF NOT EXISTS FOR (asset:service) REQUIRE asset.component_id IS UNIQUE", database_=database)
		self.load_macm_constraints(database)
		try:
			self.driver.execute_query(query, database_=database)
		except Exception as error:
			print(f"Error uploading MACM: {error}")
			self.delete_database(database)
			raise MACMCheckException(f"{error}")
		Utils().upload_databases('Macm', neo4j_db=database, app_name=app_name)

	def upload_docker_compose(self, dockerComposeContent):
		return self.converter.docker_compose_2_MACM(dockerComposeContent)

	def load_macm_constraints(self, database='macm'):
		try:
			for constraint in MacmChecks.query.where(MacmChecks.Activated==True).with_entities(MacmChecks.Query).all():
				self.driver.execute_query(constraint.Query, database_=database)
		except Exception as error:
			print(f"Error loading MACM constraints: {error}")
			raise error

	def update_macm(self, query, database='macm'):
		try:
			with self.driver.session(database=database) as neo4j_session:
				with neo4j_session.begin_transaction() as transaction:
					for query in query.split(';'):
						transaction.run(query)
					transaction.commit()
					transaction.close()
			# self.delete_macm(database, delete_neo4j=False)
			Utils().upload_databases('Macm', neo4j_db=database)
		except Exception as error:
			print(f"Error updating MACM: {error}")
			raise error

	def delete_macm_component(self, database, component_id):
		try:
			Macm.query.filter_by(App_ID=database, Component_ID=component_id).delete()
			Attack.query.filter_by(AppID=database, ComponentID=component_id).delete()
			self.driver.execute_query(f"MATCH (asset {{component_id: '{component_id}'}}) DETACH DELETE asset", database_=database)
			db.session.commit()
			return True
		except Exception as error:
			print(f"Error deleting component {component_id} from MACM {database}")
			print(error)
			return False

	def rename_macm(self, app_id, new_name):
		try:
			if MacmUser.query.filter_by(AppID=app_id, UserID=current_user.id, IsOwner=True).first() is None:
				app_name = App.query.filter_by(AppID=app_id).with_entities(App.Name).first()[0]
				raise Exception(f"User {current_user.username} is not the owner of MACM {app_name}")
			if new_name.strip() == '':
				raise Exception("New name cannot be empty")
			App.query.filter_by(AppID=app_id).update({'Name': new_name})
			db.session.commit()
			return True
		except Exception as error:
			print(f"Error renaming MACM {app_id} to {new_name}:\n {error}")
			raise error

	def delete_macm(self, app_id, delete_neo4j=True):
		try:
			user = g.api_user if hasattr(g, 'api_user') else current_user
			if MacmUser.query.filter_by(AppID=app_id, UserID=user.id, IsOwner=True).first() is None:
				app_name = App.query.filter_by(AppID=app_id).with_entities(App.Name).first()[0]
				raise Exception(f"User {user.username} is not the owner of MACM {app_name}")
			App.query.filter_by(AppID=app_id).delete()
			Macm.query.filter_by(App_ID=app_id).delete()
			MacmUser.query.filter_by(AppID=app_id).delete()
			Attack.query.filter_by(AppID=app_id).delete()
			if delete_neo4j:
				self.delete_database(app_id)
			db.session.commit()
			return True
		except Exception as error:
			print(f"Error deleting MACM {app_id}:\n {error}")
			traceback.print_exc()
			raise error
	
	def share_macm(self, app_id, users):
		try:
			owner = MacmUser.query.filter_by(AppID=app_id, IsOwner=True).with_entities(MacmUser.UserID).first()[0]
			app_name = App.query.filter_by(AppID=app_id).with_entities(App.Name).first()[0]
			if owner is not current_user.id:
				raise Exception(f"User {current_user.username} is not the owner of MACM {app_name}")
			current_users = MacmUser.query.filter_by(AppID=app_id).where(MacmUser.UserID != current_user.id).all()
			print(users)
			if users is None or users == '':
				users = []
			else:
				users = self.converter.string_to_int_list(users)
			for user in current_users:
				if user.UserID not in users:
					MacmUser.query.filter_by(AppID=app_id, UserID=user.UserID).delete()
			for user in users:
				if MacmUser.query.filter_by(AppID=app_id, UserID=user).first() is None:
					macm_user = MacmUser(AppID=app_id, AppName=app_name, UserID=user, IsOwner=False)
					db.session.add(macm_user)
			db.session.commit()
			for user in users:
				if user != current_user.id:
					create_send_notification(f"MACM '{app_name}' shared with you", f"User '{current_user.username}' has shared the MACM '{app_name}' with you.", links={"Go to MACM":"/macm"}, user_id=user)
			return True
		except Exception as error:
			raise error

	def unshare_macm(self, app_id, user_id):
		try:
			owner = MacmUser.query.filter_by(AppID=app_id, IsOwner=True).with_entities(MacmUser.UserID).first()[0]
			app_name = App.query.filter_by(AppID=app_id).with_entities(App.Name).first()[0]
			if owner is current_user.id:
				raise Exception(f"User {current_user.username} is the owner of MACM {app_name}")
			MacmUser.query.filter_by(AppID=app_id, UserID=user_id).delete()
			db.session.commit()
			return True
		except Exception as error:
			print(f"Error unsharing MACM {app_id} with user {user_id}:\n {error}")
			raise error

	def tool_asset_type_rel(self, database='macm'):
		queries = ToolCatalogue.query.with_entities(ToolCatalogue.ToolID, ToolCatalogue.CypherQuery).all()
		tool_asset_type_df = pd.DataFrame(columns=['ToolID', 'ComponentID', 'Parameters'])
		for query in queries:
			if query.CypherQuery is not None:
				components = self.driver.execute_query(query.CypherQuery, database_=database).records
				for component in components:
					if 'parameters' in component.keys():
						parameters = component['parameters']
					else:
						parameters = None
					components_to_add = pd.DataFrame({'ToolID': query.ToolID, 'ComponentID': component['component_id'], 'Parameters': parameters}, index=[0])
					tool_asset_type_df = pd.concat([tool_asset_type_df, components_to_add], ignore_index=True)
		tool_asset_type_df.drop_duplicates(inplace=True)
		tool_asset_type_df['Parameters'] = tool_asset_type_df['Parameters'].apply(lambda x: json.loads(x) if x is not None else None)
		return tool_asset_type_df

	def add_extra_components(self, database='macm'):
		try:
			query = "MATCH (asset:JetRacer) RETURN asset.component_id AS component_id"
			output = self.make_query(query, database)
			return output
		except Exception as error:
			print(f"Error adding extra components to MACM {database}:\n {error}")
			raise error

class Utils:

	def __init__(self):
		self.attack_pattern_utils = AttackPatternUtils()
		self.threat_catalog_utils = ThreatCatalogUtils()
		self.tool_catalog_utils = ToolCatalogUtils()
		self.macm_utils = MacmUtils()
		self.methodology_catalog_utils = MethodologyCatalogUtils()
		self.macm_check_catalog_utils = MACMCheckCatalogUtils()
		self.risk_analysis_catalog_utils = RiskAnalysisCatalogUtils()
		self.asset_types_catalog_utils = AssetTypesCatalogUtils()
		self.protocols_catalog_utils = ProtocolsCatalogUtils()
		self.engine = sqlalchemy.create_engine(Config.SQLALCHEMY_DATABASE_URI)

	def save_dataframe_to_database(self, df: pd.DataFrame, mapper, replace=True):
		print(f"\nLoading dataframe {mapper.__name__} to database...\n")
		Session = sessionmaker(bind=self.engine)
		session = Session()
		if inspect(self.engine).has_table(mapper.__tablename__):
			if replace:
				if self.engine.name != 'sqlite':
					session.execute(text(f"SET FOREIGN_KEY_CHECKS=0"))
					session.commit()
				# mapper.__table__.drop(self.engine)
				session.query(mapper).delete()
				session.commit()
				if self.engine.name != 'sqlite':
					session.execute(text(f"SET FOREIGN_KEY_CHECKS=1"))
					session.commit()
		mapper.metadata.create_all(self.engine)
		session.bulk_insert_mappings(mapper, df.to_dict(orient="records", index=True), render_nulls=False)
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
	
	def load_threat_agent_quesions_replies(self, df: pd.DataFrame):
		print("\nExtracting ThreatAgentQuestions-ThreatAgentReply relations to database...\n")
		relations_df = pd.DataFrame(columns=['Question_id', 'Reply_id'])
		for _, question in df.iterrows():
			for reply in question['Replies']:
				relations_df.loc[len(relations_df)] = {'Question_id': question['ID'], 'Reply_id': reply}
		relations_df.drop_duplicates(inplace=True)
		relations_df.index.name = 'Id'
		return relations_df
	
	def load_threat_agent_category_attributes(self, df: pd.DataFrame):
		print("\nExtracting ThreatAgentCategory-ThreatAgentAttribute relations to database...\n")
		relations_df = pd.DataFrame(columns=['Category_id', 'Attribute_id'])
		for _, category in df.iterrows():
			for attribute in category['Attribute']:
				relations_df.loc[len(relations_df)] = {'Category_id': category['ID'], 'Attribute_id': attribute}
		relations_df.drop_duplicates(inplace=True)
		relations_df.index.name = 'Id'
		return relations_df
	
	def load_threat_agent_reply_categories(self, df: pd.DataFrame):
		print("\nExtracting ThreatAgentReply-ThreatAgentCategory relations to database...\n")
		relations_df = pd.DataFrame(columns=['Reply_id', 'Category_id'])
		for _, category in df.iterrows():
			for reply in category['Reply']:
				relations_df.loc[len(relations_df)] = {'Reply_id': reply, 'Category_id': category['ID']}
		relations_df.drop_duplicates(inplace=True)
		relations_df.index.name = 'Id'
		return relations_df

	def upload_databases(self, database, app_name=None, neo4j_db='macm'):
		if database == 'Capec':
			attack_pattern_df = self.attack_pattern_utils.load_attack_patterns()
			self.save_dataframe_to_database(attack_pattern_df, Capec)
		elif database == 'ThreatCatalog':
			threat_catalog_df = self.threat_catalog_utils.load_threat_catalog()
			threat_capec_relations = self.load_capec_threat_relations(threat_catalog_df)
			self.save_dataframe_to_database(threat_catalog_df, ThreatCatalogue)
			self.save_dataframe_to_database(threat_capec_relations, CapecThreatRel)
		elif database == 'ToolCatalog':
			tool_catalog_df = self.tool_catalog_utils.load_tools_catalog()
			pentest_phases_df = self.tool_catalog_utils.load_pentest_phases()
			capec_tool_relations = self.load_capec_tool_relations(tool_catalog_df)
			tool_phases_relations = self.laod_tool_phases_relations(tool_catalog_df)
			self.save_dataframe_to_database(pentest_phases_df, PentestPhases)
			self.save_dataframe_to_database(tool_catalog_df, ToolCatalogue)
			self.save_dataframe_to_database(capec_tool_relations, CapecToolRel)
			self.save_dataframe_to_database(tool_phases_relations, ToolPhaseRel)
		elif database == 'MethodologyCatalog':
			methodology_catalog_df = self.methodology_catalog_utils.load_methodology_catalog()
			self.save_dataframe_to_database(methodology_catalog_df, MethodologyCatalogue)
		elif database == 'MACMChecksCatalog':
			macm_checks_catalog_df = self.macm_check_catalog_utils.load_macm_checks_catalog()
			self.save_dataframe_to_database(macm_checks_catalog_df, MacmChecks)
		elif database == 'AssetTypesCatalog':
			asset_types_catalog_df = self.asset_types_catalog_utils.load_asset_types_catalog()
			self.save_dataframe_to_database(asset_types_catalog_df, AssetTypes)
		elif database == 'ProtocolsCatalog':
			protocols_catalog_df = self.protocols_catalog_utils.load_protocols_catalog()
			self.save_dataframe_to_database(protocols_catalog_df, Protocols)
		elif database == 'RiskAnalysisCatalog':
			threat_agent_category_df = self.risk_analysis_catalog_utils.load_threat_agent_category_df()
			threat_agent_questions_df = self.risk_analysis_catalog_utils.load_threat_agent_questions()
			threat_agent_questions_replies = self.load_threat_agent_quesions_replies(threat_agent_questions_df)
			threat_agent_reply_df = self.risk_analysis_catalog_utils.load_threat_agent_reply()
			threat_agent_attributes_df = self.risk_analysis_catalog_utils.load_threat_agent_attributes()
			threat_agent_category_attributes = self.load_threat_agent_category_attributes(threat_agent_category_df)
			threat_agent_reply_categories = self.load_threat_agent_reply_categories(threat_agent_category_df)
			self.save_dataframe_to_database(threat_agent_reply_df, ThreatAgentReply)
			self.save_dataframe_to_database(threat_agent_questions_df, ThreatAgentQuestion)
			self.save_dataframe_to_database(threat_agent_questions_replies, ThreatAgentQuestionReplies)
			self.save_dataframe_to_database(threat_agent_category_df, ThreatAgentCategory)
			self.save_dataframe_to_database(threat_agent_attributes_df, ThreatAgentAttribute)
			self.save_dataframe_to_database(threat_agent_category_attributes, ThreatAgentAttributesCategory)
			self.save_dataframe_to_database(threat_agent_reply_categories, ThreatAgentReplyCategory)
		elif database == 'Macm':
			user = g.api_user if hasattr(g, 'api_user') else current_user
			macm_df = self.macm_utils.read_macm(database=neo4j_db)
			tool_asset_type_df = self.macm_utils.tool_asset_type_rel(database=neo4j_db)
			macm_user_df = pd.DataFrame({'UserID': user.id, 'AppID': neo4j_db, 'IsOwner': True}, index=[0])
			app_df = pd.DataFrame({'AppID': neo4j_db, 'Name': app_name}, index=[0])
			macm_df['App_ID'] = neo4j_db
			tool_asset_type_df['AppID'] = neo4j_db

			# check if components already exist in database
			for component_id in macm_df['Component_ID']:
				if Macm.query.filter_by(App_ID=neo4j_db, Component_ID=component_id).first() is not None:
					macm_df = macm_df[macm_df['Component_ID'] != component_id]
					tool_asset_type_df = tool_asset_type_df[tool_asset_type_df['ComponentID'] != component_id]
					macm_user_df = macm_user_df[macm_user_df['AppID'] != neo4j_db]
			
			if App.query.filter_by(AppID=neo4j_db).first() is None:
				self.save_dataframe_to_database(app_df, App, replace=False)
			self.save_dataframe_to_database(macm_user_df, MacmUser, replace=False)
			self.save_dataframe_to_database(macm_df, Macm, replace=False)
			self.save_dataframe_to_database(tool_asset_type_df, Attack, replace=False)

			AttackView.metadata.create_all(self.engine)
			ThreatModel.metadata.create_all(self.engine)
			MethodologyView.metadata.create_all(self.engine)

	def test_function(self):
		response = {}
		test_celery.delay(current_user.id)
		response['output'] = 'Celery task test_celery invoked'
		return response

class RiskAnalysisCatalogUtils:
	converter = Converter()

	def __init__(self):
		self.base_path = Config.DBS_PATH

	@staticmethod
	def get_catalog_filename():
		from flask import current_app as app
		with app.app_context():
			setting = Settings.query.filter_by(key='catalogs_filename').first()
			return setting.value if setting else None

	@property
	def file_path(self):
		filename = self.get_catalog_filename()
		return f"{self.base_path}/{filename}" if filename else None

	def load_threat_agent_category_df(self):
		file_path = self.file_path
		if not file_path or not os.path.exists(file_path):
			raise FileNotFoundError("Catalog file not found")
		print("\nLoading threat agents info...\n")
		df = pd.read_excel(file_path, sheet_name="ThreatAgentCategory", header=0)
		#df.replace(np.nan, None, inplace=True) # replace NaN with None
		df = df.astype('str')
		columns_to_convert = ['Reply', 'Attribute']
		for column in columns_to_convert:
			df[column] = df[column].apply(lambda x: self.converter.string_to_list(x))
		return df

	def load_threat_agent_questions(self):
		file_path = self.file_path
		if not file_path or not os.path.exists(file_path):
			raise FileNotFoundError("Catalog file not found")
		print("\nLoading threat questions info...\n")
		df = pd.read_excel(file_path, sheet_name="ThreatAgentQuestions", header=0)
		df = df.astype('str')
		columns_to_convert = ['Replies']
		for column in columns_to_convert:
			df[column] = df[column].apply(lambda x: self.converter.string_to_list(x))
		return df

	def load_threat_agent_reply(self):
		file_path = self.file_path
		if not file_path or not os.path.exists(file_path):
			raise FileNotFoundError("Catalog file not found")
		print("\nLoading threat replies info...\n")
		df = pd.read_excel(file_path, sheet_name="ThreatAgentReply", header=0)
		df = df.astype('str')
		return df

	def load_threat_agent_attributes(self):
		file_path = self.file_path
		if not file_path or not os.path.exists(file_path):
			raise FileNotFoundError("Catalog file not found")
		print("\nLoading threat agent attributes info...\n")
		df = pd.read_excel(file_path, sheet_name="ThreatAgentAttribute", header=0)
		df = df.astype('str')
		return df

	def reverse_map_stride(self,input_data):
		# Reverse mapping dictionary
		reverse_stride_mapping = {
			"S": "spoofing",
			"T": "tampering",
			"R": "reputation",
			"I": "informationdisclosure",
			"D": "dos",
			"E": "elevationofprivileges",
			"STRIDE": ["spoofing", "tampering", "reputation", "informationdisclosure", "dos", "elevationofprivileges"],
			"NONE": "None",
		}

		# Normalize input: Handle both single and comma-separated inputs
		if isinstance(input_data, str):
			abbreviations = input_data.strip().upper().split(",")
		else:
			return ["Unknown"]  # If input is not a string

		# Initialize an empty list for the mapped terms
		mapped_terms = []

		for abbr in abbreviations:
			# Handle the "STRIDE" case by extending the list with all STRIDE elements
			term = reverse_stride_mapping.get(abbr.strip(), "Unknown")
			if abbr.strip() == "STRIDE" and isinstance(term, list):
				mapped_terms.extend(term)  # Add all STRIDE elements
			elif term != "Unknown":
				mapped_terms.append(term)  # Add regular mappings

		return mapped_terms

	def map_stride(self,input_data):
		# Reverse mapping dictionary for STRIDE
		reverse_stride_mapping = {
			"S": "Spoofing",
			"T": "Tampering",
			"R": "Repudiation",
			"I": "Information Disclosure",
			"D": "Denial of Service (DoS)",
			"E": "Elevation of Privileges",
			"STRIDE": ["Spoofing", "Tampering", "Repudiation", "Information Disclosure", "Denial of Service (DoS)",
						"Elevation of Privileges"],
			"NONE": "None",
		}

		# Normalize input: Handle both single and comma-separated inputs
		if isinstance(input_data, str):
			abbreviations = input_data.strip().upper().split(",")
		else:
			return "Unknown"  # If input is not a string, return "Unknown"

		# Initialize an empty list for the mapped terms
		mapped_terms = []

		for abbr in abbreviations:
			# Handle the "STRIDE" case by extending the list with all STRIDE elements
			term = reverse_stride_mapping.get(abbr.strip(), "Unknown")
			if abbr.strip() == "STRIDE" and isinstance(term, list):
				mapped_terms.extend(term)  # Add all STRIDE elements
			elif term != "Unknown":
				mapped_terms.append(term)  # Add regular mappings

		# Join the terms into a single string
		return ", ".join(mapped_terms)

	def merge_threat_agent_reply_categories(self,sets):
		"""
		Unisce insiemi di oggetti ThreatAgentReplyCategory evitando duplicati.

		:param sets: Lista di liste di oggetti ThreatAgentReplyCategory
		:return: Lista unita senza duplicati
		"""
		unique_items = {}
		result = []

		for category_set in sets:
			for category in category_set:
				# Crea una chiave unica basata sugli attributi principali
				unique_key = (category.id, category.reply_id, category.category_id)
				if unique_key not in unique_items:
					unique_items[unique_key] = category
					result.append(category)

		return result

	def intersect_threat_agents(self,set1, set2):
		"""
		Restituisce la lista di ThreatAgentReplyCategory comuni tra due insiemi,
		basata esclusivamente sul campo 'category_id'.

		:param set1: Primo insieme di ThreatAgentReplyCategory
		:param set2: Secondo insieme di ThreatAgentReplyCategory
		:return: Lista di ThreatAgentReplyCategory comuni per 'category_id'
		"""
		# Crea un dizionario per il primo set basato su 'category_id'
		set1_dict = {category.Category_id: category for category in set1}

		# Trova le categorie comuni tra set1 e set2 in base a 'category_id'
		common_categories = [
			category for category in set2
			if category.Category_id in set1_dict
		]

		return common_categories

	def remove_duplicates_by_category_id(self,threat_agent_set):
		"""
		Rimuove duplicati da un set basandosi sul campo 'category_id'.

		:param threat_agent_set: Insieme di ThreatAgentReplyCategory
		:return: Set senza duplicati basato su 'category_id'
		"""
		unique_categories = {}

		# Itera sugli oggetti del set
		for category in threat_agent_set:
			# Usa 'category_id' come chiave per mantenere solo un'istanza per ID
			unique_categories[category.Category_id] = category

		# Ritorna i valori unici come un set
		return set(unique_categories.values())

	def wizard_completed(self,appId):

		# Check if the ThreatAgentRiskScore exists for the application
		completed = False
		threat_agent_score = ThreatAgentRiskScores.query.filter_by(AppID=appId).first()
		if threat_agent_score:
			completed = True
		return completed

	def stride_impact_completed(self,appId):
		# Check if the STRIDE impact records exist for the application
		stride_impact_records = StrideImpactRecord.query.filter_by(AppID=appId).all()
		return len(stride_impact_records) > 5

	def get_category(self,value):
		if value < 3.0:
			return "Low"
		elif value < 7.0:
			return "Medium"
		else:
			return "High"

	def calculate_likelihood(self,threat_data):
		likelihood_params = [
			'skill', 'motive', 'opportunity', 'size',
			'ease_of_discovery', 'ease_of_exploit',
			'awareness', 'intrusion_detection'
		]
		sum_values = 0
		count = 0
		for param in likelihood_params:
			val = int(threat_data.get(param, 5))  # default 5
			sum_values += val
			count += 1
		likelihood = sum_values / count if count else 5
		likelihood_category = self.get_category(likelihood)
		return likelihood, likelihood_category

	def calculate_impact(self,threat_data):
		tech_params = [
			'loss_of_confidentiality', 'loss_of_integrity',
			'loss_of_availability', 'loss_of_accountability'
		]
		bus_params = [
			'financialdamage', 'reputationdamage',
			'noncompliance', 'privacyviolation'
		]
		tech_sum = sum(int(threat_data.get(param, 5)) for param in tech_params)
		bus_sum = sum(int(threat_data.get(param, 5)) for param in bus_params)
		technical_impact = tech_sum / len(tech_params)
		business_impact = bus_sum / len(bus_params)
		tech_category = self.get_category(technical_impact)
		bus_category = self.get_category(business_impact)
		return technical_impact, business_impact, tech_category, bus_category

	def calculate_overall_risk(self,likelihood_category, impact_category):
		risk_matrix = {
			"Low": {
				"Low": "Note",
				"Medium": "Low",
				"High": "Medium"
			},
			"Medium": {
				"Low": "Low",
				"Medium": "Medium",
				"High": "High"
			},
			"High": {
				"Low": "Medium",
				"Medium": "High",
				"High": "Critical"
			}
		}
		return risk_matrix.get(likelihood_category, {}).get(impact_category, "Unknown")

	def get_all_threat_ids(self,post_data):
		threat_ids = set()
		for key in post_data.keys():
			if '[' in key and ']' in key:
				threat_id = key.split('[')[0]
				threat_ids.add(threat_id)
		return threat_ids

	def completed_risk_analysis(self,appId):
		try:
			# Calcola le minacce per ciascun componente
			threat_for_each_component = ThreatModel.query.filter_by(AppID=appId).with_entities(
				ThreatModel.Component_ID, func.count(ThreatModel.Component_ID)).group_by(ThreatModel.Component_ID).all()
			threat_for_each_component = self.converter.tuple_list_to_dict(threat_for_each_component)

			# Calcola il numero totale di minacce
			threat_number = ThreatModel.query.filter_by(AppID=appId).count()
		except Exception as e:
			threat_for_each_component = {}
			threat_number = 0

		# Calcolo degli ID dei componenti analizzati
		try:
			analyzed_components = (
				db.session.query(RiskRecord.ComponentID)
				.filter_by(AppID=appId)
				.distinct()
				.all()
			)
			analyzed_component_ids = [c[0] for c in analyzed_components]
		except Exception as e:
			analyzed_component_ids = []

		# Calcola se il passo finale è stato completato (verifica se tutti i componenti hanno almeno un rischio associato)
		components_with_threats = {t.Component_ID for t in ThreatModel.query.filter_by(AppID=appId).all()}
		components_with_risk = {r.ComponentID for r in RiskRecord.query.filter_by(AppID=appId).all()}
		final_step_completed = components_with_threats.issubset(components_with_risk)
		return analyzed_component_ids,final_step_completed