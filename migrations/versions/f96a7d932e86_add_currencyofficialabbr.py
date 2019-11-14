"""Add CurrencyOfficialAbbr

Revision ID: f96a7d932e86
Revises: 42b0e70c96e8
Create Date: 2019-11-10 10:45:29.878583

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f96a7d932e86'
down_revision = '42b0e70c96e8'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('currency_official_abbr',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('abbr', sa.String(length=10), nullable=True),
    sa.Column('name', sa.String(length=64), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('abbr')
    )
    op.create_foreign_key(None, 'currency', 'currency_official_abbr', ['abbr'], ['abbr'])
    op.create_foreign_key(None, 'user', 'currency', ['currency_default_choice'], ['id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'user', type_='foreignkey')
    op.drop_constraint(None, 'currency', type_='foreignkey')
    op.drop_table('currency_official_abbr')
    # ### end Alembic commands ###
