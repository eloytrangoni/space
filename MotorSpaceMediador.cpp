#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <string>
#include <vector>
#include <cmath>
#include <map>

namespace py = pybind11;

class MediadorCache {
private:
    std::string last_json = "";
    int last_cajas = 0;
    double last_h_bumper = -999.0;
    double last_tilt = -999.0;
    std::vector<double> last_splays;
    py::list last_geometria;

    // Función auxiliar para comparar doubles con tolerancia
    bool double_equals(double a, double b, double epsilon = 1e-4) const {
        return std::abs(a - b) < epsilon;
    }

    // Comparación de vectores de splays
    bool vector_equals(const std::vector<double>& a, const std::vector<double>& b, double epsilon = 1e-4) const {
        if (a.size() != b.size()) return false;
        for (size_t i = 0; i < a.size(); ++i) {
            if (!double_equals(a[i], b[i], epsilon)) return false;
        }
        return true;
    }

public:
    MediadorCache() {}

    // Patrón "Dirty Flag" para detectar cambios en parámetros mecánicos
    bool requiere_recalculo_rigging(std::string json, int cajas, double h, double tilt, std::vector<double> splays) {
        bool cambio = false;
        
        // Detecta si algún parámetro cambió
        if (json != last_json || cajas != last_cajas || 
            !double_equals(h, last_h_bumper) || 
            !double_equals(tilt, last_tilt) || 
            !vector_equals(splays, last_splays)) {
            cambio = true;
        }

        // Actualiza caché si hay cambio
        if (cambio) {
            last_json = json;
            last_cajas = cajas;
            last_h_bumper = h;
            last_tilt = tilt;
            last_splays = splays;
        }

        return cambio;
    }

    // Guardar geometría calculada
    void guardar_geometria(py::list geo) { 
        last_geometria = geo; 
    }
    
    // Obtener geometría en caché
    py::list obtener_geometria() { 
        return last_geometria; 
    }

    // Obtener estado completo de caché (para debugging)
    py::dict obtener_estado_cache() {
        py::dict estado;
        estado["last_json"] = last_json;
        estado["last_cajas"] = last_cajas;
        estado["last_h_bumper"] = last_h_bumper;
        estado["last_tilt"] = last_tilt;
        estado["last_splays"] = last_splays;
        return estado;
    }
};

PYBIND11_MODULE(motor_mediador, m) {
    m.doc() = "Motor Mediador - Orquestador de Estado y Caché - Elo Acoustics";
    
    py::class_<MediadorCache>(m, "MediadorCache")
        .def(py::init<>())
        .def("requiere_recalculo_rigging", &MediadorCache::requiere_recalculo_rigging,
             "Verifica si los parámetros mecánicos cambiaron")
        .def("guardar_geometria", &MediadorCache::guardar_geometria,
             "Guarda geometría en caché")
        .def("obtener_geometria", &MediadorCache::obtener_geometria,
             "Obtiene geometría guardada en caché")
        .def("obtener_estado_cache", &MediadorCache::obtener_estado_cache,
             "Obtiene estado actual de la caché para debugging");
}
