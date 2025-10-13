import json
from datetime import datetime
import re
from sqlalchemy.sql.expression import case
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy import ForeignKey, select, func, and_, or_, UniqueConstraint
from sqlalchemy_utils import create_view

from .types import ExternalReferencesType

from apps import db
from sqlalchemy import UniqueConstraint


# from sqlalchemy import event
# from sqlalchemy.engine import Engine
# from sqlite3 import Connection as SQLite3Connection

# @event.listens_for(Engine, "connect")
# def _set_sqlite_pragma(dbapi_connection, connection_record):
#     if isinstance(dbapi_connection, SQLite3Connection):
#         cursor = dbapi_connection.cursor()
#         cursor.execute("PRAGMA foreign_keys=ON;")
#         cursor.close()

class AlchemyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj.__class__, DeclarativeMeta):
            # Convert SQLAlchemy model to dictionary
            fields = {}
            for field in [x for x in dir(obj) if not x.startswith('_') and x != 'metadata']:
                data = obj.__getattribute__(field)
                try:
                    json.dumps(data)
                    fields[field] = data
                except TypeError:
                    fields[field] = None
            return fields
        return json.JSONEncoder.default(self, obj)

class Bibliography(db.Model):
    
    __tablename__ = 'Bibliography'

    id = db.Column(db.Integer, primary_key=True, nullable=False)
    bibtex = db.Column(db.String(1000), nullable=False)

    def __repr__(self):
        return str(self.bibtex)

class Settings(db.Model):
    
    __tablename__ = 'Settings'

    id = db.Column(db.Integer, primary_key=True, nullable=False)
    key = db.Column(db.String(100), nullable=False)
    value = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return str(self.key)
    
    def __init__(self, **kwargs):
        for property, value in kwargs.items():
            if hasattr(value, '__iter__') and not isinstance(value, str):
                value = value[0]
            setattr(self, property, value)
    
    @staticmethod
    def to_dict() -> dict:
        settings = Settings.query.all()
        return {setting.key: setting.value for setting in settings}

class PentestPhases(db.Model):
    __tablename__ = 'PentestPhases'

    PhaseID = db.Column(db.Integer, primary_key=True, nullable=False)
    PhaseName = db.Column(db.Text)
    IsSubPhaseOf = db.Column(db.Integer)

    def __init__(self, **kwargs):
        for property, value in kwargs.items():
            if hasattr(value, '__iter__') and not isinstance(value, str):
                value = value[0]

            setattr(self, property, value)

    def __repr__(self):
        return str(self.PhaseID)

class AssetTypes(db.Model):
    
    __tablename__ = 'AssetTypes'

    AssetTypeID     = db.Column(db.Integer, primary_key=True, nullable=False)
    Name            = db.Column(db.Text, nullable=False)
    Description     = db.Column(db.Text)
    PrimaryLabel    = db.Column(db.Text)
    SecondaryLabel  = db.Column(db.Text)
    Color           = db.Column(db.Text)
    Ports           = db.Column(db.Text)

    @staticmethod
    def get_colors():
        asset_types_colors = AssetTypes.query.with_entities(AssetTypes.Name, AssetTypes.Color).all()
        return {asset_type.Name: asset_type.Color for asset_type in asset_types_colors}

    @hybrid_property
    def get_ports(self):
        if self.Ports is None:
            return []
        if isinstance(self.Ports, int):
            return [self.Ports]
        ports_str = str(self.Ports).strip()
        if not ports_str:
            return []
        if ports_str.isdigit():
            return [int(ports_str)]
        return [int(p.strip()) for p in re.split(r',\s*', ports_str) if p.strip().isdigit()]

    @staticmethod
    def get_asset_type_by_port(port):
        port = int(port)
        asset_types = AssetTypes.query.all()
        return [at for at in asset_types if port in at.get_ports]

    @staticmethod
    def get_asset_type_by_ports(ports):
        asset_types = []
        for port in ports:
            asset_types.extend(AssetTypes.get_asset_type_by_port(port))
        return list({at.Name for at in asset_types})

    @staticmethod
    def get_suggested_asset_types(port_service_map):
        suggested_asset_types = {}
        for service in port_service_map.items():
            service_name = service[0]
            ports = service[1]
            asset_types = AssetTypes.get_asset_type_by_ports(ports)
            suggested_asset_types[service_name] = asset_types if asset_types else ['Service.App']
        return suggested_asset_types

    def __init__(self, **kwargs):
        for property, value in kwargs.items():
            if hasattr(value, '__iter__') and not isinstance(value, str):
                value = value[0]

            setattr(self, property, value)

    def __repr__(self):
        return str(self.AssetTypeID)

