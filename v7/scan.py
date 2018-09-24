'''
Scan functionaity for files and folders
'''

from scandir import scandir, GenericDirEntry
from multiprocessing import Pool
import multiprocessing
import time
import os
import errno

CPU_COUNT = multiprocessing.cpu_count()

def make_tests():

    rp = './tests/fixtures/folders/'
    letters = 'abcdefghij'

    for x in letters:
        try:
            os.makedirs(os.path.join(rp, x))
        except Exception:
            pass

    for p, folders, sets in os.walk(rp):

        for foldername in folders:
            subp = os.path.join(rp, foldername)
            print( subp)
            for x in letters:
                nfn = '{}{}'.format(x, x)
                p = os.path.join(subp, nfn)
                print( p)

                try:
                    os.makedirs(p)
                    for n in letters:
                        fn = 'file-{}-{}.txt'.format(nfn, n)
                        fp = os.path.join(p, fn)
                        with open(fp, 'a') as f:
                            f.write('write')
                    print( 'made', p)
                except Exception:
                    print( 'failed', p)


def scan(dirs, recurse=True, ignore=None):
    '''
    Scan the list of directories, recursing if True.
    'Ignore' defines a list of absolute path of folder to omit from
    the recursive scan.
    '''
    print( '.' , len(dirs),)

    if len(dirs) < CPU_COUNT:
        _files, _folders, _errors = scan_func_many(dirs, ignore=ignore)
        sets = ( ('', _files, _folders, _errors), )
    else:
        sets = pool_scan(scan_func, dirs, ignore=ignore)

    files = tuple()
    folders = tuple()
    errors = []

    for folderset in sets:
        fpath, _files, _folders, _errors = folderset

        folders += _folders
        files += _files
        errors.extend(_errors)

    if len(folders) > 0 and recurse is True:
        if len(folders) < CPU_COUNT:
            sub_files, sub_folders, sub_errors = scan_func_many(folders, ignore=ignore)
        else:
            sub_files, sub_folders, sub_errors = scan(folders, ignore=ignore)

        folders += sub_folders
        files += sub_files
        errors.extend(sub_errors)

    return files, folders, errors


def scan_func_many(dirs, ignore=None):
    '''
    Iterate each given directory using the scan_func.
    Return (files, folders, errors) of all directories
    '''
    files = tuple()
    folders = tuple()
    errors = []

    for x in dirs:

        _, _files, _folders, _errors = scan_func(x, ignore=ignore)

        files += _files
        folders += _folders
        errors.extend(_errors)

    return files, folders, errors


def scan_func(fpath, ignore=None):
    # rand = random.randint(0, 60) + (random.random() * 1)

    files = tuple()
    folders = tuple()
    errors = []
    ignore = ignore or []

    # print( fpath)
    scan = []
    try:
        scan = scandir("{}".format(fpath))
    except OSError as e:
        errors.append( (e.errno, fpath,))
        # if e.errno == errno.EIO:
        #     print( 'x',)
        # elif e.errno == 3:
        #     # cannot find
        #     print( '?',)
        # else:
        #     print( 'Scanfunc error', e.errno, str(e), '\n')
    except Exception as e:
        print( 'Scanfunc error', type(e), str(e), '\n')

    for entry in scan:

        if entry.is_dir():
            folders += (entry.path, )
            continue

        st = entry.stat()
        entry = (entry.path, entry.name, st.st_size, st.st_ctime)
        files += (entry, )


    return fpath, files, folders, errors


def pool_scan(f, sequence, ignore=None):

    pool = Pool(processes=CPU_COUNT)
    #from multiprocessing.dummy import Pool
    #pool = Pool(16)

    result = []
    for item in sequence:
        itemv = f(item)
        result.append(itemv)

    # result = pool.map(f, sequence)

    pool.close()
    pool.join()

    return result

