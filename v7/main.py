import time
import sys
import os
import marshal
import re
import io

from pprint import pprint as pp

p = "C:/Users/jay/Documents/projects/context-api/context/src"
sys.path.append(p)


from scan import scan


DIRS = (
        # './tests/fixtures/folders',
        "F:\\movies",
        "F:\\dwhelper",
        "D:\\movies",
        "G:\\tv",
        "I:\\Video\\Movies",
        "I:\\Video\\TV",
    )


def main(allow_cache=True):
    global result
    print('main')
    start = time.time()

    if len(sys.argv) > 1:
        cache_path = sys.argv[1]
        print('Using cache file', cache_path)
        d = DataWalker(*load_binary(cache_path))
    else:
        d = FileWalker()
        try:
            dirn = os.path.abspath(os.path.dirname(__file__))
        except NameError:
            dirn = os.path.abspath(os.path.dirname('.'))

        if allow_cache:
            print('Loading cache from baked files')
            a = os.path.join(dirn, 'a')
            b = os.path.join(dirn, 'b')
            if os.path.exists(a):
                d.load(a, b)
            else:
                print('Cache was requested but does not exist.')
        else:
            print('Scan required.')
            result = run_scan(DIRS)
            d = make_filewalker(result[0])
            # db = as_graph(result[0])
        #return db

    print('Done. Perform "db.find(key,...)"')
    end = time.time()
    print('Total time:', end - start)
    return d


def run_scan(dirs, recurse=True, ignore=None):
    '''
    Perform a scan of all dirs, returning "files, folders"
    '''

    start = time.time()
    res = scan(dirs, recurse, ignore=ignore)
    end = time.time()
    print( 'BOOM!')
    print('Scan Time:', end - start)
    return res

GB_1 = 1e+9
GB_4 = GB_1 * 4

def as_graph(files):
    import database
    from database.db import DB
    from database.graph import GraphDB, ObjectDB

    # db = GraphDB(directory='./files_db', max_bytes=GB_4)
    # db.open('files')
    # db.wipe()
    # record_files(db, files)

    db2 = GraphDB(directory='./files_db2', max_bytes=GB_4)
    db2.open('part')
    db2.wipe()
    return make_filewalker(files)
    #return db, db2
    return db2


def save_binary(data, filepath=None):
    filepath = filepath or 'db.ms'

    with open(filepath, 'wb') as stream:
        return marshal.dump(data, stream)


def load_binary(filepath=None):
    filepath = filepath or 'db.ms'

    with open(filepath, 'rb') as stream:
        return marshal.load(stream)


def record_files(db, files):
    print("\n\nAdding to DB; Currently:", db.count(), ' - Adding files:', len(files))
    count = 0
    start = time.time()

    for dataset in files:
        row = dataset[0], dataset[2], dataset[3]
        db.put(dataset[1], row, save=False)

    print("Finished.", db.count(), 'Commiting...')

    db.commit()
    end = time.time()

    print('Store Time:', end - start)
    print('Record count', db.count(), 'Caching Parts')


ITEM_KEY = '%_items_%'
DIRECTORIES_KEY = '%_directories_%'
PATHPARTS_KEY = '%_pathparts_%'

def make_filewalker(files):
    print("\n:", len(files))

    start = time.time()
    count = 0
    graph = { DIRECTORIES_KEY: {}}

    row_counter = -1
    name_list = ()

    word_graph = { 'standard': {}, 'lower': {}, 'ext': {}}

    for dataset in files:
        row = dataset[0], dataset[2], dataset[3]
        splits = dataset[0].split(os.path.sep)
        ext = os.path.splitext(row[0])[1][1:]
        name_list += (row, )
        row_counter += 1

        last_graph = graph

        ext_d = word_graph['ext'].get(ext, ())
        ext_d += (row_counter, )
        word_graph['ext'][ext] = ext_d

        last_part = None
        # 194 178
        lr_path = ()
        for path_part in splits:

            # Add the row to the subgraph items.
            portion = last_graph.get(path_part, { ITEM_KEY: ()})
            portion[ITEM_KEY] += (row_counter, )
            last_graph[path_part] = portion
            last_graph = last_graph[path_part]

            lr_path += (path_part, )
            last_graph[PATHPARTS_KEY] = lr_path


            folder_list = graph[DIRECTORIES_KEY].get(path_part, ())
            folder_list += (row_counter, )
            graph[DIRECTORIES_KEY][path_part] = folder_list
            count += 1



        word_split = re.split('[\s\-._\/\\\]', dataset[0])
        for word in word_split:
            word_list = word_graph['standard'].get(word, set())
            word_list.add(row_counter)
            word_graph['standard'][word] = word_list

            lower = word.lower()
            if lower != word:
                word_list = word_graph['lower'].get(lower, set())
                word_list.add(row_counter)
                word_graph['lower'][lower] = word_list


        if count % 2000 == 0:
            print('count {:,}'.format(count))

        #     #db.commit()
    end = time.time()
    print('Time Taken:', end - start)
    print('Portions: {:,}'.format(count))

    # db.commit()
    # tuple(x[0] for x in name_list if '1080' in x[0].lower())
    parent = DataWalker(graph, name_list)
    sub = DataWalker(word_graph, parent=parent)
    return FileWalker(parent, sub)


