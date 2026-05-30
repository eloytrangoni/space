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
            try { json j; file >> j; if (j.is_object()) db[json_path] = j; } catch (...) {}
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
    auto g = j["gabinete"];
    
    // Extraemos medidas reales del JSON
    double h = g["dimensiones_mm"]["alto"];
    double w = g["dimensiones_mm"]["ancho"];
    double sep = g["separacion_entre_gabinetes_mm"];
    
    // Coordenadas de puntos de anclaje
    double pf_x = g["coordenadas_mm"]["pivote_frontal"]["x"];
    double pf_y = g["coordenadas_mm"]["pivote_frontal"]["y"];
    
    py::list boxes;
    double cur_angle = bumper_tilt; 
    
    // Posición inicial: Bumper (asumimos el origen o bumper_height)
    double last_x = 0.0;
    double last_y = bumper_height;

    for(int i = 0; i < num_boxes; ++i) {
        if (i > 0) cur_angle += splays[i-1]; // Acumulamos Splay
        
        double rad = cur_angle * M_PI / 180.0;
        
        // La lógica de "eslabón": el pivote frontal de la caja N 
        // se une al punto de anclaje de la caja N-1
        double cur_x = last_x + (pf_x * std::cos(rad) - pf_y * std::sin(rad));
        double cur_y = last_y - (pf_x * std::sin(rad) + pf_y * std::cos(rad));
        
        // Empaquetado
        py::dict box; 
        box["x"] = cur_x; 
        box["y"] = cur_y; // Esta es la posición Y global
        box["angle"] = cur_angle;
        box["width"] = w;
        box["height"] = h;
        boxes.append(box);
        
        // Actualizamos last_x/y para la siguiente caja (pivote inferior)
        last_x = cur_x;
        last_y = cur_y - sep; 
    }
    return boxes;
}

PYBIND11_MODULE(motor_rigging, m) {
    m.def("calcular_geometria_rigging", &calcular_geometria_rigging);
    m.def("cargar_json_rigging", &cargar_json_rigging);
}