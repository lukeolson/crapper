#!/usr/bin/env python
"""
from
https://github.com/scipy/scipy/blob/master/scipy/sparse/generate_sparsetools.py
"""
import optparse
import os
from distutils.dep_util import newer
import utils

# List of the supported index typenums and the corresponding C++ types
I_TYPES = [
    ('NPY_INT32', 'npy_int32'),
    ('NPY_INT64', 'npy_int64'),
]

# List of the supported data typenums and the corresponding C++ types
T_TYPES = [
    ('NPY_BOOL', 'npy_bool_wrapper'),
    ('NPY_BYTE', 'npy_byte'),
    ('NPY_UBYTE', 'npy_ubyte'),
    ('NPY_SHORT', 'npy_short'),
    ('NPY_USHORT', 'npy_ushort'),
    ('NPY_INT', 'npy_int'),
    ('NPY_UINT', 'npy_uint'),
    ('NPY_LONG', 'npy_long'),
    ('NPY_ULONG', 'npy_ulong'),
    ('NPY_LONGLONG', 'npy_longlong'),
    ('NPY_ULONGLONG', 'npy_ulonglong'),
    ('NPY_FLOAT', 'npy_float'),
    ('NPY_DOUBLE', 'npy_double'),
    ('NPY_LONGDOUBLE', 'npy_longdouble'),
    ('NPY_CFLOAT', 'npy_cfloat_wrapper'),
    ('NPY_CDOUBLE', 'npy_cdouble_wrapper'),
    ('NPY_CLONGDOUBLE', 'npy_clongdouble_wrapper'),
]

# Code templates
THUNK_TEMPLATE = """
static Py_ssize_t %(name)s_thunk(int I_typenum, int T_typenum, void **a)
{
    %(thunk_content)s
}
"""

METHOD_TEMPLATE = """
NPY_VISIBILITY_HIDDEN PyObject *
%(name)s_method(PyObject *self, PyObject *args)
{
    return call_thunk('%(ret_spec)s', "%(arg_spec)s", %(name)s_thunk, args);
}
"""

GET_THUNK_CASE_TEMPLATE = """
static int get_thunk_case(int I_typenum, int T_typenum)
{
    %(content)s;
    return -1;
}
"""


# Code generation
def get_thunk_type_set():
    """
    Get a list containing cartesian product of data types,
    plus a getter routine.

    Returns
    -------
    i_types : list [(j, I_typenum, None, I_type, None), ...]
         Pairing of index type numbers and the corresponding C++ types,
         and an unique index `j`. This is for routines that are parameterized
         only by I but not by T.
    it_types : list [(j, I_typenum, T_typenum, I_type, T_type), ...]
         Same as `i_types`, but for routines parameterized both by T and I.
    getter_code : str
         C++ code for a function that takes I_typenum, T_typenum and returns
         the unique index corresponding to the lists, or -1 if no match was
         found.

    """
    i_types = []
    t_types = []
    it_types = []

    j = 0

    getter_code = "    if (0) {}"

    for I_typenum, I_type in I_TYPES + [(-1, -1)]:
        piece = """
        else if (I_typenum == %(I_typenum)s) {
            if (T_typenum == -1) { return %(j)s; }"""
        getter_code += piece % dict(I_typenum=I_typenum, j=j)

        if I_type is not -1:
            i_types.append((j, I_typenum, None, I_type, None))
        j += 1

        for T_typenum, T_type in T_TYPES:
            piece = """
            else if (T_typenum == %(T_typenum)s) { return %(j)s; }"""
            getter_code += piece % dict(T_typenum=T_typenum, j=j)

            if I_type is not -1:
                it_types.append((j, I_typenum, T_typenum, I_type, T_type))
            else:
                t_types.append((j, None, T_typenum, None, T_type))
            j += 1

        getter_code += """
        }"""

    gtcstr = GET_THUNK_CASE_TEMPLATE % dict(content=getter_code)
    return i_types, t_types, it_types, gtcstr


