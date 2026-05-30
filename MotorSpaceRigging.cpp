#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <cmath>
#include <vector>
#include <string>
#include <fstream>
#include <unordered_map>
#include <algorithm>
#include "json.hpp"

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

namespace py = pybind11;
using json = nlohmann::json;

// --- Gestor de Base de Datos ---
std::unordered_map<std::string, json>& get_db_rigging() {
    static std::unordered_map<std::string, json> instance;
    return instance;
}

void cargar_json_rigging(const std::string& json_path) {
    auto& db = get_db_rigging();
    if (db.find(json_path) == db.end()) {
        std::ifstream file(json_path);
        if (file.is_open()) {
            try { 
                json j; 
                file >> j; 
                if (j.is_object()) db[json_path] = j; 
            } catch (...) {}
        }
    }
}

// ---------------------------------------------------------------------------------
// FUNCIÓN DE CÁLCULO MECÁNICO: POSICIÓN DE CADA GABINETE (ESLABONES)
// ---------------------------------------------------------------------------------
py::list calcular_geometria_rigging(const std::string& json_path, int num_boxes, double bumper_height, double bumper_tilt, const std::vector<double>& splays) {
    auto& db = get_db_rigging();
    if (db.find(json_path) == db.end()) cargar_json_rigging(json_path);
    
    json j = db[json_path];
    
    // Extraemos medidas reales del JSON (convertir de mm a metros)
    double h = j["gabinete"]["dimensiones_mm"]["alto"].get<double>() / 1000.0;
    double w = j["gabinete"]["dimensiones_mm"]["ancho"].get<double>() / 1000.0;
    double sep = j["gabinete"]["separacion_entre_gabinetes_mm"].get<double>() / 1000.0;
    
    // Coordenadas de puntos de anclaje (en mm, convertir a metros)
    double pf_x = j["gabinete"]["coordenadas_mm"]["pivote_frontal"]["x"].get<double>() / 1000.0;
    double pf_y = j["gabinete"]["coordenadas_mm"]["pivote_frontal"]["y"].get<double>() / 1000.0;
    
    py::list boxes;
    double cur_angle = bumper_tilt; 
    
    // Posición inicial: Bumper
    double last_x = 0.0;
    double last_z = bumper_height;

    for(int i = 0; i < num_boxes; ++i) {
        if (i > 0 && i - 1 < splays.size()) cur_angle += splays[i-1]; // Acumulamos Splay
        
        double rad = cur_angle * M_PI / 180.0;
        
        // La lógica de "eslabón": el pivote frontal de la caja N 
        // se une al punto de anclaje de la caja N-1
        double cur_x = last_x + (pf_x * std::cos(rad) - pf_y * std::sin(rad));
        double cur_z = last_z - (pf_x * std::sin(rad) + pf_y * std::cos(rad));
        
        // Empaquetado en diccionario Python
        py::dict box; 
        box["x"] = cur_x; 
        box["y"] = 0.0;  // Centro del altavoz (eje horizontal)
        box["z"] = cur_z; // Altura
        box["angle"] = cur_angle;
        box["width"] = w;
        box["height"] = h;
        boxes.append(box);
        
        // Actualizamos last_x/z para la siguiente caja (pivote inferior)
        last_x = cur_x;
        last_z = cur_z - sep; 
    }
    return boxes;
}

// ---------------------------------------------------------------------------------
// FUNCIÓN DE CÁLCULO DE MÉTRICAS DEL SISTEMA
// ---------------------------------------------------------------------------------
py::dict calcular_metricas_sistema(const std::string& json_path, int num_boxes, const py::list& geometria) {
    auto& db = get_db_rigging();
    if (db.find(json_path) == db.end()) cargar_json_rigging(json_path);
    
    json j = db[json_path];
    
    // Peso por gabinete
    double peso_por_caja = j["gabinete"]["peso"].get<double>();
    double peso_total = peso_por_caja * num_boxes;
    
    // Medidas del gabinete
    double h = j["gabinete"]["dimensiones_mm"]["alto"].get<double>() / 1000.0;
    double sep = j["gabinete"]["separacion_entre_gabinetes_mm"].get<double>() / 1000.0;
    
    // Calcular dimensiones del arreglo curvado
    double max_z = -999.0;
    double min_z = 999.0;
    double max_x = -999.0;
    double min_x = 999.0;
    
    for (size_t i = 0; i < py::len(geometria); ++i) {
        py::dict box = geometria[i].cast<py::dict>();
        double bx = box["x"].cast<double>();
        double bz = box["z"].cast<double>();
        
        max_z = std::max(max_z, bz);
        min_z = std::min(min_z, bz);
        max_x = std::max(max_x, bx);
        min_x = std::min(min_x, bx);
    }
    
    // Longitud total del arreglo (considerando altura de los gabinetes)
    double longitud_arreglo = num_boxes > 0 ? max_z - min_z + h : 0.0;
    
    // Clearance del suelo (altura mínima del arreglo sobre el suelo)
    double clearance = min_z;
    
    py::dict metricas;
    metricas["peso_total"] = peso_total;
    metricas["longitud_arreglo"] = longitud_arreglo;
    metricas["clearance"] = clearance;
    metricas["num_boxes"] = num_boxes;
    metricas["max_z"] = max_z;
    metricas["min_z"] = min_z;
    metricas["max_x"] = max_x;
    metricas["min_x"] = min_x;
    
    return metricas;
}

PYBIND11_MODULE(motor_rigging, m) {
    m.doc() = "Motor de Rigging - Cálculo de Geometría y Métricas del Sistema - Elo Acoustics";
    m.def("calcular_geometria_rigging", &calcular_geometria_rigging, "Calcula la geometría de las cajas basado en rigging");
    m.def("calcular_metricas_sistema", &calcular_metricas_sistema, "Calcula métricas del sistema como peso y clearance");
    m.def("cargar_json_rigging", &cargar_json_rigging, "Carga archivo JSON de rigging en caché");
}
