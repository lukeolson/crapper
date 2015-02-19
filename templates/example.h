// y += a*x
template <class I, class T>
void axpy(const I n, const T a, const T * x, T * y){
    for(I i = 0; i < n; i++){
        y[i] += a * x[i];
    }
}
