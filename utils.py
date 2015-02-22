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

    with open(hfile, 'rU') as hfid:
        text = hfid.read()

    temp_iter = re.finditer('template\s*\<', text)
    temp_start = [m.start(0) for m in temp_iter]

    ntemp = len(temp_start)
    re.compile('.*<\s*class\s*([A-Z,a-z]+)
