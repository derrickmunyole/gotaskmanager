"""Added metadata columns to refresh_token table

Revision ID: 23e41057b11b
Revises: 694d4f7aaaf6
Create Date: 2024-08-01 02:30:51.405114

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '23e41057b11b'
down_revision = '694d4f7aaaf6'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('refresh_token', schema=None) as batch_op:
        batch_op.add_column(sa.Column('created_at', sa.DateTime(), nullable=False))
        batch_op.add_column(sa.Column('expires_at', sa.DateTime(), nullable=False))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('refresh_token', schema=None) as batch_op:
        batch_op.drop_column('expires_at')
        batch_op.drop_column('created_at')

    # ### end Alembic commands ###