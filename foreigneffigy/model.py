import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


class Contract(Base):
    __tablename__ = 'contract'

    id = sa.Column(sa.Integer(), primary_key=True)

    energy_usage = relationship(
        'EnergyUsage',
        backref='contract',
        uselist=False
    )


class EnergyUsage(Base):
    __tablename__ = 'energy_usage'
    __table_args__ = (
        sa.UniqueConstraint(
            'date',
            'contract_id',
            name='date_contract_unique'
        ),
    )

    id = sa.Column(sa.Integer(), primary_key=True)
    date = sa.Column(sa.DateTime())
    concession_consumption = sa.Column(sa.String(32))
    concession_cost = sa.Column(sa.String(32))
    consumption = sa.Column(sa.Numeric(precision=3, scale=2), default='0.00')
    consumption_uom = sa.Column(sa.String(32))
    cost = sa.Column(sa.Numeric(precision=3, scale=2), default='0.00')
    energy_consumption = sa.Column(
        sa.Numeric(precision=3, scale=2), default='0.00'
    )
    energy_service_consumption = sa.Column(sa.String(32))
    energy_cost = sa.Column(sa.Numeric(precision=3, scale=2), default='0.00')
    energy_service_cost = sa.Column(
        sa.Numeric(precision=3, scale=2), default='0.00'
    )
    feedin_consumption = sa.Column(sa.String(32))
    feedin_consumption_uom = sa.Column(sa.String(32))
    feedin_cost = sa.Column(sa.String(32))
    solar_present = sa.Column(sa.Boolean)
    value_pot = sa.Column(sa.Numeric(precision=3, scale=2), default='0.00')
    contract_id = sa.Column(sa.Integer, sa.ForeignKey('contract.id'))
