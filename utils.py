def identify_template(hfile):
    """
    parameters
    ==========
    hfile : string
        .h header file to be parsed

    returns
    =======
    tdict : dictionary
        dictionary of lists
        each dictionary is a function
        each list identifies the arglist
    """