class Protocols(db.Model):
    __tablename__ = 'Protocols'

    ProtocolID = db.Column(db.Integer, primary_key=True, nullable=False)
    Name = db.Column(db.Text, nullable=False)
    ExtendedName = db.Column(db.Text)
    Description = db.Column(db.Text)
    ISOLayer = db.Column(db.Text)
    Relationship = db.Column(db.Text)
    Ports = db.Column(db.Text)

    def __init__(self, **kwargs):
        for property, value in kwargs.items():
            if hasattr(value, '__iter__') and not isinstance(value, str):
                value = value[0]

            setattr(self, property, value)

    def __repr__(self):
        return str(self.ProtocolID)
class Capec(db.Model):
    __tablename__ = 'Capec'

    Capec_ID = db.Column(db.Integer, primary_key=True, nullable=False)
    Created = db.Column(db.TIMESTAMP)
    Created_By_Ref = db.Column(db.JSON)
    Description = db.Column(db.Text)
    Modified = db.Column(db.TIMESTAMP)
    Name = db.Column(db.Text)
    Object_Marking_Refs = db.Column(db.JSON)
    Spec_Version = db.Column(db.Text)
    Abstraction = db.Column(db.Text)
    Alternate_Terms = db.Column(db.JSON)
    Can_Follow_Refs = db.Column(db.JSON)
    Can_Precede_Refs = db.Column(db.JSON)
    Consequences = db.Column(db.JSON)
    Domains = db.Column(db.JSON)
    External_References = db.Column(ExternalReferencesType(10000))
    Example_Instances = db.Column(db.JSON)
    Execution_Flow = db.Column(db.Text)
    Extended_Description = db.Column(db.JSON)
    Likelihood_Of_Attack = db.Column(db.Text)
    Peer_Of_Refs = db.Column(db.JSON)
    Prerequisites = db.Column(db.JSON)
    Resources_Required = db.Column(db.JSON)
    Skills_Required = db.Column(db.JSON)
    Status = db.Column(db.Text)
    Typical_Severity = db.Column(db.Text)
    Version = db.Column(db.Text)
    Capec_Children_ID = db.Column(db.JSON)
    Capec_Parents_ID = db.Column(db.JSON)

    def __init__(self, **kwargs):
        for property, value in kwargs.items():
            if hasattr(value, '__iter__') and not isinstance(value, str):
                value = value[0]

            setattr(self, property, value)

    def __repr__(self):
        return str(self.Capec_ID)

    @hybrid_property
    def abstraction_order(self):
        table_ordering = case(
            (Capec.Abstraction == "Meta", 1),
            (Capec.Abstraction == "Standard", 2),
            (Capec.Abstraction == "Detailed", 3),
            else_=None
        )
        return table_ordering
    
