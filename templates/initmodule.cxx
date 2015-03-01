#include <Python.h>
#include "crappy.h"

extern "C" {

#include "crappy_impl.h"

#if PY_VERSION_HEX >= 0x03000000
static struct PyModuleDef moduledef = {
    PyModuleDef_HEAD_INIT,
    "crappy",
    NULL,
    -1,
    crappy_methods,
    NULL,
    NULL,
    NULL,
    NULL
};

PyObject *PyInit_crappy(void)
{
    PyObject *m;
    m = PyModule_Create(&moduledef);
    import_array();
    return m;
}
#else
PyMODINIT_FUNC initcrappy(void) {
    PyObject *m;
    m = Py_InitModule("crappy", crappy_methods);
    import_array();
    if (m == NULL) {
        Py_FatalError("can't initialize module crappy");
    }
}
#endif

}
