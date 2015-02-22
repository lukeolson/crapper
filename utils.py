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
        - multiples of the same type look like I1, I2, ...
        - in addition 'const' and 'void'
        - in addition operators of the form OP&
    """

    types = ['i', 'I', 't', 'T', 'F', 'R', 'S']

    with open(hfile, 'rU') as hfid:
        text = hfid.read()

    temp_iter = re.finditer('template\s*\<', text)
    temp_start = [m.start(0) for m in temp_iter]

    #ntemp = len(temp_start)
    classre = re.compile('template.*<(.+?)>')
    funcre = re.compile('template\s*<.*?>(.+?){', re.DOTALL)
    argsre = re.compile('(.+?)\s+(.+?)\s*\((.*?)\)', re.DOTALL)
    tidre = re.compile('([%s])' % ''.join(types) + '([0-9]+)')

    funcs = {}
    print('[parsing %s]' % hfile)
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
            atype.append(arg[0])

        funcs[funcname] = {'const': const, 'atype': atype, 'ret': funcret}
        print('\t[%s(...)]' % funcname)


if __name__ == '__main__':
    import os
    temps = os.listdir('./templates')
    example_templates = ['./templates/' + h for h in temps
                         if (h.startswith('example') and h.endswith('.h'))]
    for temp in example_templates:
        identify_template(temp)
