from statsmodels.nonparametric.kernel_regression import KernelReg
from strategies.base import BaseStrategy, BASE_DURATIONS
from sklearn.tree import DecisionTreeClassifier
from miscellaneous.utils import to_datetime
from scipy.signal import argrelextrema
from collections import defaultdict
from datetime import timedelta
from numpy import linspace
from uuid import uuid4
import pandas as pd
import numpy as np


class MAStrategy(BaseStrategy):

    DURATIONS = BASE_DURATIONS
    MAX_LAST = max(DURATIONS) * 14
    K1 = [10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 25, 30, 35, 40, 45, 50, 60, 70, 80, 90, 100]

    def apply_code(self, mqb, ctx):
        predictions = []
        delta = np.mean(np.abs(mqb['delta'].last(14)))
        if delta != 0:
            for duration in self.DURATIONS:
                ma7 = np.mean(mqb['close_ask'].last(7 * duration))
                ma14 = np.mean(mqb['close_ask'].last(14 * duration))
                ma_delta = ma7 - ma14
                for k1 in self.K1:
                    if ma_delta > delta * k1:
                        prediction = {'duration': duration, 'value': 1, 'k1': k1}
                        predictions.append(prediction)
                    elif -ma_delta > delta * k1:
                        prediction = {'duration': duration, 'value': -1, 'k1': k1}
                        predictions.append(prediction)
        return predictions


class LevelStrategy(BaseStrategy):

    DURATIONS = BASE_DURATIONS
    MAX_LAST = max(DURATIONS) * 14
    K1 = [20, 30, 40, 50, 100]

    def apply_code(self, mqb, ctx):
        predictions = []

        for duration in self.DURATIONS:
            max14 = np.max(mqb['close_ask'].last(14 * duration))
            min14 = np.min(mqb['close_ask'].last(14 * duration))

            for k1 in self.K1:
                delta14 = (max14 - min14) / k1
                if mqb['close_ask'][0] > max14 - delta14:
                    prediction = {'duration': duration, 'value': -1, 'k1': k1}
                    predictions.append(prediction)
                elif mqb['close_ask'][0] < min14 + delta14:
                    prediction = {'duration': duration, 'value': 1, 'k1': k1}
                    predictions.append(prediction)
        return predictions


class BollingerStrategy(BaseStrategy):

    DURATIONS = BASE_DURATIONS
    MAX_LAST = max(DURATIONS) * 14
    K1 = [3, 4, 5, 6, 7, 8, 9, 10, 12, 14, 16, 18, 20, 25]

    def apply_code(self, mqb, ctx):
        predictions = []

        for duration in self.DURATIONS:
            # delta = np.mean(np.abs(mqb['delta'].last(14 * duration)))
            delta = np.mean(np.abs(mqb['delta'].last_with_duration(20, duration)))
            # ma14 = np.mean(mqb['close_ask'].last(14 * duration))
            ma14 = np.mean(mqb['close_ask'].last_with_duration(20, duration))

            for k1 in self.K1:
                if mqb['close_ask'][0] > ma14 + delta*k1:
                    prediction = {'duration': duration, 'value': -1, 'k1': k1}
                    predictions.append(prediction)
                elif mqb['close_ask'][0] < ma14 - delta*k1:
                    prediction = {'duration': duration, 'value': 1, 'k1': k1}
                    predictions.append(prediction)
        return predictions


class DecisionTreeStrategy(BaseStrategy):

    DURATIONS = BASE_DURATIONS
    MAX_LAST = max(DURATIONS) * 10 + 1

    K1 = [5, 10, 20, 30, 40, 50, 75, 100]

    def initiate(self, ctx):
        ctx['current_batch'] = defaultdict(dict)
        ctx['new_batches'] = defaultdict(lambda: defaultdict(dict))
        ctx['batches'] = defaultdict(list)
        ctx['model'] = defaultdict(dict)
        ctx['prediction_list'] = defaultdict(list)

    def apply_code(self, mqb, ctx):
        predictions = []

        for duration in self.DURATIONS:

            if not ctx['current_batch'].get(duration):
                ctx['current_batch'][duration] = [mqb.delta[0]]
            elif len(ctx['current_batch'].get(duration)) < 10 * duration:
                ctx['current_batch'][duration].append(mqb.delta[0])
            else:
                ctx['new_batches'][duration][str(uuid4())] = {
                    'x': ctx['current_batch'][duration],
                    'y': mqb.delta[0],
                    'time': to_datetime(mqb.time[0]) + timedelta(minutes=duration),
                }
                ctx['current_batch'][duration] = []

            if ctx['model'][duration].get('batch_size', 0) != len(ctx['batches'][duration]) and len(ctx['batches'][duration]) >= 200:
                x = np.array([[1 if xx > 0 else -1 for xx in x['x']] for x in ctx['batches'][duration][-1000:]], dtype=np.float32)
                y = np.array([1 if x['y'] > 0 else -1 for x in ctx['batches'][duration][-1000:]], dtype=np.float32)
                model = DecisionTreeClassifier(max_depth=5)
                model.fit(x, y)
                ctx['model'][duration] = {
                    'clf': model,
                    'batch_size': len(ctx['batches'][duration])
                }

            del_keys = []
            for key, value in ctx['new_batches'][duration].items():
                if to_datetime(mqb.time[0]) >= value['time']:
                    ctx['batches'][duration].append(value)
                    del_keys.append(key)

            for key in del_keys:
                del ctx['new_batches'][duration][key]

            if ctx['model'][duration]:
                data = np.array(mqb.delta.last((10 * duration) + 1), dtype=np.float32)
                x = data[:10 * duration].reshape(1, -1)
                y = data[-1].reshape(1, -1)
                prediction = ctx['model'][duration]['clf'].predict(x, y)
                if prediction and prediction[0]:
                    ctx['prediction_list'][duration].append(prediction)
                ctx['prediction_list'][duration] = ctx['prediction_list'][duration][-100:]
                for k1 in self.K1:
                    if sum(ctx['prediction_list'][duration][-k1:]) == k1:
                        prediction = {'duration': duration, 'value': 1, 'k1': k1}
                        predictions.append(prediction)
                    elif sum(ctx['prediction_list'][duration][-k1:]) == -k1:
                        prediction = {'duration': duration, 'value': -1, 'k1': k1}
                        predictions.append(prediction)
        return predictions