class ThreatCatalogue(db.Model):
    __tablename__ = 'ThreatCatalogue'

    TID = db.Column(db.String(100), primary_key=True, nullable=False)
    Asset = db.Column(db.Text)
    Threat = db.Column(db.Text)
    Description = db.Column(db.Text)
    STRIDE = db.Column(db.Text)
    Compromised = db.Column(db.Text)
    PreC = db.Column(db.JSON)
    PreI = db.Column(db.JSON)
    PreA = db.Column(db.JSON)
    PreCondition = db.Column(db.JSON)
    PostC = db.Column(db.JSON)
    PostI = db.Column(db.JSON)
    PostA = db.Column(db.JSON)
    PostCondition = db.Column(db.JSON)
    Commento = db.Column(db.Text)

    EasyOfDiscovery = db.Column(db.Integer, default=5)
    EasyOfExploit = db.Column(db.Integer, default=5)
    Awareness = db.Column(db.Integer, default=5)
    IntrusionDetection = db.Column(db.Integer, default=5)
    LossOfConfidentiality = db.Column(db.Integer, default=5)
    LossOfIntegrity = db.Column(db.Integer, default=5)
    LossOfAvailability = db.Column(db.Integer, default=5)
    LossOfAccountability = db.Column(db.Integer, default=5)

    hasCapec = db.relationship('Capec', secondary='CapecThreatRel', backref='hasThreat')

    @hybrid_property
    def hasCapecMeta(self):
        ids = db.session.query(Capec.Capec_ID).join(CapecThreatRel).filter(CapecThreatRel.TID == self.TID).filter(
            Capec.Abstraction == 'Meta').all()
        return [id[0] for id in ids]

    @hybrid_property
    def hasCapecStandard(self):
        ids = db.session.query(Capec.Capec_ID).join(CapecThreatRel).filter(CapecThreatRel.TID == self.TID).filter(
            Capec.Abstraction == 'Standard').all()
        return [id[0] for id in ids]

    @hybrid_property
    def hasCapecDetailed(self):
        ids = db.session.query(Capec.Capec_ID).join(CapecThreatRel).filter(CapecThreatRel.TID == self.TID).filter(
            Capec.Abstraction == 'Detailed').all()
        return [id[0] for id in ids]

    def __init__(self, **kwargs):
        for property, value in kwargs.items():
            if hasattr(value, '__iter__') and not isinstance(value, str):
                value = value[0]

            setattr(self, property, value)

    def __repr__(self):
        return str(self.TID)


class CapecThreatRel(db.Model):
    __tablename__ = 'CapecThreatRel'

    Id = db.Column(db.Integer, primary_key=True, nullable=False)
    Capec_ID = db.Column(db.Integer, ForeignKey("Capec.Capec_ID", ondelete='CASCADE'))
    TID = db.Column(db.String(100), ForeignKey("ThreatCatalogue.TID", ondelete='CASCADE'))


class ToolCatalogue(db.Model):
    __tablename__ = 'ToolCatalogue'

    ToolID = db.Column(db.Integer, primary_key=True, nullable=False)
    Name = db.Column(db.Text)
    CapecID = db.Column(db.JSON)
    CypherQuery = db.Column(db.Text)
    Command = db.Column(db.Text)
    Description = db.Column(db.Text)
    PhaseID = db.Column(db.JSON)
    IsExecutable = db.Column(db.Boolean)
    ReportParser = db.Column(db.Text)
    AllowedReportExtensions = db.Column(db.JSON)

    hasPhase = db.relationship("PentestPhases", secondary='ToolPhaseRel', backref='hasTool')
    hasCapec = db.relationship('Capec', secondary='CapecToolRel', backref='hasTool')

    @hybrid_property
    def hasCapecIDs(self):
        ids = db.session.query(Capec.Capec_ID).join(CapecToolRel).filter(CapecToolRel.ToolID == self.ToolID).all()
        return [id[0] for id in ids]

    @hybrid_property
    def hasPhaseIDs(self):
        ids = db.session.query(PentestPhases.PhaseID).join(ToolPhaseRel).filter(
            ToolPhaseRel.ToolID == self.ToolID).all()
        return [id[0] for id in ids]

    def __init__(self, **kwargs):
        for property, value in kwargs.items():
            if hasattr(value, '__iter__') and not isinstance(value, str):
                value = value[0]

            setattr(self, property, value)

    def __repr__(self):
        return str(self.ToolID)


