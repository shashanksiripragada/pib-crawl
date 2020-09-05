import pandas as pd
from argparse import ArgumentParser
import numpy as np
from matplotlib import cm
import sys

def colorcell(c, v):
    r, g, b, a = c
    g = lambda x: '{:3f}'.format(x)
    color_string = ','.join(map(g, c[:3]))
    color = '\\cellcolor[rgb]{{{c}}}{{{v}}}'.format(c=color_string, v=v)
    return color

class Grid:
    def __init__(self, path, ):
        self.df = pd.read_csv(path)
        self.df = self.df.fillna(0)
        self.nrows, self.ncols = self.df.values.shape
        self.nrows = self.nrows + 1
        self.row_headers = self.df.values[:, 0].tolist()
        self.column_headers = self.df.values[:, 0].tolist()

    @property
    def values(self):
        return self.df.values[:, 1:]

    def __getitem__(self, i, j):
        assert(i >= 0 and j >= 0 and i < self.nrows-1 and j < self.ncols-1)
        return self.values[i, j]

    def __repr__(self):
        return self.df.__repr__()

class Scaling:
    def __init__(self, values, cmap, max_intensity=0.35, width=None,
            minimum=None):
        self.values = values
        self.width = width or np.ptp(values)
        self.max_intensity = max_intensity
        self.cmap = cmap
        self.minimum = minimum or np.min(values)

    def rescale(self, value):
        if value == 0: return 1.0
        scaled = (value - self.minimum)/self.width
        assert 0 <= scaled and scaled<=1
        intensity_adjusted = scaled*self.max_intensity
        # return intensity_adjusted
        return 1-intensity_adjusted

    def color(self, i, j, value):
        dvalue = self.values[i, j]
        dvalue = self.rescale(dvalue)
        color = self.cmap(int(dvalue*255))
        return colorcell(color, value)

class ColorMapping:
    def __init__(self, values, max_intensity=0.35, cmap=cm.Blues_r):
        self.values = values.astype(np.float32)

        self.positives = np.where(values>0, values, 0)
        self.negatives = np.where(values<0, values, 0)
        
        self.scaling_plus = Scaling(self.positives, cm.Blues_r,
                max_intensity=max_intensity)
        self.scaling_negs = Scaling(-1*self.negatives, cm.Reds_r,
                max_intensity=max_intensity)

        width, minimum = self.adjust(self.scaling_plus, self.scaling_negs)

        # Update
        self.scaling_plus = Scaling(self.positives, cm.Blues_r,
                max_intensity=max_intensity, width=width,
                minimum=minimum)
        self.scaling_negs = Scaling(-1*self.negatives, cm.Reds_r,
                max_intensity=max_intensity, width=width,
                minimum=minimum)

    def adjust(self, plus, negs):
        width = max(plus.width, negs.width)
        minimum = min(plus.minimum, negs.minimum)
        return width, minimum

    def color(self, i, j, value):
        if self.values[i, j] >= 0:
            return self.scaling_plus.color(i, j, value)
        else:
            return self.scaling_negs.color(i, j, value)

    def __repr__(self):
        return self.values.__repr__()


def pretty_grid(current, mapping, diff, cell_type, dreduce=False, triangular=False):
    if dreduce:
        row_diff_sum = np.sum(diff, axis=1).tolist()
        col_diff_sum = np.sum(diff, axis=0).tolist()

    fmt = {
        'float': r'{:.2f}',
        'int': r'{}'
    }

    print('&'.join([''] + current.column_headers) , '\\\\')
    for i in range(0, current.nrows-1):
        vals = []
        vals.append(str(current.row_headers[i]))
        for j in range(0, current.ncols-1):
            if i != j:
                v = current.__getitem__(i, j)
                v = fmt[cell_type].format(v)
                cell = mapping.color(i, j, v)
                if triangular and i > j:
                    vals.append('')
                else:
                    vals.append(cell)
            else:
                vals.append('')
        
        print('&'.join(vals), end='')
        if dreduce:
            print('&', fmt[cell_type].format(row_diff_sum[i]))
        print('\\\\')

    if dreduce:
        col_diff_sum = [fmt[cell_type].format(x) for x in col_diff_sum]
        print('&'.join(col_diff_sum))

def main(args):
    current = Grid(args.after)
    previous = Grid(args.before)
    diff = current.values - previous.values
    if args.cell_type == 'float':
        diff = np.array(diff, dtype=np.float32)


    before = previous.values.sum()
    after = current.values.sum()
    increment = diff.sum()
    M, N = diff.shape
    assert (M == N)
    diffs = diff.ravel()
    diffs = diffs[diffs != 0]
    average_increment = np.median(diffs)

    print("Before:{}".format(before), "After: {}".format(after)
            , "Increase: {}".format(increment), 'Median: {}'.format(average_increment))

    mapping = ColorMapping(diff)
    pretty_grid(current, mapping, diff, args.cell_type, args.reduce, args.triangular)

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--before', type=str, required=True)
    parser.add_argument('--after', type=str, required=True)
    parser.add_argument('--cell-type', choices=['float', 'int'], default='float')
    parser.add_argument('--reduce', action='store_true')
    parser.add_argument('--triangular', action='store_true')
    args = parser.parse_args()
    main(args)
