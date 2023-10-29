# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""


from typing import List
from sqlalchemy.orm import relationship, Mapped
from sqlalchemy.sql.expression import case
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import ForeignKey, select, orm, func, and_
from sqlalchemy.dialects import mysql
from sqlalchemy_utils import create_view
from .types import ExternalReferencesType

from apps import db

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
    External_References     = db.Column(ExternalReferencesType)
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
    Capec_Childs_ID         = db.Column(db.JSON)
    Capec_Parents_ID        = db.Column(db.JSON)

    def __init__(self, **kwargs):
        for property, value in kwargs.items():
            # depending on whether value is an iterable or not, we must
            # unpack it's value (when **kwargs is request.form, some values
            # will be a 1-element list)
            if hasattr(value, '__iter__') and not isinstance(value, str):
                # the ,= unpack of a singleton fails PEP8 (travis flake8 test)
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

    TID                 = db.Column(db.Text, primary_key=True, unique=True, nullable=False)
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

    hasCapec    = db.relationship('Capec', secondary='CapecToolRel', backref='hasTool', lazy='dynamic')

    @hybrid_property
    def hasCapecIDs(self):
        ids = self.hasCapec.with_entities(Capec.Capec_ID).all()
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

    Component_ID    = db.Column(db.Integer, primary_key=True, unique=True, nullable=False)
    Application     = db.Column(db.Text)
    Name            = db.Column(db.Text)
    Type            = db.Column(db.Text)
    App_ID          = db.Column(db.Integer)
    Parameters      = db.Column(db.JSON)
    
    def __init__(self, **kwargs):
        for property, value in kwargs.items():
            if hasattr(value, '__iter__') and not isinstance(value, str):
                value = value[0]

            setattr(self, property, value)

    def __repr__(self):
        return str(self.Name)
    
class ToolAssetTypeRel(db.Model):

    __tablename__ = 'ToolAssetTypeRel'

    Id           = db.Column(db.Integer, primary_key=True, unique=True, nullable=False)
    ToolID       = db.Column(db.Integer, ForeignKey("ToolCatalogue.ToolID"))
    ComponentID    = db.Column(db.Integer, ForeignKey("Macm.Component_ID"))

    def __init__(self, **kwargs):
        for property, value in kwargs.items():
            if hasattr(value, '__iter__') and not isinstance(value, str):
                value = value[0]

            setattr(self, property, value)

    def __repr__(self):
        return str(f'{self.ToolID}-{self.AssetType}')

class AttackView(db.Model):
    row_number_column = func.row_number().over(order_by=Macm.Component_ID).label('Attack_Number')
    
    __table__ = create_view(
                "AttackView",
                select(
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
                    Macm.Parameters
                )
                .select_from(Macm)
                .join(ThreatCatalogue, Macm.Type==ThreatCatalogue.Asset)
                .join(CapecThreatRel)
                .join(Capec)
                .join(CapecToolRel)
                .join(ToolCatalogue)
                .join(ToolAssetTypeRel, and_(Macm.Component_ID==ToolAssetTypeRel.ComponentID, ToolAssetTypeRel.ToolID==ToolCatalogue.ToolID))
                .add_columns(row_number_column),
                db.metadata,
                replace=True
                )
    
    def __repr__(self):
        return str(f'{self.Component_ID}-{self.Capec_ID}')