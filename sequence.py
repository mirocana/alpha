from miscellaneous.utils import to_datetime, to_ch_datetime
from raven import Client as SentryClient
from collections import defaultdict
from datetime import datetime
import requests
import settings


class NoDataError(Exception):
    pass


class JoinMQBError(Exception):
    pass


class Context(object):

    def __init__(self, **kwargs):
        self.context = {**kwargs}

    def __getitem__(self, item):
        return self.context.get(item)

    def get(self, item, default=None):
        return self.context.get(item, default)

    def __setitem__(self, key, value):
        self.context[key] = value

    def __repr__(self):
        return str(sorted(self.context.items()))


class MQBSequence(object):

    MAX_LAST = 10e3

    def __init__(self, name, data, max_last=None):
        self.name = name
        self.data = data
        self.show = self.data
        self.offset = 0
        self.data_size = len(self.data)
        self.max_last = max_last or self.MAX_LAST

    def __len__(self):
        return self.data_size

    def __getitem__(self, item):
        if isinstance(item, int) and item <= 0:
            return self.show[-1]
        if isinstance(item, slice):
            return self.show[-item.start:-item.stop]
        try:
            return self.show[-int(item)-1]
        except IndexError:
            return None

    def _add_data(self, extra_data):
        self.data.extend(extra_data)
        self.data_size += len(extra_data)

    def _optimize(self, index):
        offset = max(int(index - self.max_last), 0)
        self.data = self.data[(offset-self.offset):]
        self.offset = offset

    def _set_show(self, index):
        self.show = self.data[:index-self.offset]

    def last(self, count):
        return self.show[-int(count):]

    def last_with_duration(self, count, duration=1):
        return self.show[-int(count*duration)::duration]

    def last_with_shift(self, count, shift=0):
        if shift != 0:
            return self.show[-int(count+shift):-shift]
        else:
            a = self.show[-int(count):]
            return self.show[-int(count):]


class BaseMQB(object):

    def __getitem__(self, item):
        if isinstance(item, int):
            return {x: self[x][item] for x in self.slugs}
        return getattr(self, item)

    def __setitem__(self, key, value):
        return setattr(self, key, value)

    def __iter__(self):
        return self

    def __next__(self):
        self.index += 1
        next_object = self.get(self.index)
        if not next_object:
            raise StopIteration
        return next_object

    def __repr__(self):
        return '{0} at {1}: {2}'.format(
            self.__class__.__name__,
            self[self.time_field][0],
            ', '.join(
                ['{0}: {1}'.format(k, self[k][0]) for k in sorted(self.slugs) if k != self.time_field]
            )
        )

    def __dict__(self):
        return {k: self[k][0] for k in self.slugs}

    def to_dict(self):
        return {k: self[k][0] for k in self.slugs}

    def get(self, index):
        if not self.data_size:
            return None
        if index >= self.data_size:
            data = self.load_data(to_datetime(self[self.time_field][0]))
            if not data:
                return None
            for slug in self.slugs:
                self[slug]._add_data(data[slug])
            self.data_size += len(data[self.time_field])
        if index < self.data_size:
            for slug in self.slugs:
                self[slug]._set_show(index)
                if index % 10000 == 0:
                    self[slug]._optimize(index)
            return self
        return None


class MQB(BaseMQB):

    BATCH_SIZE = 10000

    def __init__(self, slugs, table, time_field, symbol_tickets, periods, dt1=None, dt2=None, max_last=None, strategy_run_ids=None):
        """

        :param slugs: dict {`name`: `select`} defining what to select from `table`
        :param table: table to select from
        :param time_field: specific field for pagination
        :param symbol_tickets: list: symbol sid to get sequence for
        :param periods: list: period (minutes) to get sequence for
        :param dt1: min datetime to search for
        :param dt2: max datetime to search for
        """

        if not symbol_tickets:
            raise KeyError('Symbol ticket must be defined')

        if not isinstance(symbol_tickets, (list, set, tuple)):
            symbol_tickets = [symbol_tickets]

        if not isinstance(periods, (list, set, tuple)):
            periods = [periods]

        self.sentry = SentryClient(settings.SENTRY_DSN)
        self.slugs = slugs
        self.index = 0
        self.table = table
        self.time_field = time_field
        self.__symbol_tickets = symbol_tickets
        self.__periods = periods
        self.max_last = max_last
        self.strategy_run_ids = strategy_run_ids or []

        self.dt1 = dt1 or datetime(2000, 1, 1)
        self.dt2 = dt2 or datetime(2030, 1, 1)

        self.data_size = 0
        data = self.load_data()
        if data:
            self.data_size = len(data[self.time_field])
            for slug in self.slugs:
                self[slug] = MQBSequence(slug, data[slug], max_last=max_last)

    @property
    def symbol_tickets(self):
        return self.__symbol_tickets

    @property
    def periods(self):
        return self.__periods

    def call(self, method, **kwargs):
        response = requests.get('http://{}:{}/{}'.format(
            settings.MAINNODE_HOST,
            settings.MAINNODE_PORT,
            method,
        ), params=kwargs).json()
        if response.get('ok'):
            return response.get('data', {})
        self.sentry.captureMessage(response.get('error'))
        return None

    def load_data(self, start=None):
        data = self.call(
            'mqb/get',
            table=self.table,
            slugs=', '.join(['{} AS {}'.format(v, k) for k, v in self.slugs.items()]),
            time_field=self.time_field,
            dt1=to_ch_datetime(start or self.dt1),
            dt2=to_ch_datetime(self.dt2),
            symbol_ticket="', '".join(self.symbol_tickets),
            period=', '.join([str(x) for x in self.periods]),
            strategy_run_ids="', '".join(self.strategy_run_ids),
            batch_size=self.BATCH_SIZE,
        )
        if not data:
            return None

        dict_data = defaultdict(list)
        for d in data:
            for k, v in d.items():
                dict_data[k].append(v)
        return dict_data