def parse_routine(name, args, types):
    """
    Generate thunk and method code for a given routine.

    Parameters
    ----------
    name : str
        Name of the C++ routine
    args : str
        Argument list specification in format:
        'i':  integer scalar
        'I':  integer array
        'T':  data array
        '*':  indicates that the next argument is an output argument
        'v':  void

        e.g. vITT*T  for
             void axpy(const I n, const T a, const T * x, T * y)
    types : list
        List of types to instantiate, as returned `get_thunk_type_set`

    """

    ret_spec = args[0]
    arg_spec = args[1:]

    def get_arglist(I_type, T_type):
        """
        Generate argument list for calling the C++ function
        """
        args = []
        next_is_writeable = False
        j = 0
        for t in arg_spec:
            const = '' if next_is_writeable else 'const '
            next_is_writeable = False
            if t == '*':
                next_is_writeable = True
                continue
            elif t == 'i':
                args.append("*(%s*)a[%d]" % (const + I_type, j))
            elif t == 'I':
                args.append("(%s*)a[%d]" % (const + I_type, j))
            elif t == 'T':
                args.append("(%s*)a[%d]" % (const + T_type, j))
            elif t == 'B':
                args.append("(npy_bool_wrapper*)a[%d]" % (j,))
            elif t == 'V':
                if const:
                    raise ValueError("'V' argument must be an output arg")
                args.append("(std::vector<%s>*)a[%d]" % (I_type, j,))
            elif t == 'W':
                if const:
                    raise ValueError("'W' argument must be an output arg")
                args.append("(std::vector<%s>*)a[%d]" % (T_type, j,))
            else:
                raise ValueError("Invalid spec character %r" % (t,))
            j += 1
        return ", ".join(args)

    # Generate thunk code: a giant switch statement with different
    # type combinations inside.
    thunk_content = """int j = get_thunk_case(I_typenum, T_typenum);
    switch (j) {"""
    for j, I_typenum, T_typenum, I_type, T_type in types:
        arglist = get_arglist(I_type, T_type)
        if T_type is None:
            dispatch = "%s" % (I_type,)
        else:
            dispatch = "%s,%s" % (I_type, T_type)
        if 'B' in arg_spec:
            dispatch += ",npy_bool_wrapper"

        piece = """
        case %(j)s:"""
        if ret_spec == 'v':
            piece += """
            (void)%(name)s<%(dispatch)s>(%(arglist)s);
            return 0;"""
        else:
            piece += """
            return %(name)s<%(dispatch)s>(%(arglist)s);"""
        thunk_content += piece % dict(j=j, I_type=I_type, T_type=T_type,
                                      I_typenum=I_typenum, T_typenum=T_typenum,
                                      arglist=arglist, name=name,
                                      dispatch=dispatch)

    thunk_content += """
    default:
        throw std::runtime_error("internal error: invalid argument typenums");
    }"""

    thunk_code = THUNK_TEMPLATE % dict(name=name,
                                       thunk_content=thunk_content)

    # Generate method code
    method_code = METHOD_TEMPLATE % dict(name=name,
                                         ret_spec=ret_spec,
                                         arg_spec=arg_spec)

    return thunk_code, method_code


def main(hfilelist, hfiledir):
    """
    Parameters
    ----------
        hfilelist: array of strings
            List of .h files that containt templates

        hfiledir: string
            Relative path to hfilelist

    Notes
    -----
        - Gets all combinations of I and T through get_thunk_type_set
        - Idetifies templates with utils.identify_templates
        - Creates a call for every combination with parse_routines
        - Wrties these calls to *_impl.h
        - Adds these headers to sparsetoos_impl.h
    """
    p = optparse.OptionParser(usage=__doc__.strip())
    p.add_option("--no-force", action="store_false",
                 dest="force", default=True)
    options, args = p.parse_args()

    names = []

    i_types, t_types, it_types, getter_code = get_thunk_type_set()

    # Generate *_impl.h for each header
    for hfile in hfilelist:
        funcs = utils.identify_templates(os.path.join(hfiledir, hfile))

        # Produce output
        dst = os.path.join(os.path.dirname(__file__), hfiledir,
                           hfile.replace('.h', '') + '_impl.h')

        if not newer(__file__, dst) or not options.force:
            print("[generate_functions] %r already up-to-date" % (dst,))
        else:
            print("[generate_functions] generating %r" % (dst,))

            thunks = []
            methods = []
            for func in funcs:
                name = func['func']
                args = func['spec']
                if ('i' in args or 'I' in args) and\
                        ('t' in args or 'T' in args):
                    thunk, method = parse_routine(name, args, it_types)
                elif ('i' in args or 'I' in args):
                    thunk, method = parse_routine(name, args, i_types)
                elif ('t' in args or 'T' in args):
                    thunk, method = parse_routine(name, args, t_types)

            if name in names:
                raise ValueError("Duplicate routine %r" % (name,))

            names.append(name)
            thunks.append(thunk)
            methods.append(method)

            with open(dst, 'w') as f:
                f.write('/* File autogenerated by generate_functions.py' +
                        ' * Do not edit manually or check into VCS.' +
                        '*/')
                f.write(getter_code)
                for thunk in thunks:
                    f.write(thunk)
                for method in methods:
                    f.write(method)

    # Generate code for method struct
    method_defs = ""
    for name in names:
        method_defs += "NPY_VISIBILITY_HIDDEN PyObject *%s_method(PyObject *, PyObject *);\n" % (name,)

    method_struct = """\nstatic struct PyMethodDef sparsetools_methods[] = {"""
    for name in names:
        method_struct += "\n\t{\"%(name)s\", (PyCFunction)%(name)s_method, METH_VARARGS, NULL}," % dict(name=name)
    method_struct += "\n\t{NULL, NULL, 0, NULL}"
    method_struct += '\n};'

    # Produce sparsetools_impl.h
    dst = os.path.join(os.path.dirname(__file__),
                       'base',
                       'sparsetools_impl.h')

    if not newer(__file__, dst) or not options.force:
        print("[generate_functions] %r already up-to-date" % (dst,))
    else:
        print("[generate_functions] generating %r" % (dst,))
        with open(dst, 'w') as f:
            f.write('/* File autogenerated by generate_functions.py' +
                    ' * Do not edit manually or check into VCS.' +
                    '*/')
            f.write(method_defs)
            f.write(method_struct)

if __name__ == "__main__":
    temps = os.listdir('./templates')
    example_templates = [h for h in temps
                         if (h.startswith('example') and h.endswith('.h'))]
    example_templates = ['example.h']
    main(example_templates, './templates/')