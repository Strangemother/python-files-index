import os
import json
from datetime import datetime
import subprocess
from uuid import uuid4

from operator import itemgetter


from flask import Flask
from flask import render_template
from flask import jsonify
from flask import request

from log import log


import sys

sys.path.append("C:/Users/jay/Documents/GitHub/files")
sys.path.append("C:/Users/jay/Documents/GitHub/files/v7")
import v7.main as filer
from v7.main import ITEM_KEY, PATHPARTS_KEY, DIRECTORIES_KEY, FileRows

app = Flask(__name__)

UNDEFINED = {}
ROOT = os.path.dirname(__file__)
DATA = UNDEFINED

import platform
import os
import socket


def sysname():
    n1 = platform.node()
    n2 = socket.gethostname()
    n3 = os.environ["COMPUTERNAME"]
    if n1 == n2 == n3:
        return n1
    elif n1 == n2:
        return n1
    elif n1 == n3:
        return n1
    elif n2 == n3:
        return n2
    else:
        raise Exception("Computernames are not equal to each other")


def main(root_path=None, persistent_name=None):
    '''Run the dlask application, checking for a persistent file.'''
    app.run(debug=True, host='0.0.0.0', port=8007)


@app.context_processor
def inject_persistent():
    return dict(cache={
            'sysname':sysname(),
        })


@app.route("/")
@app.route("/<path:path>")
def index_page(path=None):
    '''Flask method for the index.html rendered template.
    '''
    init_data = ''
    if path is not None:
        init_data = get_graph_files(path)
        init_data = json.dumps(init_data)
    return render_template('index.html',
        init_data=init_data,
        path=path,
        )

meta_cache = {}
from flask import g

@app.route("/files/", methods=['GET', 'POST'])
@app.route("/files/<path:path>", methods=['GET', 'POST'])
def get_files(path=None):
    # meta = request.endpoint == 'metae'
    if path is None:
        path = request.form.get('path', path)

    res = get_graph_files(path)
    return jsonify(res)

def get_graph_files(path=None):
    st = time.time()
    res = meta_cache.get(path, None)
    if res is None:
        res = get_graph(path, True, True)
        if res is not None:
            path = path or res['path']
            print('Writing cache', path)
            meta_cache[path]  = res
            res['from_cache'] = False
    else:
        res['from_cache'] = True
    if len(res['meta']) == 0:
        print('\nno files')

    res['time'] = time.time() - st
    return res


@app.route("/files-meta/", methods=['GET', 'POST'], endpoint='metae')
@app.route("/files-meta/<path:path>", methods=['GET', 'POST'], endpoint='metae')
def get_files_meta(path=None):
    return jsonify(meta_cache.get(path, get_graph(path, True, True)))

from operator import itemgetter
import time

DATA = filer.main()

def get_graph(path=None, meta=False, meta_only=False, graph=None, count=False):
    '''Flask method for the index.html rendered template.
    '''

    if path is None:
        # root address for initial request
        graph =  graph or DATA.top()
    else:
        if path.endswith('/'):
            path = path[:-1]
        graph = graph or  DATA.walkers[0].resolve_path(path, sep='/')

    if graph is None:
        graph = DATA.top()

    meta_keys = None
    hidden_keys = set([PATHPARTS_KEY, ITEM_KEY])

    try:

        if meta is True:
            meta_keys = ()
            g_keys = set(graph.keys()) - hidden_keys
            for x in g_keys:
                subgraphs = {}
                y = graph[x]
                has_content = None
                is_file = False
                if hasattr(y, 'get'):
                    is_file = len(y.get(ITEM_KEY, '')) == 0

                if is_file is False:
                    # test again
                    pp = graph.get('%_pathparts_%', None)
                    fp = '/'.join(pp + (x,)) if pp else x
                    is_file = os.path.isfile(fp)

                # name (of folder or fild),
                #   boolean,
                #       int of children count,
                #           sorter key index
                _count = len(set(y.keys()) - hidden_keys)
                if _count == 1:
                    subgraphs[x] = get_graph(graph=y, count=True)
                meta_keys += ( (x, is_file, _count, x.lower(), subgraphs),)
            meta_keys = sorted(meta_keys, key=itemgetter(3))
        elif count is True:
            meta_keys = ()

            g_keys = set(graph.keys()) - hidden_keys
            for x in g_keys:
                y = graph[x]
                _count = len(set(y.keys()) - hidden_keys)
                meta_keys += ( (x, _count,),)
        if meta_only is False:
            keys = set(graph.keys()) - hidden_keys
        else:
            keys = None
    except AttributeError:
        if isinstance(graph, tuple):
            files  = FileRows(DATA.walkers[0].row[graph], path)
            keys = set(tuple(x.name for x in files))

    try:
        diffed = tuple(keys - hidden_keys)
        view_keys = tuple(keys)#diffed#view_keys = sorted(diffed, key=str.lower)
    except TypeError:
        view_keys = keys

    if hasattr(graph, 'get'):
        parts = graph.get(PATHPARTS_KEY, None)
    else:
        parts = path.split('/')

    is_file = False
    if view_keys is None or len(view_keys) == 0 \
        or  meta_keys is None or len(meta_keys) == 0:
        if isinstance(path, str):
            is_file = os.path.isfile(path)

    data = {
            "path": path,
            'keys': view_keys,
            'meta': meta_keys,
            "parts": parts,
            "is_file": is_file,
        }

    return data


@app.route("/scan/", methods=['GET', 'POST'])
def perform_scan():
    '''Flask method for the index.html rendered template.
    '''
    global DATA
    DATA = filer.main(False)
    DATA.save('a','b')
    data = { 'items': dict(name='foo'), }
    return jsonify(data)


query_cache = {}

@app.route("/search/", methods=['GET', 'POST'])
def perform_search():
    '''Flask method for the index.html rendered template.
    '''
    query = request.form.get('query')
    words = request.form.get('word', None) is not None
    partial = request.form.get('partial', None) is not None
    start = request.form.get('start', None)
    limit = request.form.get('limit', None)
    without_results = request.form.get('without_results', None) is not None

    qs = '-'.join(map(str, (query, words, partial, limit, without_results)))
    if qs in query_cache:
        return query_cache[qs]


    res = 0 if without_results else ()
    if partial:
        rows = DATA.search(query)
        if without_results:
            res += len(rows)
        else:
            for row in rows:
                res += ( (row.name, row.path.split(os.path.sep), row.size),)

    if words:
        rows = DATA.query(query)
        if without_results:
            res += len(rows)
        else:
            for row in rows:
                res += ( (row.name, row.path.split(os.path.sep), row.size),)

    len_res = res if without_results else len(res)
    if limit is not None:
        res = res[int(start) if start else 0: int(limit)]

    query_cache[qs] = jsonify({
            'query': query,
            'limit': int(limit),
            'start': start,
            'items': [] if without_results else res,
            'total': res if without_results else len_res,
            'total_size': rows.total_size(),
            'size_str': rows.size,
        })

    return query_cache[qs]


if __name__ == '__main__':
    main()
