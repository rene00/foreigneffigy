from datetime import datetime as dt
from fake_useragent import UserAgent
from model import sa, sessionmaker
from pprint import pprint
from sqlalchemy.orm.exc import NoResultFound
from validate import validate_date
import logging
import configparser
import datetime
import base64
import click
import model
import requests
import sys


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ForeignEffigyError(Exception):
    pass


class ForeignEffigy(requests.Session):

    def __init__(self, config, contract, db_session, debug=False):
        self.config = config
        self.contract = contract
        self.username = config[str(self.contract.id)]['username']
        self.password = config[str(self.contract.id)]['password']

        self.db_session = db_session
        self.session = requests.Session()
        self.session.headers = {'User-Agent': self.user_agent}
        self.debug = debug

    @property
    def daily_supply_charge(self):
        """ The daily supply charge.

        If daily_supply_charge exists within config, use it.
        """
        try:
            return float(
                self.config[str(self.contract.id)]
                ['daily_supply_charge']
            )
        except KeyError:
            return None

    def login(self):
        url = base64.urlsafe_b64decode(
            'aHR0cHM6Ly93d3cub3JpZ2luZW5lcmd5LmNvbS5hdS9iaW4vb3JpZ2luLXV'
            'pL2xvZ2lub3JpZ2lu'
        )
        refer = base64.urlsafe_b64decode(
            'aHR0cHM6Ly93d3cub3JpZ2luZW5lcmd5LmNvbS5hdS9sb2dpbi5odG1s'
        )
        payload = {'username': self.username, 'password': self.password}
        self.session.headers.update({'Referer': refer})
        resp = self.session.post(
            url,
            headers=self.session.headers,
            data=payload
        )
        if not resp.json()['success']:
            raise ForeignEffigyError('Failed to login.')

    @property
    def division_id(self):
        return int('01')

    @property
    def user_agent(self):
        try:
            return self.__user_agent
        except AttributeError:
            ua = UserAgent()
            return ua.msie

    @user_agent.setter
    def user_agent(self, user_agent):
        return self.__user_agent

    def energy_usage(self, start_date, end_date, aggregation_level='HOUR'):
        url = base64.urlsafe_b64decode(
            'aHR0cHM6Ly93d3cub3JpZ2luZW5lcmd5LmNvbS5hdS9iaW4vb3JpZ2luLXVp'
            'L2dldFVzYWdlR3JhcGg='
        )
        referer = base64.urlsafe_b64decode(
            'aHR0cHM6Ly93d3cub3JpZ2luZW5lcmd5LmNvbS5hdS9mb3ItaG9tZS9t'
            'eS1hY2NvdW50L3VzYWdlLmh0bWw='
        )
        params = {
            'contractId': self.contract.id,
            'divisionId': self.division_id,
            'startDate': dt.strftime(start_date, "%d/%m/%Y"),
            'endDate': dt.strftime(end_date, "%d/%m/%Y"),
            'aggregationLevel': aggregation_level
        }
        self.session.headers.update({'Referer': referer, 'Accept': '*/*'})
        resp = self.session.get(
            url, headers=self.session.headers, params=params
        )
        self.usage = resp.json()

    def _add_daily_supply_charge(self, usage):
        """Manually add supply charge to hourly usage.

        Provider stopped including supply charge with usage data so we
        have to manually add it in if it exists within the config.
        """
        if self.daily_supply_charge:
            usage['feedinCost'] = self.daily_supply_charge / 24
            usage['feedinConsumption'] = 1
            usage['feedinConsumptionUom'] = 'cents'
        return usage

    @property
    def account(self):
        """ Return account properties. """
        url = base64.urlsafe_b64decode(
            'aHR0cHM6Ly93d3cub3JpZ2luZW5lcmd5LmNvbS5hdS9iaW4vb3JpZ2luLX'
            'VpL2dldEFjY291bnRQcm9wZXJ0aWVz'
        )
        referer = base64.urlsafe_b64decode(
            'aHR0cHM6Ly93d3cub3JpZ2luZW5lcmd5LmNvbS5hdS9mb3ItaG9tZS9teS1'
            'hY2NvdW50L3VzYWdlLmh0bWw='
        )
        self.session.headers.update({'Referer': referer})
        resp = self.session.get(url, headers=self.session.headers)
        return resp.json()

    def update_db(self):
        data = self.usage.get(str(self.contract.id))
        for date, interval in data.items():
            for hourly, usage in interval.items():
                usage = self._add_daily_supply_charge(usage)
                logger.debug(usage)
                hour = dt.strptime(hourly, '%d %B, %Y %H:%M')
                energy_usage = model.EnergyUsage(
                    date=hour,
                    concession_consumption=usage['concessionConsumption'],
                    concession_cost=usage['concessionCost'],
                    consumption=usage['consumption'],
                    consumption_uom=usage['consumptionUom'],
                    cost=usage['cost'],
                    energy_consumption=usage['energyConsumption'],
                    energy_cost=usage['energyCost'],
                    energy_service_consumption=(
                        usage['energyServiceConsumption']
                    ),
                    energy_service_cost=usage['energyServiceCost'],
                    feedin_consumption=usage['feedinConsumption'],
                    feedin_consumption_uom=usage['feedinConsumptionUom'],
                    feedin_cost=usage['feedinCost'],
                    solar_present=usage['solarPresent'],
                    value_pot=usage['valuePOT'],
                    contract_id=self.contract.id
                )
                self.db_session.add(energy_usage)
                try:
                    self.db_session.commit()
                except sa.exc.IntegrityError as e:
                    # Most probably a duplicate. Rollback and move on.
                    self.db_session.rollback()


@click.command()
@click.option('--db-file', default='fe.db')
@click.option('--start-date', callback=validate_date)
@click.option('--end-date', callback=validate_date)
@click.option('--conf-file', required=True)
@click.option('--debug', is_flag=True, default=False)
def foreigneffigy(db_file, start_date, end_date, conf_file, debug):

    if debug:
        logger.setLevel(logging.DEBUG)

    config = configparser.ConfigParser()
    config.read(conf_file)

    engine = sa.create_engine('sqlite:///{0}'.format(db_file))
    model.Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    if start_date is None:
        start_date = datetime.datetime.now() - datetime.timedelta(days=7)

    if end_date is None:
        end_date = datetime.datetime.now()

    if end_date < start_date:
        raise click.BadParameter("End date must be greater than start date.")

    for section in config.sections():
        try:
            contract = (
                session.query(model.Contract).filter_by(id=section).one()
            )
        except sa.orm.exc.NoResultFound:
            contract = model.Contract(id=section)
            session.add(contract)
            session.commit()

        fe = ForeignEffigy(
            config,
            contract=contract,
            db_session=session,
            debug=debug
        )
        fe.login()
        # Display account properties if we're debugging.
        if debug:
            logger.debug(fe.account)
        fe.energy_usage(start_date, end_date)
        fe.update_db()


if __name__ == '__main__':
    foreigneffigy()
