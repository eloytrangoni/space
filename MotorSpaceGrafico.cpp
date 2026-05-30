#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <cmath>
#include <algorithm>
#include <stdexcept>
#include <omp.h>

namespace py = pybind11;

inline void valor_a_color(double valor, double min_val, double max_val, uint8_t& r, uint8_t& g, uint8_t& b) {
    double rango = max_val - min_val;
    if (rango <= 0) rango = 1.0; 
    
    double v = (valor - min_val) / rango;
    v = std::max(0.0, std::min(1.0, v));
    
    r = static_cast<uint8_t>(std::max(0.0, std::min(255.0, 255.0 * std::min(1.0, std::max(0.0, 1.5 - std::abs(4.0 * v - 3.0))))));
    g = static_cast<uint8_t>(std::max(0.0, std::min(255.0, 255.0 * std::min(1.0, std::max(0.0, 1.5 - std::abs(4.0 * v - 2.0))))));
    b = static_cast<uint8_t>(std::max(0.0, std::min(255.0, 255.0 * std::min(1.0, std::max(0.0, 1.5 - std::abs(4.0 * v - 1.0))))));
}

py::array_t<uint8_t> renderizar_mapa_colores(py::array_t<double, py::array::c_style | py::array::forcecast> spl_matrix, double min_db, double max_db) {
    
    py::buffer_info buf_spl = spl_matrix.request();
    
    // BARRERA CRÍTICA: Bloquea cualquier petición de memoria absurda
    if (buf_spl.ndim != 2) {
        throw std::runtime_error("El Motor Gráfico requiere una matriz 2D. Se recibio ndim: " + std::to_string(buf_spl.ndim));
    }
    
    double* ptr_spl = static_cast<double*>(buf_spl.ptr);
    int alto = buf_spl.shape[0]; 
    int ancho = buf_spl.shape[1];
    
    auto result = py::array_t<uint8_t>({alto, ancho, 4});
    py::buffer_info buf_res = result.request();
    uint8_t* ptr_img = static_cast<uint8_t*>(buf_res.ptr);

    py::gil_scoped_release release;
    
    #pragma omp parallel for
    for (int i = 0; i < alto; ++i) {
        for (int j = 0; j < ancho; ++j) {
            double spl = ptr_spl[i * ancho + j];
            int pixel_idx = (i * ancho + j) * 4;
            
            if (spl < (min_db - 10.0) || spl <= 0.1) {
                ptr_img[pixel_idx] = 0;     
                ptr_img[pixel_idx + 1] = 0; 
                ptr_img[pixel_idx + 2] = 0; 
                ptr_img[pixel_idx + 3] = 0; 
            } else {
                uint8_t r, g, b; 
                valor_a_color(spl, min_db, max_db, r, g, b);
                ptr_img[pixel_idx] = r;     
                ptr_img[pixel_idx + 1] = g; 
                ptr_img[pixel_idx + 2] = b; 
                ptr_img[pixel_idx + 3] = 200; 
            }
        }
    }
    
    return result;
}

PYBIND11_MODULE(motor_grafico, m) {
    m.doc() = "Motor Grafico C++ Optimizado OpenMP - Elo Acoustics";
    m.def("renderizar_mapa_colores", &renderizar_mapa_colores);
}