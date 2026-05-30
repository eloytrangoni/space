#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <cmath>
#include <vector>
#include <string>
#include <fstream>
#include <unordered_map>
#include <map>
#include "json.hpp"
#include "MotorSpaceRigging.hpp"

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

namespace py = pybind11;
using json = nlohmann::json;

PYBIND11_MODULE(motor_rigging, m) {
    m.doc() = "Motor Rigging Mecánico - Elo Acoustics";
    
    m.def("calcular_geometria_rigging", &calcular_geometria_rigging,
          "Calcula la geometría del arreglo de cajas");
    m.def("cargar_json_rigging", &cargar_json_rigging,
          "Carga archivo JSON de configuración");
    m.def("calcular_metricas_sistema", &calcular_metricas_sistema,
          "Calcula métricas del sistema (peso, longitud, clearance)");
}
