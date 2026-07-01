from sqlalchemy import Column, Integer, String, Float, Text, TIMESTAMP, ForeignKey, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Disease(Base):
    __tablename__ = "diseases"

    id = Column(Integer, primary_key=True, index=True)
    disease_name = Column(String(255), nullable=False, index=True)
    disease_id = Column(String(100), unique=True)
    description = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    disease_target_associations = relationship("DiseaseTargetAssociation", back_populates="disease")
    evidence_records = relationship("EvidenceRecord", back_populates="disease")
    expression_data = relationship("ExpressionData", back_populates="disease")


class Target(Base):
    __tablename__ = "targets"

    id = Column(Integer, primary_key=True, index=True)
    target_id = Column(String(100), unique=True, nullable=False, index=True)
    gene_symbol = Column(String(50), index=True)
    protein_name = Column(String(255))
    uniprot_id = Column(String(50))
    pathways = Column(ARRAY(Text))
    functions = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now())

    disease_target_associations = relationship("DiseaseTargetAssociation", back_populates="target")
    drug_target_interactions = relationship("DrugTargetInteraction", back_populates="target")
    evidence_records = relationship("EvidenceRecord", back_populates="target")
    string_interactions = relationship("StringInteraction", back_populates="target")
    expression_data = relationship("ExpressionData", back_populates="target")
    reactome_pathways = relationship("ReactomePathway", back_populates="target")


class Drug(Base):
    __tablename__ = "drugs"

    id = Column(Integer, primary_key=True, index=True)
    chembl_id = Column(String(50), unique=True, nullable=False, index=True)
    drug_name = Column(String(255), nullable=False, index=True)
    max_phase = Column(Integer, index=True)
    molecule_type = Column(String(100))
    mechanism_of_action = Column(Text)
    indications = Column(ARRAY(Text))
    created_at = Column(TIMESTAMP, server_default=func.now())

    drug_target_interactions = relationship("DrugTargetInteraction", back_populates="drug")
    evidence_records = relationship("EvidenceRecord", back_populates="drug")


class DiseaseTargetAssociation(Base):
    __tablename__ = "disease_target_associations"

    id = Column(Integer, primary_key=True, index=True)
    disease_id = Column(Integer, ForeignKey("diseases.id", ondelete="CASCADE"), nullable=False, index=True)
    target_id = Column(Integer, ForeignKey("targets.id", ondelete="CASCADE"), nullable=False, index=True)
    association_score = Column(Float)
    data_sources = Column(ARRAY(Text))
    created_at = Column(TIMESTAMP, server_default=func.now())

    disease = relationship("Disease", back_populates="disease_target_associations")
    target = relationship("Target", back_populates="disease_target_associations")


class DrugTargetInteraction(Base):
    __tablename__ = "drug_target_interactions"

    id = Column(Integer, primary_key=True, index=True)
    drug_id = Column(Integer, ForeignKey("drugs.id", ondelete="CASCADE"), nullable=False, index=True)
    target_id = Column(Integer, ForeignKey("targets.id", ondelete="CASCADE"), nullable=False, index=True)
    interaction_type = Column(String(100))
    activity_value = Column(Float)
    activity_units = Column(String(50))
    created_at = Column(TIMESTAMP, server_default=func.now())

    drug = relationship("Drug", back_populates="drug_target_interactions")
    target = relationship("Target", back_populates="drug_target_interactions")


class EvidenceRecord(Base):
    __tablename__ = "evidence_records"

    id = Column(Integer, primary_key=True, index=True)
    disease_id = Column(Integer, ForeignKey("diseases.id", ondelete="CASCADE"), nullable=False, index=True)
    drug_id = Column(Integer, ForeignKey("drugs.id", ondelete="CASCADE"), nullable=False, index=True)
    target_id = Column(Integer, ForeignKey("targets.id", ondelete="CASCADE"), nullable=False, index=True)

    # Score components 
    open_targets_score = Column(Float)
    chembl_score = Column(Float)
    uniprot_score = Column(Float)
    omim_score = Column(Float)
    string_score = Column(Float, nullable=True)
    expression_score = Column(Float, nullable=True)
    reactome_score = Column(Float, nullable=True)

    total_score = Column(Float, index=True)

    # Metadata
    confidence_level = Column(String(20))
    data_completeness = Column(Float)

    search_timestamp = Column(TIMESTAMP, server_default=func.now(), index=True)

    disease = relationship("Disease", back_populates="evidence_records")
    drug = relationship("Drug", back_populates="evidence_records")
    target = relationship("Target", back_populates="evidence_records")


class OMIMAssociation(Base):
    __tablename__ = "omim_associations"

    id = Column(Integer, primary_key=True, index=True)
    omim_id = Column(String(50), nullable=False, index=True)
    gene_symbol = Column(String(50), nullable=False, index=True)
    disease_name = Column(String(255))
    phenotype_description = Column(Text)
    inheritance_pattern = Column(String(100))
    created_at = Column(TIMESTAMP, server_default=func.now())


class StringInteraction(Base):
    """STRING protein-protein interaction data."""
    __tablename__ = "string_interactions"

    id = Column(Integer, primary_key=True, index=True)
    target_id = Column(Integer, ForeignKey("targets.id", ondelete="CASCADE"), nullable=False, index=True)
    interactor_gene = Column(String(50), nullable=False)
    combined_score = Column(Float)
    network_distance = Column(Integer)
    created_at = Column(TIMESTAMP, server_default=func.now())

    target = relationship("Target", back_populates="string_interactions")


class ExpressionData(Base):
    """Differential gene expression data from Expression Atlas."""
    __tablename__ = "expression_data"

    id = Column(Integer, primary_key=True, index=True)
    target_id = Column(Integer, ForeignKey("targets.id", ondelete="CASCADE"), nullable=False, index=True)
    disease_id = Column(Integer, ForeignKey("diseases.id", ondelete="CASCADE"), nullable=False, index=True)
    fold_change = Column(Float)
    p_value = Column(Float)
    expression_level = Column(String(20))  # 'up', 'down', 'unchanged'
    tissue_type = Column(String(100))
    created_at = Column(TIMESTAMP, server_default=func.now())

    target = relationship("Target", back_populates="expression_data")
    disease = relationship("Disease", back_populates="expression_data")


class ReactomePathway(Base):
    """Reactome pathway membership data."""
    __tablename__ = "reactome_pathways"

    id = Column(Integer, primary_key=True, index=True)
    target_id = Column(Integer, ForeignKey("targets.id", ondelete="CASCADE"), nullable=False, index=True)
    pathway_id = Column(String(50), nullable=False)
    pathway_name = Column(String(255))
    pathway_category = Column(String(100))
    created_at = Column(TIMESTAMP, server_default=func.now())

    target = relationship("Target", back_populates="reactome_pathways")
