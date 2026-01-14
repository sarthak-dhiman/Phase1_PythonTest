"""create ingests and logs tables

Revision ID: 0001_create_ingests_logs
Revises: 
Create Date: 2026-01-14 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
import sqlalchemy.dialects.postgresql as pg

# revision identifiers, used by Alembic.
revision = '0001_create_ingests_logs'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create ingests table
    op.create_table(
        'ingests',
        sa.Column('id', pg.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('file_hash', sa.String(length=128), nullable=False),
        sa.Column('file_name', sa.String(length=255), nullable=True),
        sa.Column('status', sa.String(length=32), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('total_rows', sa.Integer(), nullable=True),
        sa.Column('inserted_rows', sa.Integer(), nullable=True),
    )
    op.create_index(op.f('ix_ingests_file_hash'), 'ingests', ['file_hash'], unique=True)

    # Create logs table
    op.create_table(
        'logs',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('ingest_id', pg.UUID(as_uuid=True), sa.ForeignKey('ingests.id'), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
        sa.Column('module', sa.String(length=128), nullable=True),
        sa.Column('level', sa.String(length=32), nullable=True),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('row_hash', sa.String(length=128), nullable=False),
    )
    op.create_unique_constraint('uq_logs_row_hash', 'logs', ['row_hash'])
    op.create_index(op.f('ix_logs_ingest_id'), 'logs', ['ingest_id'], unique=False)
    op.create_index(op.f('ix_logs_timestamp'), 'logs', ['timestamp'], unique=False)
    op.create_index(op.f('ix_logs_module'), 'logs', ['module'], unique=False)
    op.create_index(op.f('ix_logs_level'), 'logs', ['level'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_logs_level'), table_name='logs')
    op.drop_index(op.f('ix_logs_module'), table_name='logs')
    op.drop_index(op.f('ix_logs_timestamp'), table_name='logs')
    op.drop_index(op.f('ix_logs_ingest_id'), table_name='logs')
    op.drop_constraint('uq_logs_row_hash', 'logs', type_='unique')
    op.drop_table('logs')

    op.drop_index(op.f('ix_ingests_file_hash'), table_name='ingests')
    op.drop_table('ingests')
