#pragma once

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <cmath>
#include <vector>
#include <string>
#include <fstream>
#include <unordered_map>
#include "json.hpp"

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

namespace py = pybind11;
using json = nlohmann::json;

// --- Gestor de Base de Datos ---
inline std::unordered_map<std::string, json>& get_db_rigging() {
    static std::unordered_map<std::string, json> instance;
    return instance;
}

inline void cargar_json_rigging(const std::string& json_path) {
    auto& db = get_db_rigging();
    if (db.find(json_path) == db.end()) {
        std::ifstream file(json_path);
        if (file.is_open()) {
            try { json j; file >> j; if (j.is_object()) db[json_path] = j; } catch (...) {}
        }
    }
}

// Clase Motor de Rigging para usar dentro de Mediador
class MotorSpaceRigging {
public:
    // FUNCIÓN DE CÁLCULO MECÁNICO: POSICIÓN DE CADA GABINETE
    py::list calcularArreglo(const std::string& json_path, int num_boxes, double bumper_height, double bumper_tilt, const std::vector<double>& splays) {
        auto& db = get_db_rigging();
        if (db.find(json_path) == db.end()) cargar_json_rigging(json_path);
        
        json j = db[json_path];
        auto g = j["gabinete"];
        
        // Extraemos medidas reales del JSON
        double h = g["dimensiones_mm"]["alto"];
        double w = g["dimensiones_mm"]["ancho"];
        double sep = g.value("separacion_entre_gabinetes_mm", 10.0);
        
        // Coordenadas de puntos de anclaje
        double pf_x = g["coordenadas_mm"]["pivote_frontal"]["x"];
        double pf_y = g["coordenadas_mm"]["pivote_frontal"]["y"];
        
        py::list boxes;
        double cur_angle = bumper_tilt; 
        
        // Posición inicial: Bumper
        double last_x = 0.0;
        double last_z = bumper_height;

        for(int i = 0; i < num_boxes; ++i) {
            if (i > 0 && i-1 < (int)splays.size()) cur_angle += splays[i-1]; // Acumulamos Splay
            
            double rad = cur_angle * M_PI / 180.0;
            
            // Cinemática: pivote frontal se une al punto anterior
            double cur_x = last_x + (pf_x * std::cos(rad) - pf_y * std::sin(rad)) / 1000.0;
            double cur_z = last_z - (pf_x * std::sin(rad) + pf_y * std::cos(rad)) / 1000.0;
            
            // Empaquetado en dict de Python
            py::dict box; 
            box["x"] = cur_x; 
            box["z"] = cur_z;
            box["angle"] = cur_angle;
            box["width"] = w / 1000.0;
            box["height"] = h / 1000.0;
            boxes.append(box);
            
            // Actualizamos para la siguiente caja
            last_x = cur_x;
            last_z = cur_z - (sep / 1000.0);
        }
        return boxes;
    }
};

// Funciones independientes para el módulo C++
inline py::list calcular_geometria_rigging(const std::string& json_path, int num_boxes, double bumper_height, double bumper_tilt, const std::vector<double>& splays) {
    MotorSpaceRigging motor;
    return motor.calcularArreglo(json_path, num_boxes, bumper_height, bumper_tilt, splays);
}

inline std::map<std::string, double> calcular_metricas_sistema(const std::string& json_path, int num_boxes, const py::list& geometria) {
    std::map<std::string, double> metricas;
    
    auto& db = get_db_rigging();
    if (db.find(json_path) == db.end()) cargar_json_rigging(json_path);
    
    json j = db[json_path];
    
    // Peso total
    double peso_unitario = j.value("gabinete", json::object()).value("peso", 25.0);
    metricas["peso_total"] = peso_unitario * num_boxes;
    
    // Longitud aproximada del arreglo
    double altura_caja = j["gabinete"]["dimensiones_mm"]["alto"] / 1000.0;
    metricas["longitud_arreglo"] = altura_caja * num_boxes;
    
    // Clearance estimado (altura mínima del piso)
    metricas["clearance"] = 0.5; // placeholder
    
    return metricas;
}
