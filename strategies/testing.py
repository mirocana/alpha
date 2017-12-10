from miscellaneous.utils import to_datetime, time_usage
from collections import defaultdict
from sequence import DeltaMQB
from bson import ObjectId
import importlib


class TestStrategy(object):

    def __init__(self, strategy_reference, symbol_ticket='EUR_USD', period=60, batch_size=300):
        self.strategy_reference = strategy_reference
        self.strategy_run = {
            '_id': str(ObjectId()),
            'symbol_ticket': symbol_ticket,
            'period': period,
            'batch_size': batch_size,
        }
        with time_usage('delta'):
            self.delta_mqb = DeltaMQB(symbol_tickets=symbol_ticket, period=period)
        self.delta = defaultdict(lambda: defaultdict(dict))

        self.total_predictions = 0
        self.right_predictions = 0
        self.batch_counter = 0
        self.total_result = 0

    def start(self):
        module_name, class_name = self.strategy_reference.rsplit(".", 1)
        strategy = getattr(importlib.import_module(module_name), class_name)(self.strategy_run)
        while True:
            # with time_usage('calculate_predictions'):
            strategy_run, predictions, is_explored = strategy.calculate_predictions()
            self.strategy_run = strategy_run
            # with time_usage('print_progress'):
            self.print_progress(predictions)
            if is_explored:
                break

    def print_progress(self, predictions):
        with time_usage('load_delta'):
            self.load_delta()
        total_predictions = len(predictions)
        for p in predictions:
            p['delta_pct'] = self.delta.get(p['time'], {}).get(p['duration'], {}).get('delta_pct', 0)*p.get('value', 0)
            if p['delta_pct'] > 0:
                self.right_predictions += 1
        total_result = sum([x['delta_pct'] for x in predictions])
        self.total_result += total_result
        self.batch_counter += 1
        self.total_predictions += total_predictions
        win_rate = self.right_predictions / self.total_predictions if self.total_predictions else 0
        print(
            "BTCH_N\t{batch_number}\t"
            "PR_P_B\t{prediction_in_batch}\t"
            "ALL_PR\t{total_predictions}\t"
            "TTL_RES\t{total_result:.2f}\t"
            "WIN_R\t{win_rate:.2f}".format(
                batch_number=self.batch_counter,
                prediction_in_batch=total_predictions,
                total_predictions=self.total_predictions,
                total_result=self.total_result,
                win_rate=win_rate
            )
        )

    def load_delta(self):
        for i, mqb in enumerate(self.delta_mqb):
            self.delta[mqb['time'][0]][mqb['duration'][0]] = mqb.to_dict()
            if to_datetime(mqb['time'][0]) > self.strategy_run['iteration_time']:
                break


if __name__ == '__main__':
    test = TestStrategy(
        strategy_reference='strategies.simple.DecisionTreeStrategy',
        symbol_ticket='EUR_USD',
        period=60,
    )
    test.start()
