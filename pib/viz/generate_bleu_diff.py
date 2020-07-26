import pandas as pd
import numpy as np
from argparse import ArgumentParser
from matplotlib import cm

def generate(before, after):
    key = 'Unnamed: 0'
    index = before[key]
    before = before.drop(key, 1)
    after = after.drop(key, 1)
    diff = after.subtract(before)
    positives = diff.where(diff > 0, 0)
    negatives = diff.where(diff < 0, 0)
    negatives = -1*negatives

    diff.insert(0, key, index)
    colors = diff.copy()
    nrows, ncols = diff.shape


    def colors(diff):
        _colors = {}
        def scaleValues(df):
            grid = df.values
            mn = np.min(grid)
            mx = np.ptp(grid)
            def f(x):
                return (x - mn)/mx
            return f

        def f(cmap, cF, v):
            x = cF(v)
            T = 0
            x = x * 0.35 + T
            x = cmap(int(255*x))
            return x

        cP = scaleValues(positives)
        cN = scaleValues(negatives)
        for i in range(0, nrows):
            for j in range(1, ncols):
                v = diff.iat[i, j]
                if v > 0:
                    _colors[(i, j)] = f(cm.Blues, cP, v)

                else:
                    _colors[(i, j)] = f(cm.Reds, cN, -1*v)
        return _colors

    def f(c, v):
        r, g, b, a = c
        g = lambda x: '{:3f}'.format(x)
        cstring = ','.join(map(g, c[:3]))
        color = '\\cellcolor[rgb]{{{c}}}{{{v}}}'.format(c=cstring, v=v)
        return color

    diff_colors = colors(diff)
    nrows, ncols = diff.shape
    print('&'.join(diff.columns.values))
    print('\\\\')
    print('\\hline')
    for i in range(0, nrows):
        vals = [diff.iat[i, 0]]
        for j in range(1, ncols):
            v = '{:.2f}'.format(diff.iat[i, j])
            c = f(diff_colors[(i, j)], v)
            vals.append(c)
        print(' & '.join(vals))
        print('\\\\')

    


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--before', type=str, required=True)
    parser.add_argument('--after', type=str, required=True)
    args = parser.parse_args()
    before = pd.read_csv(args.before)
    after = pd.read_csv(args.after)
    generate(before, after)
