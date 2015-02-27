#ifndef CRAPPY_H
#define CRAPPY_H

#define PY_ARRAY_UNIQUE_SYMBOL _crappy
#define NPY_NO_DEPRECATED_API NPY_1_7_API_VERSION
#include <Python.h>
#include "numpy/arrayobject.h"

#include <stdexcept>

#include "bool_ops.h"
#include "complex_ops.h"

typedef Py_ssize_t thunk_t(int I_typenum, int T_typenum, void **args);

NPY_VISIBILITY_HIDDEN PyObject *
call_thunk(char ret_spec, const char *spec, thunk_t *thunk, PyObject *args);

#endif
