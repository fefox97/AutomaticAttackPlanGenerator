# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""


from typing import List
from sqlalchemy.orm import relationship, Mapped
from sqlalchemy.sql.expression import case
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import ForeignKey, select, orm, func, and_, UniqueConstraint
from sqlalchemy.dialects import mysql
from sqlalchemy_utils import create_view
from .types import ExternalReferencesType

from apps import db
from sqlalchemy import UniqueConstraint

class PentestPhases(db.Model):

    __tablename__ = 'PentestPhases'

    PhaseID                = db.Column(db.Integer, primary_key=True, unique=True, nullable=False)
    PhaseName              = db.Column(db.Text)
    IsSubPhaseOf           = db.Column(db.Integer)

    def __init__(self, **kwargs):
        for property, value in kwargs.items():
            if hasattr(value, '__iter__') and not isinstance(value, str):
                value = value[0]

            setattr(self, property, value)

    def __repr__(self):
        return str(self.PhaseID)

class Capec(db.Model):

    __tablename__ = 'Capec'

    Capec_ID                = db.Column(db.Integer, primary_key=True, unique=True, nullable=False)
    Created                 = db.Column(db.TIMESTAMP)
    Created_By_Ref          = db.Column(db.JSON)
    Description             = db.Column(db.Text)
    Modified                = db.Column(db.TIMESTAMP)
    Name                    = db.Column(db.Text)
    Object_Marking_Refs     = db.Column(db.JSON)
    Spec_Version            = db.Column(db.Text)
    Abstraction             = db.Column(db.Text)
    Alternate_Terms         = db.Column(db.JSON)
    Can_Follow_Refs         = db.Column(db.JSON)
    Can_Precede_Refs        = db.Column(db.JSON)
    Consequences            = db.Column(db.JSON)
    Domains                 = db.Column(db.JSON)
    External_References     = db.Column(ExternalReferencesType(2000))
    Example_Instances       = db.Column(db.JSON)
    Execution_Flow          = db.Column(db.Text)
    Extended_Description    = db.Column(db.JSON)
    Likelihood_Of_Attack    = db.Column(db.Text)
    Peer_Of_Refs            = db.Column(db.JSON)
    Prerequisites           = db.Column(db.JSON)
    Resources_Required      = db.Column(db.JSON)
    Skills_Required         = db.Column(db.JSON)
    Status                  = db.Column(db.Text)
    Typical_Severity        = db.Column(db.Text)
    Version                 = db.Column(db.Text)
    Capec_Children_ID       = db.Column(db.JSON)
    Capec_Parents_ID        = db.Column(db.JSON)

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
                whens={"Meta":1, "Standard":2, "Detailed": 3},
                value=Capec.Abstraction
        )
        return (table_ordering)
    
class ThreatCatalogue(db.Model):

    __tablename__ = 'ThreatCatalogue'

    TID                 = db.Column(db.Text(10), primary_key=True, unique=True, nullable=False)
    Asset               = db.Column(db.Text)
    Threat              = db.Column(db.Text)
    Description         = db.Column(db.Text)
    STRIDE              = db.Column(db.Text)
    Compromised         = db.Column(db.Text)
    PreC                = db.Column(db.JSON)
    PreI                = db.Column(db.JSON)
    PreA                = db.Column(db.JSON)
    Precondition        = db.Column(db.JSON)
    PostC               = db.Column(db.JSON)
    PostI               = db.Column(db.JSON)
    PostA               = db.Column(db.JSON)
    PostCondition       = db.Column(db.JSON)
    # CapecMeta           = db.Column(db.JSON)
    # CapecStandard       = db.Column(db.JSON)
    # CapecDetailed       = db.Column(db.JSON)
    Commento            = db.Column(db.Text)
    
    hasCapec            = db.relationship('Capec', secondary='CapecThreatRel', backref='hasThreat', lazy='dynamic')
    
    @hybrid_property
    def hasCapecMeta(self):
        ids = self.hasCapec.filter(Capec.Abstraction == 'Meta').with_entities(Capec.Capec_ID).all()
        return [id[0] for id in ids]
    
    @hybrid_property
    def hasCapecStandard(self):
        ids = self.hasCapec.filter(Capec.Abstraction == 'Standard').with_entities(Capec.Capec_ID).all()
        return [id[0] for id in ids]
    
    @hybrid_property
    def hasCapecDetailed(self):
        ids = self.hasCapec.filter(Capec.Abstraction == 'Detailed').with_entities(Capec.Capec_ID).all()
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

    Id           = db.Column(db.Integer, primary_key=True, unique=True, nullable=False)
    Capec_ID     = db.Column(db.Integer, ForeignKey("Capec.Capec_ID"))
    TID          = db.Column(db.Text, ForeignKey("ThreatCatalogue.TID"))

