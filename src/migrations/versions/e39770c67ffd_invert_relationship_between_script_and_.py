"""Invert relationship between script and version

Revision ID: e39770c67ffd
Revises: f68ba083a980
Create Date: 2023-03-05 12:19:37.482899

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e39770c67ffd'
down_revision = 'f68ba083a980'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('mirc_scripts_version_id_fkey', 'mirc_scripts', type_='foreignkey')
    op.drop_column('mirc_scripts', 'version_id')
    op.add_column('script_versions', sa.Column('script_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'script_versions', 'mirc_scripts', ['script_id'], ['id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'script_versions', type_='foreignkey')
    op.drop_column('script_versions', 'script_id')
    op.add_column('mirc_scripts', sa.Column('version_id', sa.INTEGER(), autoincrement=False, nullable=True))
    op.create_foreign_key('mirc_scripts_version_id_fkey', 'mirc_scripts', 'script_versions', ['version_id'], ['id'])
    # ### end Alembic commands ###
