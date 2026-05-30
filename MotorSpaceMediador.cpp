#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <string>
#include <vector>
#include <cmath>
#include <map>
#include "MotorSpaceRigging.hpp"

namespace py = pybind11;

class MediadorCache {
private:
    std::string last_json = "";
    int last_cajas = 0;
    double last_h_bumper = -999.0;
    double last_tilt = -999.0;
    std::vector<double> last_splays;
    py::list last_geometria;

    // Instancia del motor de Rigging
    MotorSpaceRigging motor_rigging;

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

    // Patrón "Dirty Flag" para detectar cambios
    bool requiere_recalculo_rigging(std::string json, int cajas, double h, double tilt, std::vector<double> splays) {
        bool cambio = false;
        
        if (json != last_json || cajas != last_cajas || 
            !double_equals(h, last_h_bumper) || 
            !double_equals(tilt, last_tilt) || 
            !vector_equals(splays, last_splays)) {
            cambio = true;
        }

        if (cambio) {
            last_json = json;
            last_cajas = cajas;
            last_h_bumper = h;
            last_tilt = tilt;
            last_splays = splays;
        }

        return cambio;
    }

    // FUNCIÓN PUENTE: Obtiene o calcula geometría
    py::list obtener_o_calcular_rigging(std::string json, int cajas, double h, double tilt, std::vector<double> splays) {
        if (requiere_recalculo_rigging(json, cajas, h, tilt, splays)) {
            last_geometria = motor_rigging.calcularArreglo(json, cajas, h, tilt, splays);
        }
        return last_geometria;
    }

    void guardar_geometria(py::list geo) { 
        last_geometria = geo; 
    }
    
    py::list obtener_geometria() { 
        return last_geometria; 
    }
};

PYBIND11_MODULE(motor_mediador, m) {
    m.doc() = "Motor Mediador de Estado y Caché - Elo Acoustics";
    py::class_<MediadorCache>(m, "MediadorCache")
        .def(py::init<>())
        .def("obtener_o_calcular_rigging", &MediadorCache::obtener_o_calcular_rigging)
        .def("requiere_recalculo_rigging", &MediadorCache::requiere_recalculo_rigging)
        .def("guardar_geometria", &MediadorCache::guardar_geometria)
        .def("obtener_geometria", &MediadorCache::obtener_geometria);
}
