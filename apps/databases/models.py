# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""


from typing import List
from sqlalchemy.orm import relationship, Mapped
from sqlalchemy.sql.expression import case
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import ForeignKey

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
        return str(self.Name) 

    @hybrid_property
    def abstraction_order(self):
        table_ordering = case(
                whens={"Meta":1, "Standard":2, "Detailed": 3},
                value=Capec.Abstraction
        )
        return (table_ordering)
    
class ThreatCatalog(db.Model):

    __tablename__ = 'ThreatCatalog'

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
    CapecMeta           = db.Column(db.JSON)
    CapecStandard       = db.Column(db.JSON)
    CapecDetailed       = db.Column(db.JSON)
    Commento            = db.Column(db.Text)
    
    CapecMetaRel: Mapped[List[Capec]] = relationship("Capec", secondary="AssociationTable", backref="ThreatCatalog")


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
        return str(self.Asset)
    
class Association(db.Model):

    __tablename__ = 'AssociationTable'

    Capec_ID                  = db.Column(db.Integer, ForeignKey("Capec.Capec_ID"), primary_key=True, unique=True, nullable=False)
    ThreatCatalog_ID          = db.Column(db.Text, ForeignKey("ThreatCatalog.TID"), primary_key=True, unique=True, nullable=False)
class Macm(db.Model):

    __tablename__ = 'Macm'

    Component_ID    = db.Column(db.Integer, primary_key=True)
    Application     = db.Column(db.Text)
    Name            = db.Column(db.Text)
    Type            = db.Column(db.Text)
    App_ID          = db.Column(db.Integer)
    

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
        return str(self.Name)
    