class QuotesMQB(MQB):

    def __init__(self, symbol_tickets, period=60, dt1=None, dt2=None, max_last=None):

        oanda_symbols = self.call('data_sources/oanda/symbols')
        poloniex_symbols = self.call('data_sources/poloniex/symbols')
        reuters_symbols = self.call('data_sources/reuters/symbols')

        if not isinstance(symbol_tickets, (list, set, tuple)):
            symbol_tickets = [symbol_tickets]

        if all([s in oanda_symbols for s in symbol_tickets]):
            table_name = 'oanda_quotes'
            slugs = {
                'time': 'time',
                'symbol_ticket': 'symbol_ticket',
                'period': 'period',
                'open_ask': 'open_ask',
                'open_bid': 'open_bid',
                'high_ask': 'high_ask',
                'high_bid': 'high_bid',
                'low_ask': 'low_ask',
                'low_bid': 'low_bid',
                'close_ask': 'close_ask',
                'close_bid': 'close_bid',
                'open_mid': '(open_ask+open_bid)/2',
                'high_mid': '(high_ask+high_bid)/2',
                'low_mid': '(low_ask+low_bid)/2',
                'close_mid': '(close_ask+close_bid)/2',
                'delta': 'close_mid-open_mid',
                'volume': 'volume',
            }
        elif all([s in poloniex_symbols for s in symbol_tickets]):
            table_name = 'poloniex_quotes'
            slugs = {
                'time': 'time',
                'symbol_ticket': 'symbol_ticket',
                'period': 'period',
                'open_ask': 'open',
                'open_bid': 'open',
                'high_ask': 'high',
                'high_bid': 'high',
                'low_ask': 'low',
                'low_bid': 'low',
                'close_ask': 'close',
                'close_bid': 'close',
                'open_mid': 'open',
                'high_mid': 'high',
                'low_mid': 'low',
                'close_mid': 'close',
                'delta': 'close-open',
                'volume': 'volume',
            }
        elif all([s in reuters_symbols for s in symbol_tickets]):
            table_name = 'reuters_quotes'
            slugs = {
                'time': 'time',
                'symbol_ticket': 'symbol_ticket',
                'period': 'period',
                'open_ask': 'open',
                'open_bid': 'open',
                'high_ask': 'high',
                'high_bid': 'high',
                'low_ask': 'low',
                'low_bid': 'low',
                'close_ask': 'close',
                'close_bid': 'close',
                'open_mid': 'open',
                'high_mid': 'high',
                'low_mid': 'low',
                'close_mid': 'close',
                'delta': 'close-open',
                'volume': 'volume',
            }
        else:
            raise NoDataError('Symbol Ticket {} not found'.format(symbol_tickets))
        super(QuotesMQB, self).__init__(slugs, table_name, 'time', symbol_tickets, period, dt1, dt2, max_last)


class PredictionMQB(MQB):

    def __init__(self, include_slugs=None, exclude_slugs=None, symbol_tickets=None, period=None,
                 strategy_run_ids=None, dt1=None, dt2=None, max_last=None, time_field='time'):

        base_slugs = {
            'time': 'time',
            'symbol_ticket': 'symbol_ticket',
            'period': 'period',
            'close_time': 'time+duration*60*{}'.format(period),
            'strategy_reference': 'strategy_reference',
            'strategy_params': 'strategy_params',
            'duration': 'duration',
            'prediction': 'value',
        }
        if isinstance(include_slugs, dict):
            base_slugs.update(include_slugs)
        if isinstance(exclude_slugs, (dict, list, tuple, set)):
            for slug in exclude_slugs:
                if slug in base_slugs:
                    del base_slugs[slug]
        super(PredictionMQB, self).__init__(
            base_slugs, 'predictions', time_field, symbol_tickets, period, dt1, dt2, max_last, strategy_run_ids=strategy_run_ids)


class DeltaMQB(MQB):

    def __init__(self, include_slugs=None, exclude_slugs=None, symbol_tickets=None, period=None,
                 dt1=None, dt2=None, max_last=None, time_field='time'):

        base_slugs = {
            'time': 'time',
            'symbol_ticket': 'symbol_ticket',
            'period': 'period',
            'close_time': 'close_time',
            'duration': 'duration',
            'delta_abs': 'delta_abs',
            'delta_pct': 'delta_pct',
            'max_abs': 'max_abs',
            'max_pct': 'max_pct',
            'min_abs': 'min_abs',
            'min_pct': 'min_pct',
        }
        if isinstance(include_slugs, dict):
            base_slugs.update(include_slugs)
        if isinstance(exclude_slugs, (dict, list, tuple, set)):
            for slug in exclude_slugs:
                if slug in base_slugs:
                    del base_slugs[slug]
        super(DeltaMQB, self).__init__(base_slugs, 'delta', time_field, symbol_tickets, period, dt1, dt2, max_last)
