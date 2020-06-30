import pandas as pd
from argparse import ArgumentParser
import numpy as np
from matplotlib import cm

def main(args):
    df1 = pd.read_csv(args.top_csv)
    df2 = pd.read_csv(args.bot_csv)
    top = df1.values[:, 1:]
    top = np.array(top)
    max_top = np.ptp(top)
    bot = df2.values[:, 1:]
    bot = np.array(bot)
    max_bot = np.ptp(bot)
    # I need f(y) : f(mx) = T, f(0) = 0
    # Scale 0 -> T to 0 to mx
    def rescale(m, mx):
        nm = np.where(m>0,m,int(1e9))
        T = 0.35
        mn = np.min(nm)
        #print(mn)
        def alter(x):
            if x==0:
                return 1.0
            #print(x, mn)
            shift_x = x-mn
            sc = shift_x/mx
            assert 0<=sc and sc<=1
            rsc = sc*T

            return 1-rsc
            #return 1-((x-mn)/mx)*T

        #scale = lambda x: alter(x)
        return alter
    top_scale = rescale(top, max_top)
    bot_scale = rescale(bot, max_bot) 
    # print(scale(m))
    #keys = df1.columns[1:]
    def f(c, v):
        r, g, b, a = c
        g = lambda x: '{:3f}'.format(x)
        cstring = ','.join(map(g, c[:3]))
        color = '\\cellcolor[rgb]{{{c}}}{{{v}}}'.format(c=cstring, v=v)
        return color

    for ii in range(1, len(df1.index)+1):
        vals = []
        i = ii-1
        for j in range(0, len(df2.index)+1):
            if  j==0:
               vals.append(str(df1.values[i,j]))

            elif ii<j:
                x = int(top_scale(df1.values[i,j]) * 255)
                color =cm.Blues_r(x)
                cell = f(c=color, v=df1.values[i,j])
                vals.append(cell)
            elif ii>j:
                x = int(bot_scale(df2.values[i,j]) * 255)
                color =cm.Reds_r(x)
                cell = f(c=color, v=df2.values[i,j])
                vals.append(cell)
            else:
                vals.append('')
            #print(df1.values[i,j],df2.values[i,j],i,j)
            # for idx, row in df1.iterrows():
            #     
            #     for key in keys:
            #         v = row[key]
            #         cell = ('\\cc{{{c:.3f}}}{{{v}}}'
            #                 .format(c=scale(v), v=v))
            #         vals.append(cell)
        
        print('&'.join(vals), end='')
        print('\\\\')


    

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--top_csv', type=str, required=True)
    parser.add_argument('--bot_csv', type=str, required=True)
    args = parser.parse_args()
    main(args)