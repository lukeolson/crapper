import re
import numpy as np


def identify_templates(hfile):
    """
    Parameters
    ----------
    hfile : string
        .h header file to be parsed

    Returns
    -------
    tdict : dictionary
        dictionary of lists
        each dictionary is a function
        each list identifies the arglist

    Notes
    -----
    The header looks for

    template <class I, class T>
    void myfunc(const I n, const T a, const T * x, T * y){
    ...
    }

    rules:
        - 'template' identifies the start of a templated function
        - the argument list is limited to
          - I: int array
          - T: data array
        - if *, then pointer type
          else, scalar
        - multiples of the same type look like I1, I2, ...
        - in addition 'const' and 'void'
        - in addition operators of the form OP&
        - then it makes i, I, t, T, depending on type
    """

    types = ['i', 'I', 't', 'T']

    with open(hfile, 'rU') as hfid:
        text = hfid.read()

    temp_iter = re.finditer('template\s*\<', text)
    temp_start = [m.start(0) for m in temp_iter]

    docst_iter = re.finditer(r'//\s*begin{docstring}', text)
    docst_start = [m.start(0) for m in docst_iter]
    docst_iter = re.finditer(r'//\s*end{docstring}', text)
    docst_end = [m.start(0) for m in docst_iter]

    # check begin and end docstrings
    if len(docst_start) != len(docst_end):
        raise ValueError('Problem with docstring begin{docstring} ' +
                         'or end{docstring}')

    # each docstring is associated with some template
    # each template is not associated with some docstring
    # associate the templates with docstring if possible (from docstrong POV)
    temp_start = np.array(temp_start)
    docst = ['' for t in range(len(temp_start))]
    cppcomment = re.compile('^//')

    for ms, me in zip(docst_start, docst_end):
        if ms >= me:
            raise ValueError('Problem with docstring begin{docstring} ' +
                             'or end{docstring}')
        docid = np.where(ms < temp_start)[0][0]
        docstring = text[ms:me].splitlines()
        pdocstring = []
        for d in docstring[1:]:  # not the first line
            pdocstring.append(cppcomment.sub('', d))
        docst[docid] = '\n'.join(pdocstring)

    classre = re.compile('template.*<(.+?)>')
    funcre = re.compile('template\s*<.*?>(.+?){', re.DOTALL)
    argsre = re.compile('(.+?)\s+(.+?)\s*\((.*?)\)', re.DOTALL)
    tidre = re.compile('([%s])' % ''.join(types) + '([0-9]+)')

    funcs = []
    print('[identify_templates] ...parsing %s' % hfile)
    k = 0
    for tstart in temp_start:
        # class list
        classes = classre.search(text, tstart).group(1).strip()

        # function call
        funccall = funcre.search(text, tstart).group(1).strip()

        # check classes
        classes = re.sub('class', '', classes)
        classes = re.sub('typename', '', classes)
        classes = re.sub('\s', '', classes).split(',')
        for tid in classes:
            if len(tid) == 1:
                thistype = tid
            else:
                m = tidre.match(tid)
                thistype = m.group(1).strip()
                thisnum = m.group(2).strip()
                del thisnum

            if thistype not in types:
                raise ValueError('class type \'%s\' not supported' % thistype +
                                 ' in your header file %s' % hfile)

        # get the function declaration
        m = argsre.match(funccall)
        funcret = m.group(1).strip()
        funcname = m.group(2).strip()
        funcargs = m.group(3).strip()
        args = funcargs.split(',')

        # mark args, const, type
        if len(args[0]) == 0:
            args = []
        const = []
        atype = []
        for arg in args:
            if 'const ' in arg:
                const.append(True)
            else:
                const.append(False)
            arg = arg.replace('const', '').strip()
            if ('*' in arg) or ('[]' in arg):
                atype.append(arg[0].upper())
            else:
                atype.append(arg[0].lower())

        if funcret == 'void':
            spec = 'v'
        else:
            spec = funcret
        for c, t in zip(const, atype):
            if c:
                spec += t
            else:
                spec += '*' + t

        funcs.append({'func': funcname, 'const': const, 'atype': atype,
                      'ret': funcret, 'spec': spec,
                      'docstring': docst[k]})
        print('\t...found %s(...)' % funcname)
        k += 1
    return funcs


if __name__ == '__main__':
    import sys
    if len(sys.argv) == 1:
        import os
        temps = os.listdir('./templates')
        example_templates = [h for h in temps
                             if (h.startswith('example') and h.endswith('.h'))]
        example_templates = ['example.h']
        funcs = identify_templates(example_templates, './templates/')
    else:
        f = sys.argv[1]
        funcs = identify_templates(f)
        for func in funcs:
            print(func['func'])
            print('     %s' % func['spec'])