class ToolCatalogue(db.Model):

    __tablename__ = 'ToolCatalogue'

    ToolID      = db.Column(db.Integer, primary_key=True, unique=True, nullable=False)
    Name        = db.Column(db.Text)
    CapecID     = db.Column(db.JSON)
    CypherQuery = db.Column(db.Text)
    Command     = db.Column(db.Text)
    Description = db.Column(db.Text)
    PhaseID     = db.Column(db.JSON)
    IsExecutable = db.Column(db.Boolean)
    OutputParser = db.Column(db.Text)
    AllowedOutputExtensions = db.Column(db.JSON)
    
    hasPhase       = db.relationship("PentestPhases", secondary='ToolPhaseRel', backref='hasTool', lazy='dynamic')
    hasCapec    = db.relationship('Capec', secondary='CapecToolRel', backref='hasTool', lazy='dynamic')

    @hybrid_property
    def hasCapecIDs(self):
        ids = self.hasCapec.with_entities(Capec.Capec_ID).all()
        return [id[0] for id in ids]
    
    @hybrid_property
    def hasPhaseIDs(self):
        ids = self.hasPhase.with_entities(PentestPhases.PhaseID).all()
        return [id[0] for id in ids]

    def __init__(self, **kwargs):
        for property, value in kwargs.items():
            if hasattr(value, '__iter__') and not isinstance(value, str):
                value = value[0]

            setattr(self, property, value)

    def __repr__(self):
        return str(self.ToolID)

class CapecToolRel(db.Model):

    __tablename__ = 'CapecToolRel'

    Id           = db.Column(db.Integer, primary_key=True, unique=True, nullable=False)
    Capec_ID     = db.Column(db.Integer, ForeignKey("Capec.Capec_ID"))
    ToolID       = db.Column(db.Text, ForeignKey("ToolCatalogue.ToolID"))

class Macm(db.Model):

    __tablename__ = 'Macm'

    Component_ID    = db.Column(db.Integer, primary_key=True, nullable=False)
    Application     = db.Column(db.Text)
    Name            = db.Column(db.Text)
    Type            = db.Column(db.Text)
    App_ID          = db.Column(db.Text, primary_key=True, nullable=False)
    Labels          = db.Column(db.JSON)
    Parameters      = db.Column(db.JSON)

    def __init__(self, **kwargs):
        for property, value in kwargs.items():
            if hasattr(value, '__iter__') and not isinstance(value, str):
                value = value[0]

            setattr(self, property, value)

    def __repr__(self):
        return str(self.Name)
    

class MacmUser(db.Model):

    __tablename__ = 'MacmUser'

    UserID         = db.Column(db.Integer, ForeignKey("Users.id"), primary_key=True, nullable=False)
    AppID          = db.Column(db.Text, ForeignKey("Macm.App_ID"), primary_key=True, nullable=False)
    AppName        = db.Column(db.Text)

    def __init__(self, **kwargs):
        for property, value in kwargs.items():
            if hasattr(value, '__iter__') and not isinstance(value, str):
                value = value[0]

            setattr(self, property, value)

    def __repr__(self):
        return str(self.UserID)
    
class ToolAssetRel(db.Model):

    __tablename__ = 'ToolAssetRel'

    Id           = db.Column(db.Integer, primary_key=True, unique=True, nullable=False)
    ToolID       = db.Column(db.Integer, ForeignKey("ToolCatalogue.ToolID"))
    ComponentID  = db.Column(db.Integer, ForeignKey("Macm.Component_ID"))
    AppID        = db.Column(db.Integer, ForeignKey("Macm.App_ID"))
    __table_args__ =  (UniqueConstraint('ToolID', 'ComponentID', 'AppID', name='uix_1'),)

    def __init__(self, **kwargs):
        for property, value in kwargs.items():
            if hasattr(value, '__iter__') and not isinstance(value, str):
                value = value[0]

            setattr(self, property, value)

    def __repr__(self):
        return str(f'{self.ToolID}-{self.AssetType}')
    