class MethodologyCatalogue(db.Model):
    __tablename__ = 'MethodologyCatalogue'

    MID = db.Column(db.Integer, primary_key=True, nullable=False)
    Name = db.Column(db.Text)
    AssetType = db.Column(db.Text)
    Description = db.Column(db.Text)
    Link = db.Column(db.Text)

    def __init__(self, **kwargs):
        for property, value in kwargs.items():
            if hasattr(value, '__iter__') and not isinstance(value, str):
                value = value[0]
            setattr(self, property, value)

    def __repr__(self):
        return str(self.MID)


class CapecToolRel(db.Model):
    __tablename__ = 'CapecToolRel'

    Id = db.Column(db.Integer, primary_key=True, nullable=False)
    Capec_ID = db.Column(db.Integer, ForeignKey("Capec.Capec_ID", ondelete='CASCADE'))
    ToolID = db.Column(db.Integer, ForeignKey("ToolCatalogue.ToolID", ondelete='CASCADE'))


class Macm(db.Model):
    __tablename__ = 'Macm'

    Id              = db.Column(db.Integer, primary_key=True, nullable=False)
    Component_ID    = db.Column(db.Integer, nullable=False, index=True)
    Name            = db.Column(db.Text)
    Type            = db.Column(db.Text)
    App_ID          = db.Column(db.String(100), ForeignKey("App.AppID", ondelete='CASCADE'), nullable=False, index=True)
    Labels          = db.Column(db.JSON)
    Parameters      = db.Column(db.JSON)

    __table_args__ =  (UniqueConstraint('Component_ID', 'App_ID', name='uix_1'),)

    def __init__(self, **kwargs):
        for property, value in kwargs.items():
            if hasattr(value, '__iter__') and not isinstance(value, str):
                value = value[0]

            setattr(self, property, value)

    def __repr__(self):
        return str(self.Name)

class MacmChecks(db.Model):
    __tablename__ = 'MacmChecks'

    Id = db.Column(db.Integer, primary_key=True, nullable=False)
    Name = db.Column(db.Text)
    Description = db.Column(db.Text)
    Query = db.Column(db.Text)

    def __init__(self, **kwargs):
        for property, value in kwargs.items():
            if hasattr(value, '__iter__') and not isinstance(value, str):
                value = value[0]

            setattr(self, property, value)

    def __repr__(self):
        return str(f'{self.Component_ID}-{self.CheckName}')

class App(db.Model):
    
    __tablename__ = 'App'

    AppID = db.Column(db.String(100), primary_key=True, nullable=False)
    Name = db.Column(db.Text)
    Description = db.Column(db.Text)
    Created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=True)
    Updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=True)

    def __init__(self, **kwargs):
        for property, value in kwargs.items():
            if hasattr(value, '__iter__') and not isinstance(value, str):
                value = value[0]

            setattr(self, property, value)

    def __repr__(self):
        return str(self.Name)

class MacmUser(db.Model):
    __tablename__ = 'MacmUser'

    UserID         = db.Column(db.Integer, ForeignKey("Users.id", ondelete='CASCADE'), primary_key=True, nullable=False)
    AppID          = db.Column(db.String(100), ForeignKey("App.AppID", ondelete='CASCADE'), primary_key=True, nullable=False, index=True)
    IsOwner        = db.Column(db.Boolean)
    User           = db.relationship("Users", backref="MacmUser")
    App            = db.relationship("App", backref="MacmUser")

    def __init__(self, **kwargs):
        for property, value in kwargs.items():
            if hasattr(value, '__iter__') and not isinstance(value, str):
                value = value[0]

            setattr(self, property, value)

    def __repr__(self):
        return str(f'{self.UserID}-{self.AppID}')

    @classmethod
    def usersPerApp(self):
        result = self.query.with_entities(self.AppID, func.group_concat(self.UserID)).group_by(self.AppID).all()
        return {app_id: [int(x) for x in user_ids.split(',')] for app_id, user_ids in result}

    @classmethod
    def ownerPerApp(self):
        result = self.query.with_entities(self.AppID, self.UserID).filter_by(IsOwner=True).all()
        return {app_id: user_id for app_id, user_id in result}
    