class PatternRecognitionStrategy(BaseStrategy):
    TIMES_IN_WINDOW = 30

    DURATIONS = BASE_DURATIONS
    K1 = [3, 4, 5, 6, 7, 8, 9, 10, 12, 14, 16, 18, 20, 25]
    MAX_LAST = max(DURATIONS) * 30

    def initiate(self, ctx):
        ctx['max_min'] = defaultdict(float)
        ctx['iter_count'] = 0

    def find_max_min(self, prices, kr):
        prices_ = prices.copy()
        prices_.index = linspace(1., len(prices_), len(prices_))
        kr = kr
        f = kr.fit([prices_.index.values])
        smooth_prices = pd.Series(data=f[0], index=prices_.index)

        local_max = argrelextrema(smooth_prices.values, np.greater)[0]
        local_min = argrelextrema(smooth_prices.values, np.less)[0]

        price_local_max_indexes = []
        for i in local_max:
            if (i > 1) and (i < len(prices) - 1):
                price_local_max_indexes.append(prices.iloc[i - 2:i + 2].argmax())

        price_local_min_indexes = []
        for i in local_min:
            if (i > 1) and (i < len(prices) - 1):
                price_local_min_indexes.append(prices.iloc[i - 2:i + 2].argmin())

        prices.name = 'price'
        maxima = pd.DataFrame(prices.loc[price_local_max_indexes])
        minima = pd.DataFrame(prices.loc[price_local_min_indexes])
        max_min = pd.concat([maxima, minima]).sort_index()

        max_min.index.name = 'date'

        max_min = max_min.reset_index()

        max_min = max_min[~max_min.date.duplicated()]

        p = prices.reset_index()
        max_min['day_num'] = p[p['index'].isin(max_min.date)].index.values

        max_min = max_min.set_index('day_num').price

        return max_min

    def apply_code(self, mqb, ctx):
        pass


class ExpandedBottomStrategy(PatternRecognitionStrategy):
    TIMES_IN_WINDOW = 30

    def apply_code(self, mqb, ctx):
        predictions = []

        ctx['iter_count'] += 1

        for duration in self.DURATIONS:

            if ctx['iter_count'] > duration*self.TIMES_IN_WINDOW:
                close_mid_values = mqb['close_mid'].last_with_duration(self.TIMES_IN_WINDOW, duration)
                indexes = linspace(1., len(close_mid_values), len(close_mid_values))
                close_prices = pd.Series(index=indexes, data=close_mid_values)
                prices = close_prices.copy()

                kr = KernelReg([prices.values], [prices.index.values], var_type='c', bw=[1.8, 1])

                max_mins = self.find_max_min(prices, kr)

                if max_mins.shape[0] == 5:
                    e1 = max_mins.iloc[0]
                    e2 = max_mins.iloc[1]
                    e3 = max_mins.iloc[2]
                    e4 = max_mins.iloc[3]
                    e5 = max_mins.iloc[4]

                    if e1 > e2 and e3 > e2 and e5>e2 and e1>e4 and e3 > e4 and e5 > e4:
                        if e5 > e3 > e1 and e2 < e4:
                            if close_mid_values[-1] > e5:
                                prediction = {'duration': duration, 'value': 1}
                                predictions.append(prediction)

                elif max_mins.shape[0] == 6:
                    e1 = max_mins.iloc[0]
                    e2 = max_mins.iloc[1]
                    e3 = max_mins.iloc[2]
                    e4 = max_mins.iloc[3]
                    e5 = max_mins.iloc[4]
                    e6 = max_mins.iloc[5]

                    if e1 > e2 and e3 > e2 and e5 > e2 and e1> e4 and e1 > e4 and e5 > e4 and e1>6 and e3 > e6 and e5> e6:
                        if e1 < e3 < e5 and e6 < e4 < e2:
                            if close_mid_values[-1] < e6:
                                prediction = {'duration': duration, 'value': -1}
                                predictions.append(prediction)

        return predictions