class ToolPhaseRel(db.Model):

    __tablename__ = 'ToolPhaseRel'

    Id           = db.Column(db.Integer, primary_key=True, unique=True, nullable=False)
    ToolID       = db.Column(db.Integer, ForeignKey("ToolCatalogue.ToolID"))
    PhaseID      = db.Column(db.Integer, ForeignKey("PentestPhases.PhaseID"))
    __table_args__ =  (UniqueConstraint('ToolID', 'PhaseID', name='uix_1'),)

    def __init__(self, **kwargs):
        for property, value in kwargs.items():
            if hasattr(value, '__iter__') and not isinstance(value, str):
                value = value[0]

            setattr(self, property, value)

    def __repr__(self):
        return str(f'{self.ToolID}-{self.PhaseID}')

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
                    ToolCatalogue.OutputParser.label("Output_Parser"),
                    ToolCatalogue.AllowedOutputExtensions.label("Allowed_Output_Extensions"),
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
                )
                .select_from(Macm)
                .join(ThreatCatalogue, Macm.Type==ThreatCatalogue.Asset)
                .join(CapecThreatRel)
                .join(Capec)
                .join(CapecToolRel)
                .join(ToolCatalogue)
                .join(ToolAssetRel, and_(Macm.Component_ID==ToolAssetRel.ComponentID, ToolAssetRel.ToolID==ToolCatalogue.ToolID, Macm.App_ID==ToolAssetRel.AppID))
                .join(ToolPhaseRel, ToolCatalogue.ToolID==ToolPhaseRel.ToolID)
                .join(PentestPhases, ToolPhaseRel.PhaseID==PentestPhases.PhaseID)
                .add_columns(row_number_column),
                db.metadata,
                replace=True
                )
    
    def __repr__(self):
        return str(f'{self.Component_ID}-{self.Capec_ID}')

class ThreatAgentReply(db.Model):

    __tablename__ = 'ThreatAgentReply'

    Id = db.Column(db.Integer, primary_key=True, unique=True, nullable=False)
    attribute = db.Column(db.Text)
    attribute_value = db.Column(db.Text)
    description = db.Column(db.Text,nullable=True)
    score = db.Column(db.Integer)

class ThreatAgentAttribute(db.Model):

    __tablename__ = 'ThreatAgentAttribute'

    Id = db.Column(db.Integer, primary_key=True, unique=True, nullable=False)
    attribute = db.Column(db.Text)
    attribute_value = db.Column(db.Text)
    description = db.Column(db.Text,nullable=True)
    score = db.Column(db.Integer)



class ThreatAgentCategory(db.Model):

    __tablename__ = 'ThreatAgentCategory'

    Id           = db.Column(db.Integer, primary_key=True, unique=True, nullable=False)
    Category       = db.Column(db.Text)
    Description       = db.Column(db.Text)
    CommonAction       = db.Column(db.Text)
    #Replies       = db.Column(db.Text)
    hasReply = db.relationship('Reply', secondary='CategoryThreatRel', backref='hasCategory', lazy='dynamic')

    @hybrid_property
    def hasReply(self):
        ids = self.hasReply.filter().with_entities(ThreatAgentReply.Id).all()
        return [id[0] for id in ids]
    Attributes       = db.Column(db.Text)

    @hybrid_property
    def hasAttribute(self):
        ids = self.hasAttribute.filter().with_entities(ThreatAgentAttribute.Id).all()
        return [id[0] for id in ids]


class ThreatAgentQuestion(db.Model):

    __tablename__ = 'ThreatAgentQuestion'

    Id           = db.Column(db.Integer, primary_key=True, unique=True, nullable=False)
    Question       = db.Column(db.Text)
    Qid       = db.Column(db.Text)
    #Replies       = db.Column(db.Text)
    hasReply = db.relationship('Reply', secondary='CategoryThreatRel', backref='hasCategory', lazy='dynamic')

    @hybrid_property
    def hasReply(self):
        ids = self.hasReply.filter().with_entities(ThreatAgentReply.Id).all()
        return [id[0] for id in ids]
    Attributes       = db.Column(db.Text)