class Attack(db.Model):
    __tablename__ = 'Attack'

    Id           = db.Column(db.Integer, primary_key=True, nullable=False)
    ToolID       = db.Column(db.Integer, ForeignKey("ToolCatalogue.ToolID", ondelete='CASCADE'))
    ComponentID  = db.Column(db.Integer, nullable=False)
    AppID        = db.Column(db.String(100), ForeignKey("App.AppID", ondelete='CASCADE'), nullable=False)
    Parameters   = db.Column(db.JSON)
    ReportFiles  = db.Column(db.JSON)
    
    Tool = db.relationship("ToolCatalogue", backref="Attack")

    __table_args__ = (UniqueConstraint('ToolID', 'ComponentID', 'AppID', name='uix_1'),)

    def __repr__(self):
        return str(f'{self.AppID}-{self.ComponentID}-{self.ToolID}')


class ToolPhaseRel(db.Model):
    __tablename__ = 'ToolPhaseRel'

    Id = db.Column(db.Integer, primary_key=True, nullable=False)
    ToolID = db.Column(db.Integer, ForeignKey("ToolCatalogue.ToolID", ondelete='CASCADE'))
    PhaseID = db.Column(db.Integer, ForeignKey("PentestPhases.PhaseID", ondelete='CASCADE'))
    __table_args__ = (UniqueConstraint('ToolID', 'PhaseID', name='uix_1'),)

    def __init__(self, **kwargs):
        for property, value in kwargs.items():
            if hasattr(value, '__iter__') and not isinstance(value, str):
                value = value[0]

            setattr(self, property, value)

    def __repr__(self):
        return str(f'{self.ToolID}-{self.PhaseID}')


class ThreatModel(db.Model):
    # row_number_column = func.row_number().over(order_by=Macm.Component_ID).label('Attack_Number')
    row_number_column = func.row_number().over(partition_by=Macm.App_ID).label('TM_Number')

    __table__ = create_view(
                "ThreatModel",
                select(
                    ThreatCatalogue.TID.label("Threat_ID"), 
                    Macm.Type.label("Asset_Type"), 
                    ThreatCatalogue.Threat, 
                    ThreatCatalogue.Description.label("Threat_Description"),
                    ThreatCatalogue.Compromised,
                    ThreatCatalogue.PreC,
                    ThreatCatalogue.PreI,
                    ThreatCatalogue.PreA,
                    ThreatCatalogue.PostC,
                    ThreatCatalogue.PostI,
                    ThreatCatalogue.PostA,
                    ThreatCatalogue.STRIDE.label("STRIDE"),
                    ThreatCatalogue.EasyOfDiscovery,
                    ThreatCatalogue.EasyOfExploit,
                    ThreatCatalogue.Awareness,
                    ThreatCatalogue.IntrusionDetection,
                    ThreatCatalogue.LossOfConfidentiality,
                    ThreatCatalogue.LossOfIntegrity,
                    ThreatCatalogue.LossOfAvailability,
                    ThreatCatalogue.LossOfAccountability,
                    Macm.Component_ID,
                    Macm.Name.label("Asset"), 
                    Macm.Parameters,
                    App.AppID
                )
                .select_from(Macm)
                .join(App, Macm.App_ID==App.AppID)
                .join(ThreatCatalogue, or_(Macm.Type==ThreatCatalogue.Asset, Macm.Labels.contains(ThreatCatalogue.Asset)))
                .add_columns(row_number_column),
                db.metadata,
                replace=True
                )
    
    def __repr__(self):
        return str(f'{self.Component_ID}-{self.Threat_ID}')


