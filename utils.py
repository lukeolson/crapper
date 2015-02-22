import re


def identify_template(hfile):
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
          - i: int scalar
          - I: int array
          - t: data scalar
          - T: data array
        - in addition 'const' and 'void'
    """

    types = ['i', 'I', 't', 'T']

    with open(hfile, 'rU') as hfid:
        text = hfid.read()

    temp_iter = re.finditer('template\s*\<', text)
    temp_start = [m.start(0) for m in temp_iter]

    ntemp = len(temp_start)
    classre = re.compile('template.*<(.+)>')
    funcre = re.compile('template.*<.*>\s*(.+)\s*{')
    argsre = re.compile('(.+)\s+(.+)\s*\((.+)\)')

    funcs = {}
    print('[parsing %s]' % hfile)
    for tstart in temp_start:
        # class list
        classes = classre.search(text, tstart).groups(0)[0].strip()

        # function call
        funccall = funcre.search(text, tstart).groups(0)[0].strip()

        # check classes
        classes = re.sub('class', '', classes)
        classes = re.sub('\s', '', classes).split(',')
        for tid  in classes:
            if tid not in types:
                raise ValueError('class type \'%s\' not supported ' % tid +
                                 'in your header file %s' % hfile) 

        # get the function declaration
        m = argsre.match(funccall)
        funcret = m.group(1)
        funcname = m.group(2)
        funcargs = m.group(3)
        args = funcargs.split(',')
        const = []
        atype = []
        for arg in args:
            if 'const ' in arg:
                const.append(True)
            else:
                const.append(False)
            arg = arg.replace('const', '').strip()
            atype.append(arg[0])

        print('\t[%s(...)]' % funcname)


if __name__ == '__main__':
    identify_template('./templates/example.h')
