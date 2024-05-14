"""init

Revision ID: 526a46b1dae8
Revises: 
Create Date: 2024-05-14 22:19:49.017258

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '526a46b1dae8'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('flight',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('flight_number', sa.String(length=100), nullable=False),
    sa.Column('departure_from', sa.String(length=100), nullable=True),
    sa.Column('arrival_time', sa.String(length=100), nullable=True),
    sa.Column('arrival_date', sa.String(length=100), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('user',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('username', sa.String(length=80), nullable=False),
    sa.Column('password_hash', sa.String(length=512), nullable=False),
    sa.Column('email', sa.String(length=120), nullable=True),
    sa.Column('mobile', sa.String(length=120), nullable=True),
    sa.Column('profile_picture', sa.String(length=120), nullable=True),
    sa.Column('bio', sa.Text(), nullable=True),
    sa.Column('last_seen', sa.DateTime(), nullable=True),
    sa.Column('is_admin', sa.Boolean(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_user_email'), ['email'], unique=True)
        batch_op.create_index(batch_op.f('ix_user_username'), ['username'], unique=True)

    op.create_table('activity',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('event', sa.String(length=100), nullable=True),
    sa.Column('description', sa.String(length=255), nullable=True),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.Column('checked_in', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('guest',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('booking', sa.String(length=100), nullable=False),
    sa.Column('first_name', sa.String(length=100), nullable=False),
    sa.Column('last_name', sa.String(length=100), nullable=False),
    sa.Column('flight_id', sa.Integer(), nullable=True),
    sa.Column('departure_from', sa.String(length=100), nullable=True),
    sa.Column('arriving_date', sa.String(length=100), nullable=True),
    sa.Column('arrival_time', sa.String(length=100), nullable=True),
    sa.Column('transportation', sa.String(length=100), nullable=True),
    sa.Column('status', sa.String(length=100), nullable=True),
    sa.Column('checked_time', sa.DateTime(), nullable=True),
    sa.Column('checked_by', sa.Integer(), nullable=True),
    sa.Column('comments', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['checked_by'], ['user.id'], ),
    sa.ForeignKeyConstraint(['flight_id'], ['flight.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('message',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('sender_id', sa.Integer(), nullable=True),
    sa.Column('receiver_id', sa.Integer(), nullable=True),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.Column('read', sa.Boolean(), nullable=False),
    sa.ForeignKeyConstraint(['receiver_id'], ['user.id'], ),
    sa.ForeignKeyConstraint(['sender_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('message', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_message_timestamp'), ['timestamp'], unique=False)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('message', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_message_timestamp'))

    op.drop_table('message')
    op.drop_table('guest')
    op.drop_table('activity')
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_user_username'))
        batch_op.drop_index(batch_op.f('ix_user_email'))

    op.drop_table('user')
    op.drop_table('flight')
    # ### end Alembic commands ###