class AttackView(db.Model):
    # row_number_column = func.row_number().over(order_by=Macm.Component_ID).label('Attack_Number')
    row_number_column = func.row_number().over(partition_by=Macm.App_ID).label('Attack_Number')

    __table__ = create_view(
                "AttackView",
                select(
                    ToolCatalogue.ToolID.label("Tool_ID"), 
                    ToolCatalogue.Name.label("Tool_Name"), 
                    ToolCatalogue.Command,
                    ToolCatalogue.Description.label("Tool_Description"),
                    ToolCatalogue.IsExecutable.label("Is_Executable"),
                    ToolCatalogue.ReportParser.label("Report_Parser"),
                    ToolCatalogue.AllowedReportExtensions.label("Allowed_Report_Extensions"),
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
                    Attack.Parameters,
                    App.AppID,
                    PentestPhases.PhaseID.label("PhaseID"),
                    PentestPhases.PhaseName.label("PhaseName"),
                    Attack.ReportFiles
                )
                .select_from(Macm)
                .join(ThreatCatalogue, or_(Macm.Type==ThreatCatalogue.Asset, Macm.Labels.contains(ThreatCatalogue.Asset)))
                .join(CapecThreatRel)
                .join(Capec)
                .join(CapecToolRel)
                .join(ToolCatalogue)
                .join(App, Macm.App_ID==App.AppID)
                .join(Attack, and_(Macm.Component_ID==Attack.ComponentID, Attack.ToolID==ToolCatalogue.ToolID, Macm.App_ID==Attack.AppID))
                .join(ToolPhaseRel, ToolCatalogue.ToolID==ToolPhaseRel.ToolID)
                .join(PentestPhases, ToolPhaseRel.PhaseID==PentestPhases.PhaseID)
                .add_columns(row_number_column),
                db.metadata,
                replace=True
                )
    
    def __repr__(self):
        return str(f'{self.Component_ID}-{self.Capec_ID}')


class MethodologyView(db.Model):
    row_number_column = func.row_number().over(partition_by=Macm.App_ID).label('Methodology_Number')
    __table__ = create_view(
                "MethodologyView",
                select(
                    MethodologyCatalogue.MID, 
                    MethodologyCatalogue.Name, 
                    MethodologyCatalogue.Description,
                    MethodologyCatalogue.AssetType,
                    MethodologyCatalogue.Link,
                    Macm.Component_ID,
                    App.AppID
                ).select_from(Macm)
                .join(App, Macm.App_ID==App.AppID)
                .join(MethodologyCatalogue, Macm.Type==MethodologyCatalogue.AssetType)
                .add_columns(row_number_column),
                db.metadata,
                replace=True
                )
    
    def __repr__(self):
        return str(f'{self.Component_ID}-{self.Methodology_ID}')


class ThreatAgentReply(db.Model):
    __tablename__ = 'ThreatAgentReply'

    Id = db.Column(db.Integer, primary_key=True, nullable=False)  # Unique identifier
    Reply = db.Column(db.Text, nullable=False)  # Reply text (e.g., "Yes", "No")
    Details = db.Column(db.Text, nullable=True)  # Additional details (e.g., "Yes, because...")
    Multiple = db.Column(db.Integer, nullable=False, default=0)  # Multiple indicator (0 or 1)


class ThreatAgentAttribute(db.Model):
    __tablename__ = 'ThreatAgentAttribute'

    Id = db.Column(db.Integer, primary_key=True, nullable=False)
    Attribute = db.Column(db.Text)
    Description = db.Column(db.Text, nullable=True)
    Score = db.Column(db.Integer)
    Attribute = db.Column(db.Text)
    AttributeValue = db.Column(db.Text)
    Description = db.Column(db.Text, nullable=True)
    Score = db.Column(db.Integer)


