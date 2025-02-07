"""Add job_number and contractor columns to projects

Revision ID: 21bfa265addc
Revises: 0b5bdb10bee4
Create Date: 2025-02-05 10:00:00
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '21bfa265addc'
down_revision = '0b5bdb10bee4'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('projects', sa.Column('job_number', sa.String(length=50), nullable=True))
    op.add_column('projects', sa.Column('contractor', sa.String(length=200), nullable=True))

def downgrade():
    op.drop_column('projects', 'contractor')
    op.drop_column('projects', 'job_number')
