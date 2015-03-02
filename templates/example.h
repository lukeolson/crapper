// begin{docstring}
//
// Perform a BLAS-2 AXPY: y = a * x + y
//
// Parameters
// ----------
// n : array length
//     length of arrays x and y
// a : scalar
//     scalar for multiplication
// x : numpy array
//     vector x
// y : numpy array (overwritten)
//     vector y
//
// Examples
// --------
// >>> x = numpy.array([1.0, 2, 3])
// >>> y = numpy.array([2.0, 2, 2])
// >>> a = 4.4
// >>> n = 3
// >>> axpy(n, a, x, y)
// end{docstring}
//
// y += a*x
template <class I, class T>
void axpy(const I n, const T a, const T * x, T * y){
    for(I i = 0; i < n; i++){
        y[i] += a * x[i];
    }
}
