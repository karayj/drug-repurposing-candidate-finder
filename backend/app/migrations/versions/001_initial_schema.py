"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-05-16 03:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create diseases table
    op.create_table('diseases',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('disease_name', sa.String(length=255), nullable=False),
    sa.Column('disease_id', sa.String(length=100), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('disease_id')
    )
    op.create_index(op.f('ix_diseases_disease_name'), 'diseases', ['disease_name'], unique=False)
    op.create_index(op.f('ix_diseases_id'), 'diseases', ['id'], unique=False)

    # Create targets table
    op.create_table('targets',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('target_id', sa.String(length=100), nullable=False),
    sa.Column('gene_symbol', sa.String(length=50), nullable=True),
    sa.Column('protein_name', sa.String(length=255), nullable=True),
    sa.Column('uniprot_id', sa.String(length=50), nullable=True),
    sa.Column('pathways', postgresql.ARRAY(sa.Text()), nullable=True),
    sa.Column('functions', sa.Text(), nullable=True),
    sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('target_id')
    )
    op.create_index(op.f('ix_targets_gene_symbol'), 'targets', ['gene_symbol'], unique=False)
    op.create_index(op.f('ix_targets_id'), 'targets', ['id'], unique=False)
    op.create_index(op.f('ix_targets_target_id'), 'targets', ['target_id'], unique=False)

    # Create drugs table
    op.create_table('drugs',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('chembl_id', sa.String(length=50), nullable=False),
    sa.Column('drug_name', sa.String(length=255), nullable=False),
    sa.Column('max_phase', sa.Integer(), nullable=True),
    sa.Column('molecule_type', sa.String(length=100), nullable=True),
    sa.Column('mechanism_of_action', sa.Text(), nullable=True),
    sa.Column('indications', postgresql.ARRAY(sa.Text()), nullable=True),
    sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('chembl_id')
    )
    op.create_index(op.f('ix_drugs_chembl_id'), 'drugs', ['chembl_id'], unique=False)
    op.create_index(op.f('ix_drugs_drug_name'), 'drugs', ['drug_name'], unique=False)
    op.create_index(op.f('ix_drugs_id'), 'drugs', ['id'], unique=False)
    op.create_index(op.f('ix_drugs_max_phase'), 'drugs', ['max_phase'], unique=False)

    # Create disease_target_associations table
    op.create_table('disease_target_associations',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('disease_id', sa.Integer(), nullable=False),
    sa.Column('target_id', sa.Integer(), nullable=False),
    sa.Column('association_score', sa.Float(), nullable=True),
    sa.Column('data_sources', postgresql.ARRAY(sa.Text()), nullable=True),
    sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['disease_id'], ['diseases.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['target_id'], ['targets.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_disease_target_associations_disease_id'), 'disease_target_associations', ['disease_id'], unique=False)
    op.create_index(op.f('ix_disease_target_associations_id'), 'disease_target_associations', ['id'], unique=False)
    op.create_index(op.f('ix_disease_target_associations_target_id'), 'disease_target_associations', ['target_id'], unique=False)

    # Create drug_target_interactions table
    op.create_table('drug_target_interactions',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('drug_id', sa.Integer(), nullable=False),
    sa.Column('target_id', sa.Integer(), nullable=False),
    sa.Column('interaction_type', sa.String(length=100), nullable=True),
    sa.Column('activity_value', sa.Float(), nullable=True),
    sa.Column('activity_units', sa.String(length=50), nullable=True),
    sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['drug_id'], ['drugs.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['target_id'], ['targets.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_drug_target_interactions_drug_id'), 'drug_target_interactions', ['drug_id'], unique=False)
    op.create_index(op.f('ix_drug_target_interactions_id'), 'drug_target_interactions', ['id'], unique=False)
    op.create_index(op.f('ix_drug_target_interactions_target_id'), 'drug_target_interactions', ['target_id'], unique=False)

    # Create evidence_records table
    op.create_table('evidence_records',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('disease_id', sa.Integer(), nullable=False),
    sa.Column('drug_id', sa.Integer(), nullable=False),
    sa.Column('target_id', sa.Integer(), nullable=False),
    sa.Column('open_targets_score', sa.Float(), nullable=True),
    sa.Column('chembl_score', sa.Float(), nullable=True),
    sa.Column('uniprot_score', sa.Float(), nullable=True),
    sa.Column('omim_score', sa.Float(), nullable=True),
    sa.Column('total_score', sa.Float(), nullable=True),
    sa.Column('confidence_level', sa.String(length=20), nullable=True),
    sa.Column('data_completeness', sa.Float(), nullable=True),
    sa.Column('search_timestamp', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['disease_id'], ['diseases.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['drug_id'], ['drugs.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['target_id'], ['targets.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_evidence_records_disease_id'), 'evidence_records', ['disease_id'], unique=False)
    op.create_index(op.f('ix_evidence_records_drug_id'), 'evidence_records', ['drug_id'], unique=False)
    op.create_index(op.f('ix_evidence_records_id'), 'evidence_records', ['id'], unique=False)
    op.create_index(op.f('ix_evidence_records_search_timestamp'), 'evidence_records', ['search_timestamp'], unique=False)
    op.create_index(op.f('ix_evidence_records_total_score'), 'evidence_records', ['total_score'], unique=False)
    op.create_index(op.f('ix_evidence_records_target_id'), 'evidence_records', ['target_id'], unique=False)

    # Create omim_associations table
    op.create_table('omim_associations',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('omim_id', sa.String(length=50), nullable=False),
    sa.Column('gene_symbol', sa.String(length=50), nullable=False),
    sa.Column('disease_name', sa.String(length=255), nullable=True),
    sa.Column('phenotype_description', sa.Text(), nullable=True),
    sa.Column('inheritance_pattern', sa.String(length=100), nullable=True),
    sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_omim_associations_gene_symbol'), 'omim_associations', ['gene_symbol'], unique=False)
    op.create_index(op.f('ix_omim_associations_id'), 'omim_associations', ['id'], unique=False)
    op.create_index(op.f('ix_omim_associations_omim_id'), 'omim_associations', ['omim_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_omim_associations_omim_id'), table_name='omim_associations')
    op.drop_index(op.f('ix_omim_associations_id'), table_name='omim_associations')
    op.drop_index(op.f('ix_omim_associations_gene_symbol'), table_name='omim_associations')
    op.drop_table('omim_associations')
    op.drop_index(op.f('ix_evidence_records_target_id'), table_name='evidence_records')
    op.drop_index(op.f('ix_evidence_records_total_score'), table_name='evidence_records')
    op.drop_index(op.f('ix_evidence_records_search_timestamp'), table_name='evidence_records')
    op.drop_index(op.f('ix_evidence_records_id'), table_name='evidence_records')
    op.drop_index(op.f('ix_evidence_records_drug_id'), table_name='evidence_records')
    op.drop_index(op.f('ix_evidence_records_disease_id'), table_name='evidence_records')
    op.drop_table('evidence_records')
    op.drop_index(op.f('ix_drug_target_interactions_target_id'), table_name='drug_target_interactions')
    op.drop_index(op.f('ix_drug_target_interactions_id'), table_name='drug_target_interactions')
    op.drop_index(op.f('ix_drug_target_interactions_drug_id'), table_name='drug_target_interactions')
    op.drop_table('drug_target_interactions')
    op.drop_index(op.f('ix_disease_target_associations_target_id'), table_name='disease_target_associations')
    op.drop_index(op.f('ix_disease_target_associations_id'), table_name='disease_target_associations')
    op.drop_index(op.f('ix_disease_target_associations_disease_id'), table_name='disease_target_associations')
    op.drop_table('disease_target_associations')
    op.drop_index(op.f('ix_drugs_max_phase'), table_name='drugs')
    op.drop_index(op.f('ix_drugs_id'), table_name='drugs')
    op.drop_index(op.f('ix_drugs_drug_name'), table_name='drugs')
    op.drop_index(op.f('ix_drugs_chembl_id'), table_name='drugs')
    op.drop_table('drugs')
    op.drop_index(op.f('ix_targets_target_id'), table_name='targets')
    op.drop_index(op.f('ix_targets_id'), table_name='targets')
    op.drop_index(op.f('ix_targets_gene_symbol'), table_name='targets')
    op.drop_table('targets')
    op.drop_index(op.f('ix_diseases_id'), table_name='diseases')
    op.drop_index(op.f('ix_diseases_disease_name'), table_name='diseases')
    op.drop_table('diseases')
