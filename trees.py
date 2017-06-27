import networkx as nx
import numpy as np
import pandas as pd
import math


def corr_matrix(df, window=250, enddate="2017-01-24", method="gower"):
    """To generate correlation matrix for a certain period, method = 'gower' or 'power'"""
    end = int(np.where(df.index == enddate)[0])
    start = end - window + 1
    sub = df[start:end + 1].dropna(axis=1, how='any')  # dropna in case it is too early for some tickers to exist
    # print(sub)
    corr_mat = sub.corr(min_periods=1)
    if method == "gower":
        corr_mat = (2 - 2 * corr_mat[corr_mat.notnull()]) ** 0.5  # gower
    elif method == "power":
        corr_mat = 1 - corr_mat[corr_mat.notnull()] ** 2  # power
    # corr_mat.apply(lambda x:1-x**2 if not math.isnan(x) else np.nan)
    return corr_mat


def rolling_corr(df, window=250, enddate="2017-01-24", startdate='2005-01-03', space=10):
    """Return a dictionary of correlation matrices.
    The key is the enddate of the window, the value is corresponding correlation matrix"""
    end = int(np.where(df.index == enddate)[0])
    start = int(np.where(df.index == startdate)[0])
    space = -space
    dates = df.index.values
    dates = dates[end:start:space]
    result = {}
    for d in dates:
        d = pd.to_datetime(d).strftime("%Y-%m-%d")
        result[str(d)] = corr_matrix(df, window, enddate=d)
    return result


def constructgraph(corr_matrix):
    """Convert a correlation matrix to a graph"""
    G = nx.from_numpy_matrix(corr_matrix.values)
    mapping = dict(zip(list(range(127)), list(corr_matrix.index)))
    G = nx.relabel_nodes(G, mapping, copy=False)
    # delete NAN weights
    for (u, v, d) in G.edges(data=True):
        if math.isnan(d["weight"]):
            G.remove_edges_from([(u, v)])
    # delete self-connected edges
    for (u, v, d) in G.edges(data=True):
        if u == v:
            G.remove_edges_from([(u, v)])
    # delete nodes whose degree is 0
    nodes = list(G.nodes())
    for node in nodes:
        if G.degree(node) == 0:
            G.remove_node(node)
    return G


def importdata(filename):
    """imports data from a .csv file, returns a pandas dataframe of prices and another of log returns"""
    df = pd.read_csv(filename)
    # set date as index and sort by date
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.set_index(pd.DatetimeIndex(df['Date']))
    df = df.drop(['Date'], axis=1)
    df.sort_index(inplace=True)
    # forward fill for NA
    df.fillna(method='ffill', axis=0, inplace=True)
    # Log return
    log_ret = np.log(df) - np.log(df.shift(1))
    return df, log_ret


def MST(filename="SP100_prices.csv", window=250, enddate="2017-01-24", startdate='2015-12-30', space=1):
    """Returns a dictionary of Minimum Spanning Tree for each end date,
    space means the interval between two sample updates"""
    log_ret = importdata(filename)[1]
    dic = rolling_corr(log_ret, window, enddate, startdate, space)
    trees = {}
    for key in sorted(dic.keys()):
        corr_matrix = dic[key]
        G = constructgraph(corr_matrix)
        T = nx.minimum_spanning_tree(G, "weight")
        trees[key] = T
    return trees


# unfinished: need DBHT
def construct_trees(filename="SP100_prices.csv", window=250, enddate="2017-01-24", startdate='2015-12-30', space=1,
                    tree_type='MST'):
    """construct a dictionary of trees {date: tree}. Based on tree_type, can return MST or DBHT"""
    if tree_type == 'MST':
        return MST(filename=filename, window=window, enddate=enddate, startdate=startdate, space=space)
    elif tree_type == 'DBHT':
        pass
        # ......
    else:
        print ("'tree_type' can only be 'MST' or 'DBHT'. Your input was '%s'." % tree_type)
        return None