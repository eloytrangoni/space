#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <cmath>
#include <vector>
#include <string>
#include <fstream>
#include <algorithm>
#include <unordered_map>
#include "json.hpp"

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

namespace py = pybind11;
using json = nlohmann::json;

// --- Gestor de base de datos de Micrófono ---
std::unordered_map<std::string, json>& get_db_mic() {
    static std::unordered_map<std::string, json> instance;
    return instance;
}

void cargar_json_mic(const std::string& json_path) {
    auto& db = get_db_mic();
    if (db.find(json_path) == db.end()) {
        std::ifstream file(json_path);
        if (file.is_open()) { 
            try { 
                json j; file >> j; 
                if (j.is_object()) { db[json_path] = j; }
            } catch (...) {} 
        }
    }
}

// ---------------------------------------------------------------------------------
// FUNCIÓN DE SIMULACIÓN DE RESPUESTA EN PUNTO (MICRÓFONO VIRTUAL)
// ---------------------------------------------------------------------------------
py::dict simular_microfono_virtual(const std::string& json_path, const py::list& geometria, double mic_x, double mic_y, double mic_z, double freq, double temp, double hum) {
    auto& db = get_db_mic();
    if (db.find(json_path) == db.end()) cargar_json_mic(json_path);
    
    json j_data = (db.find(json_path) != db.end()) ? db[json_path] : json::object();
    double spl_max_nominal = j_data.value("Max SPL RMS (1m)", 130.0);
    
    // Parámetros ambientales
    double c = 331.4 + 0.6 * temp;
    double k = (freq > 0.0) ? (2.0 * M_PI * freq) / c : 0.0;
    double air_absorption = (temp > 25.0 && hum < 50.0) ? 0.04 : 0.01;
    
    double p_real_total = 0.0;
    double p_imag_total = 0.0;
    
    // Acumulación de presión sonora compleja (Suma de fuentes)
    for (size_t b = 0; b < py::len(geometria); ++b) {
        py::dict box = geometria[b].cast<py::dict>();
        double bx = box["x"].cast<double>();
        double bz = box["z"].cast<double>();
        // Usamos Y=0 para el centro del altavoz en el modelo actual
        
        double dx = mic_x - bx;
        double dy = mic_y - 0.0;
        double dz = mic_z - bz;
        
        // SEGURIDAD: Prevenir división por cero/log de cero
        double dist = std::max(0.2, std::sqrt(dx*dx + dy*dy + dz*dz));
        
        // SPL por caja (Ley inversa + Absorción)
        double spl_caja = spl_max_nominal - 20.0 * std::log10(dist) - (air_absorption * dist);
        
        // Conversión a fasor
        double p_amp = std::pow(10.0, spl_caja / 20.0);
        double phase = -k * dist;
        
        p_real_total += p_amp * std::cos(phase);
        p_imag_total += p_amp * std::sin(phase);
    }
    
    // Resultado final SPL RMS
    double p_rms = std::sqrt(p_real_total * p_real_total + p_imag_total * p_imag_total);
    double spl_final = (p_rms > 1e-10) ? 20.0 * std::log10(p_rms) : 0.0;
    
    py::dict resultado;
    resultado["spl"] = spl_final;
    resultado["fase"] = std::atan2(p_imag_total, p_real_total) * 180.0 / M_PI;
    
    return resultado;
}

PYBIND11_MODULE(motor_mic, m) {
    m.doc() = "Motor de Microfono Virtual - Elo Acoustics";
    m.def("cargar_json_mic", &cargar_json_mic);
    m.def("simular_microfono_virtual", &simular_microfono_virtual);
}