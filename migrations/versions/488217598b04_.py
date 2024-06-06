"""empty message

Revision ID: 488217598b04
Revises: 0cf76049f35b
Create Date: 2024-06-06 00:34:59.074252

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '488217598b04'
down_revision = '0cf76049f35b'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('guest', schema=None) as batch_op:
        batch_op.add_column(sa.Column('cabin', sa.String(length=100), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('guest', schema=None) as batch_op:
        batch_op.drop_column('cabin')

    # ### end Alembic commands ###