class ThreatAgentCategory(db.Model):
    __tablename__ = 'ThreatAgentCategory'

    Id = db.Column(db.Integer, primary_key=True, nullable=False)
    Category = db.Column(db.Text)
    Description = db.Column(db.Text)
    CommonAction = db.Column(db.Text)
    hasReply = db.relationship('Reply', secondary='CategoryThreatRel', backref='hasCategory', lazy='dynamic')

    @hybrid_property
    def hasReply(self):
        ids = self.hasReply.filter().with_entities(ThreatAgentReply.Id).all()
        return [id[0] for id in ids]

    @hybrid_property
    def hasAttribute(self):
        ids = self.hasAttribute.filter().with_entities(ThreatAgentAttribute.Id).all()
        return [id[0] for id in ids]


class ThreatAgentQuestion(db.Model):
    __tablename__ = 'ThreatAgentQuestion'

    Id = db.Column(db.Integer, primary_key=True, nullable=False)
    Question = db.Column(db.Text)
    Qid = db.Column(db.Text)
    # Replies       = db.Column(db.Text)
    hasReply = db.relationship('Reply', secondary='CategoryThreatRel', backref='hasCategory', lazy='dynamic')

    @hybrid_property
    def hasReply(self):
        ids = self.hasReply.filter().with_entities(ThreatAgentReply.Id).all()
        return [id[0] for id in ids]


class ThreatAgentAttributesCategory(db.Model):
    __tablename__ = 'ThreatAgentAttributesCategory'

    Id = db.Column(db.Integer, primary_key=True, nullable=False)
    Attribute_id = db.Column(db.Integer, ForeignKey("ThreatAgentAttribute.Id", ondelete='CASCADE'))
    Category_id = db.Column(db.Integer, ForeignKey("ThreatAgentCategory.Id", ondelete='CASCADE'))

    def __repr__(self):
        return f"<ThreatAgentAttributesCategory(id={self.id}, attribute_id={self.attribute_id}, category_id={self.category_id})>"


class ThreatAgentQuestionReplies(db.Model):
    __tablename__ = 'ThreatAgentQuestionReplies'

    Id = db.Column(db.Integer, primary_key=True, nullable=False)
    Question_id = db.Column(db.Integer, ForeignKey("ThreatAgentQuestion.Id", ondelete='CASCADE'))
    Reply_id = db.Column(db.Integer, ForeignKey("ThreatAgentReply.Id", ondelete='CASCADE'))


class ThreatAgentRiskScores(db.Model):
    __tablename__ = 'ThreatAgentRiskScores'

    AppID = db.Column(db.String(100), primary_key=True, nullable=False, index=True)
    Skill = db.Column(db.Integer, nullable=False)
    Size = db.Column(db.Integer, nullable=False)
    Motive = db.Column(db.Integer, nullable=False)
    Opportunity = db.Column(db.Integer, nullable=False)
    Created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=True)
    Updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=True)

    def __init__(self, **kwargs):
        for property, value in kwargs.items():
            if hasattr(value, '__iter__') and not isinstance(value, str):
                value = value[0]
            setattr(self, property, value)

    def save(self):
        try:
            db.session.add(self)  # Aggiungi l'oggetto alla sessione
            db.session.commit()  # Commetti le modifiche
        except Exception as e:
            db.session.rollback()  # Annulla le modifiche se c'è un errore
            print(f"Error saving data: {e}")