class DataWalker(object):
    """The simple data walker helps step through the graph:

        db['I:'].Video.TV.Friends['Season 10']
    """

    def __init__(self, graph=None, name_list=None, parent=None, **kw):
        """Given a previously generated graph, the walker allows
        easier abstraction of values.

        Provide a name list for key row resolution to index items within
        the graph.

        The parent is the owning walker this walker. If the name_list is none,
        this walker will test up the chain for a name_list.

        """
        self.graph = graph
        self.name_list = name_list
        self._row = None
        self.parent = parent or self
        self.kw = kw

    def resolve_path(self, path, sep=None):
        """Walk the path left to right resolving the sub dictionary
        index. Return an object of graph keys.

        db<FileWalker>.<datawalker>

            db.walkers[0].resolve_path('G:\\264\\Two\\tK')

        resolve an index in the row:

             db.walkers[0].get_row(11005)

        """
        sep = sep or os.path.sep

        graph = self.graph
        for item in path.split(sep):
            cur_graph = graph.get(item, None)
            if cur_graph is None:
                print('Key (subkey) "{}" is not a object in the graph'.format(item))
                return None
            graph = cur_graph

        return graph

    def dir_files(self, directory):
        ints = self.graph[DIRECTORIES_KEY].get(directory, None)
        rows = self.row[ints]
        return FileRows(rows, directory)
        # sub_graph = self.resolve_dir(path)

    def path_files(self, path, sep=None):
        sub_graph = self.resolve_path(path, sep=sep)
        if sub_graph is None:
            print('Could not resolve path \n{}'.format(path))
            return None

        rows = self.row[sub_graph.get(ITEM_KEY, ())]
        # rows = self.walkers[0].row[tuple(ints)]
        return FileRows(rows, path)

    def save(self, filename):

        return save_binary(
            (self.graph, self.name_list, self.kw),
            filename)

    def load(self, filename, return_new=True):
        d = load_binary(filename)
        if return_new:
            return DataWalker(d[0], d[1], **d[2])

        self.graph = d[0]
        self.name_list = d[1]
        self.kw = d[2]

        return self

    def __getitem__(self, key):
        """Return a sub key DataWalker. If the key is not a
        graph key, the value is used as a postion index for the items

        """
        return self.get_key(key)

    def get_key(self, key, convert_set=True, safe=None):
        try:
            dd = self.graph[key]
        except KeyError as e:
            dd = None
            if isinstance(key, int):
                return tuple(self.graph.items())[key]
            if safe is False:
                raise e
            if safe is True:
                return None

        if isinstance(dd, dict):
            return DataWalker(dd, parent=self.parent)

        if isinstance(dd, set):
            if convert_set:
                return tuple(dd)

        return dd

    @property
    def row(self):
        """Return a row index walker for easier getitem of namelist.
        """
        if self._row is None:
            self._row = Rows(self)
        return self._row

    def get_row(self, index):
        """Return a single row from the name_list or parent name_list chain
        """
        if self.name_list:
            return self.name_list[index]
        return self.parent.get_name_list()[index]

    def get_name_list(self):
        """Return the relevant name list for row values from an internal
        list or a parent name_list"""
        if self.name_list:
            return self.name_list
        return self.parent.get_name_list()

    def __getattr__(self, key):
        return self.__getitem__(key)

    def __repr__(self):
        return "<DataWalker '{}'>".format(self.graph.keys())


class Rows:

    def __init__(self, walker):
        self.walker = walker

    def __getitem__(self, index):
        if isinstance(index, (tuple, list, set)):
            # db[0].row[set(db[1].standard.font)]
            res = ()
            for item in index:
                res += (self.walker.get_row(item), )
            return res
        return self.walker.get_row(index)

    def __repr__(self):
        return '<Rows {}>'.format(len(self.walker.get_name_list() or ''))


