"""empty message

Revision ID: e198b69ffede
Revises: f96a7d932e86
Create Date: 2019-11-10 19:29:37.054770

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e198b69ffede'
down_revision = 'f96a7d932e86'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_foreign_key(None, 'currency', 'currency_official_abbr', ['abbr'], ['abbr'])
    op.create_foreign_key(None, 'user', 'currency', ['currency_default_choice'], ['id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'user', type_='foreignkey')
    op.drop_constraint(None, 'currency', type_='foreignkey')
    # ### end Alembic commands ###
