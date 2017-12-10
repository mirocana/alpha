from sequence import QuotesMQB, Context
from miscellaneous.utils import to_datetime
from datetime import datetime, timedelta
from raven import Client as SentryClient
from copy import deepcopy
import settings
import dill

BASE_DURATIONS = [1, 2, 3, 4, 5, 6, 8, 10, 12, 14, 16, 18, 20, 25, 30, 35, 40, 45, 50, 60, 70, 80, 90, 100]


class BaseStrategy(object):

    BATCH_SIZE = 1000
    DURATIONS = deepcopy(BASE_DURATIONS)
    MAX_LAST = None
    K1, K2, K3 = None, None, None

    def __init__(self, strategy_run):
        """

        :param strategy_run: {
            _id: str,
            symbol_ticket: str,
            period: int,
            iteration_time: datetime,
            iteration_number: int,
            context: Context,
        }
        """
        self.name = self.__class__.__name__
        self.strategy_run = strategy_run
        self.sentry = SentryClient(settings.SENTRY_DSN)
        self.mqb = None

        if not self.strategy_run.get('context'):
            self.strategy_run['context'] = dill.dumps(Context())
        if not self.strategy_run.get('iteration_number'):
            self.strategy_run['iteration_number'] = 0

    def calculate_predictions(self):
        is_explored = False
        predictions_data = []

        if not self.mqb:
            self.mqb = QuotesMQB(
                symbol_tickets=self.strategy_run.get('symbol_ticket'),
                period=self.strategy_run.get('period'),
                dt1=self.strategy_run.get('iteration_time')
            )

        context = dill.loads(self.strategy_run.get('context'))
        if not self.strategy_run.get('iteration_time'):
            self.initiate(context)

        for i, mqb in enumerate(self.mqb):
            current_time = to_datetime(mqb['time'][0])
            if current_time < datetime.utcnow() - timedelta(days=1):
                self.strategy_run['iteration_time'] = current_time
                self.strategy_run['iteration_number'] += 1

                predictions = []
                try:
                    predictions = self.apply_code(mqb, context)
                except Exception as e:
                    print('apply_code error: {}'.format(str(e)))
                    self.sentry.captureException()

                for prediction in predictions:
                    strategy_params = []
                    for slug in [k for k in ('k1', 'k2', 'k3') if k in prediction]:
                        strategy_params.append('{}={}'.format(slug, prediction[slug]))
                    prediction_data = {
                        'strategy_reference': self.strategy_run.get('strategy_reference'),
                        'strategy_params': ', '.join(strategy_params),
                        'strategy_run_id': self.strategy_run['_id'],
                        'create_time': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
                        'version': self.strategy_run.get('version', settings.VERSION),
                        'symbol_ticket': self.strategy_run.get('symbol_ticket'),
                        'period': self.strategy_run.get('period'),
                        'time': mqb['time'][0],
                        'date': mqb['time'][0].split()[0],
                        'duration': prediction['duration'],
                        'value': prediction['value'],
                    }
                    predictions_data.append(prediction_data)
            else:
                is_explored = True
                break

            if len(predictions_data) >= self.strategy_run.get('batch_size', self.BATCH_SIZE):
                break

            if i > 1000:
                break

        self.strategy_run['context'] = dill.dumps(context)
        return self.strategy_run, predictions_data, is_explored

    def initiate(self, ctx):
        return

    def apply_code(self, mqb, ctx):
        raise NotImplementedError()