class FileWalker(object):
    """Given the result from the scan and index, utilize the index
    items for an easier file walker.
    """
    def __init__(self, *walkers, files=None):
        self.walkers = walkers
        if files is not None:
            self.load(*files)

    def save(self, *filenames):
        res = ()
        for walker, filename in zip(self.walkers, filenames):
            res += (walker.save(filename), )
        return res

    def resolve(self, indexes):
        self.walkers[0].row[indexes]

    def load(self, *files):
        """Load each file in order of walker sequence
        """
        walkers = ()

        for _file in files:
            if isinstance(_file, str):
                # datawalker load
                walker = DataWalker().load(_file)
            # elif isinstance(_file, io.BufferedWriter):
            elif isinstance(_file, DataWalker):
                walker = file
            walkers += (walker,)
        self.walkers = walkers

    def __repr__(self):
        s = '' if len(self.walkers) == 1 else 's'
        return "<FileWalker of {} walker{}>".format(len(self.walkers), s)

    def get(self, key, case=False, indexes=False):
        """
        Return an index list of all int positions for the given key as
        FileRows instance.
        if indexes=True return a tuple, not a FileRows
        for a given key without an index, raise a KeyError
        """
        walker = self.walkers[1]
        words = walker['standard' if case else 'lower']

        try:
            ints = words.get_key(key, convert_set=False, safe=True)
            if indexes:
                return ints

            return FileRows(self.walkers[0].row[tuple(ints)], key)
        except KeyError as e:
            print('Key "{}" does not exist'.format(key))
            raise e

    def find(self, *keys):
        """ Return FileRows of discovered values given one or more
        string keys.

            find('three', 'blind', 'mice')

        Each keys index is insected with its neighbour returning a
        match for all keys in a filename.
        """
        res = ()
        for key in keys:
            res += (self.get(key, indexes=True), )

        if len(res) == 0:
            print('Nothing for "{}"'.format(res))
            return None

        intersect = res[0] or set()


        for key in res[1:]:
            try:
                intersect &= key
            except TypeError as e:
                print('intersect: {}'.format(intersect))
                print('key: {}'.format(key))
                if key is None:
                    continue
                raise e

        res = FileRows(self.walkers[0].row[tuple(intersect)], keys)
        print('Found {} file totaling {}'.format(len(res), res.size))
        return res

    def search(self, string):
        '''Like find but as a string'''
        return self.find(*string.split(' '))

    def files(self, path, sep=None):
        return self.walkers[0].path_files(path, sep)

    def top(self):
        return self.walkers[0].graph

    def dirs(self, directory):
        """Return FileRows for all files within the given directory.
        This includes the children by default.

            d=db.dirs('Two.and.a.Half.Men.COMPLETE.720p.WEB-DL.H.264')
            <FileRows 264 of "Two.and.a.Half.Men.COMPLETE.720p.WEB-DL.H.264">

        This utilized the _directories sub graph.
        """
        return self.walkers[0].dir_files(directory)



class FileRows(object):
    """A tuple containing a subset of scans from the graph rows or
    general load
    """
    def __init__(self, rows, header_name):
        self.rows = rows
        self.header_name = header_name

    def __getitem__(self, index):
        return FileItem(self.rows[index])

    def __len__(self):
        return len(self.rows)

    def __repr__(self):
        return '<FileRows {} of "{}">'.format(len(self.rows), self.header_name)

    @property
    def pp(self):
        """Print a list of file items using standard pprint
        """
        pp(tuple(self))

    @property
    def size(self):
        return self.total_size(True, True)

    def total_size(self, readable=False, small=False):
        """
        Return a sum of all bytes from the row files.
        if small is True (default), the return value is reduces
        to the nearest round major byte size: MB, GB, TB.
        provide small=False for a whole byte int.

            12.34

        If readable is True return a string with the postfix reduction
        type. 12.34mb

        _this function is backward... - by default it should return a byte_

        """
        v = sum((x[1] for x in self.rows))
        label = 'mb'
        if small:
            v = v / 1000 / 1000
            if v > 999:
                # GB
                label = 'gb'
                v = v / 1000
            if v > 999:
                # GB
                label = 'tb'
                v = v / 1000

            v = round(v, 2)

        if readable:
            return '{:,}{}'.format(v, label)

        return v


class FileItem(object):

    def __init__(self, asset):
        self.asset = asset
        self.name = os.path.basename(self.asset[0])
        self.path = os.path.dirname(self.asset[0])
        self.size = asset[1]
        self._date = asset[2]


    def __repr__(self):
        size = round(self.size / 1000 / 1000, 2)
        return '<File "{}" {}mb>'.format(self.name, size, self.path)



if __name__ == '__main__':
    db = main()