class StrideImpactRecord(db.Model):
    _tablename_ = 'StrideImpactRecord'
    ID = db.Column(db.Integer, primary_key=True, autoincrement=True)  # ID come primary key, auto incrementale
    AppID = db.Column(db.String(100), nullable=False)
    Stride = db.Column(db.String(100), nullable=False)
    Financialdamage = db.Column(db.Integer, nullable=False)
    Reputationdamage = db.Column(db.Integer, nullable=False)
    Noncompliance = db.Column(db.Integer, nullable=False)
    Privacyviolation = db.Column(db.Integer, nullable=False)
    Created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=True)
    Updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=True)

    def __init__(self, **kwargs):
        for property, value in kwargs.items():
            if hasattr(value, '__iter__') and not isinstance(value, str):
                value = value[0]
            setattr(self, property, value)

    def save(self):
        try:
            db.session.add(self)  # Aggiungi l'oggetto alla sessione
            db.session.commit()  # Commetti le modifiche
        except Exception as e:
            db.session.rollback()  # Annulla le modifiche se c'è un errore
            print(f"Error saving data: {e}")

    @staticmethod
    def update_or_create(app_id, stride, financialdamage, reputationdamage, noncompliance, privacyviolation):
        # Cerca se esiste già un record con lo stesso appID e stride
        existing_record = StrideImpactRecord.query.filter_by(AppID=app_id, Stride=stride).first()

        if existing_record:
            # Se il record esiste, aggiorna
            existing_record.financialdamage = financialdamage
            existing_record.reputationdamage = reputationdamage
            existing_record.noncompliance = noncompliance
            existing_record.privacyviolation = privacyviolation
            existing_record.updated_at = datetime.utcnow()  # aggiorna la data di modifica
            print(f"Updated record for STRIDE category: {stride}")
        else:
            # Se il record non esiste, inserisci un nuovo record
            new_record = StrideImpactRecord(
                AppID=app_id,
                Stride=stride,
                Financialdamage=financialdamage,
                Reputationdamage=reputationdamage,
                Noncompliance=noncompliance,
                Privacyviolation=privacyviolation,
                Created_at=datetime.utcnow(),
                Updated_at=datetime.utcnow()
            )
            db.session.add(new_record)
            db.session.commit()  # Commit del nuovo record
            print(f"Inserted new record for STRIDE category: {stride}")


class RiskRecord(db.Model):
    __tablename__ = 'RiskRecord'
    AppID = db.Column(db.String(100), primary_key=True, nullable=False, index=True)
    ComponentID = db.Column(db.Integer, primary_key=True, nullable=False, index=True)
    ThreatID = db.Column(db.String(100), primary_key=True, nullable=False, index=True)
    Skill = db.Column(db.Integer, nullable=False)
    Size = db.Column(db.Integer, nullable=False)
    Motive = db.Column(db.Integer, nullable=False)
    Opportunity = db.Column(db.Integer, nullable=False)
    Easyofdiscovery = db.Column(db.Integer, nullable=False)
    Easyofexploit = db.Column(db.Integer, nullable=False)
    Awareness = db.Column(db.Integer, nullable=False)
    Intrusiondetection = db.Column(db.Integer, nullable=False)
    Lossconfidentiality = db.Column(db.Integer, nullable=False)
    Lossintegrity = db.Column(db.Integer, nullable=False)
    Lossavailability = db.Column(db.Integer, nullable=False)
    Lossaccountability = db.Column(db.Integer, nullable=False)
    Financialdamage = db.Column(db.Integer, nullable=False)
    Reputationdamage = db.Column(db.Integer, nullable=False)
    Noncompliance = db.Column(db.Integer, nullable=False)
    Privacyviolation = db.Column(db.Integer, nullable=False)
    Likelihood = db.Column(db.Integer, nullable=False)
    TechnicalImpact = db.Column(db.Integer, nullable=False)
    BusinessImpact = db.Column(db.Integer, nullable=False)
    TechnicalRisk = db.Column(db.Text, nullable=False)
    OverallRisk = db.Column(db.Text, nullable=False)
    Created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=True)
    Updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=True)
class ThreatAgentReplyCategory(db.Model):
    __tablename__ = 'ThreatAgentReplyCategory'

    Id = db.Column(db.Integer, primary_key=True, nullable=False)
    Reply_id = db.Column(db.Integer, ForeignKey("ThreatAgentReply.Id", ondelete='CASCADE'))
    Category_id = db.Column(db.Integer, ForeignKey("ThreatAgentCategory.Id", ondelete='CASCADE'))


