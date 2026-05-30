#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <vector>
#include <string>
#include <cmath>
#include <fstream>
#include <iostream>
#include <algorithm>
#include "json.hpp" 

namespace py = pybind11;
using json = nlohmann::json;

const std::string DB_FILE = "autosplay_brain.json";

struct Proyecto {
    int cajas;
    double h_bumper;
    double tilt;
    std::vector<double> splays;
};

// ---------------------------------------------------------------------------------
// MANEJO DE MEMORIA A LARGO PLAZO (DISCO)
// ---------------------------------------------------------------------------------
std::vector<Proyecto> cargar_memoria() {
    std::vector<Proyecto> memoria;
    std::ifstream file(DB_FILE);
    if (file.is_open()) {
        try {
            json j;
            file >> j;
            if(j.is_array()) { // INGENIERÍA: Chequeo de integridad del vector JSON
                for (const auto& item : j) {
                    Proyecto p;
                    p.cajas = item.value("cajas", 0);
                    p.h_bumper = item.value("h_bumper", 0.0);
                    p.tilt = item.value("tilt", 0.0);
                    if(item.contains("splays") && item["splays"].is_array()) {
                        p.splays = item["splays"].get<std::vector<double>>();
                    }
                    memoria.push_back(p);
                }
            }
        } catch (...) {
            // Fallo silencioso y seguro: Si el usuario borra la mitad del archivo a mano, no crashea
        }
    }
    return memoria;
}

void guardar_memoria(const std::vector<Proyecto>& memoria) {
    json j = json::array();
    for (const auto& p : memoria) {
        j.push_back({
            {"cajas", p.cajas},
            {"h_bumper", p.h_bumper},
            {"tilt", p.tilt},
            {"splays", p.splays}
        });
    }
    std::ofstream file(DB_FILE);
    if (file.is_open()) {
        file << j.dump(4);
    }
}

// Llama a esta función desde Python cada vez que el usuario hace un splay manual y aprieta "Guardar"
void registrar_decision(int cajas, double h_bumper, double tilt, const std::vector<double>& splays) {
    if (cajas <= 1 || splays.empty()) return;
    auto memoria = cargar_memoria();
    memoria.push_back({cajas, h_bumper, tilt, splays});
    guardar_memoria(memoria);
}

// ---------------------------------------------------------------------------------
// MOTOR DE INFERENCIA IA (KNN + IDW)
// ---------------------------------------------------------------------------------
std::vector<double> predecir_splays(int cajas, double h_bumper, double tilt) {
    // SEGURIDAD CRÍTICA: Prevenir división por cero si solo hay 1 gabinete (sin splay)
    if (cajas <= 1) {
        return std::vector<double>(); 
    }

    std::vector<double> fallback(cajas - 1, 0.0);
    // Fallback matemático heurístico (Espiral logarítmica básica) si la IA nace sin memoria
    for(int i = 0; i < cajas - 1; ++i) {
        fallback[i] = std::pow(static_cast<double>(i) / (cajas - 1), 2.0) * 8.0; 
    }

    auto memoria = cargar_memoria();
    std::vector<Proyecto> validos;
    
    // Filtramos solo los proyectos que tengan la misma cantidad de cajas, e integridad de arrays validada
    for (const auto& p : memoria) {
        if (p.cajas == cajas && p.splays.size() == static_cast<size_t>(cajas - 1)) {
            validos.push_back(p);
        }
    }

    // Si la IA no tiene recuerdos para esta cantidad exacta de cajas, devuelve el fallback
    if (validos.empty()) return fallback; 

    // K-Nearest Neighbors: Buscamos las predicciones que tengan altura y tilt más parecidos
    std::vector<std::pair<double, int>> distancias; 
    for (size_t i = 0; i < validos.size(); ++i) {
        double dist_h = validos[i].h_bumper - h_bumper;
        double dist_tilt = validos[i].tilt - tilt;
        // Ponderación: Le damos el doble de peso a la diferencia de tilt porque afecta más la puntería
        double d = std::sqrt(dist_h * dist_h + (dist_tilt * dist_tilt * 2.0));
        distancias.push_back({d, static_cast<int>(i)});
    }

    std::sort(distancias.begin(), distancias.end());

    // Usamos los 3 vecinos más cercanos (o los que haya si son menos de 3)
    int K = std::min(3, static_cast<int>(validos.size()));
    std::vector<double> prediccion(cajas - 1, 0.0);
    double suma_pesos = 0.0;

    for (int k = 0; k < K; ++k) {
        double d = distancias[k].first;
        double peso = 1.0 / (d + 0.001); // Prevenir división por cero si la distancia es exacta (match perfecto)
        suma_pesos += peso;
        
        int idx = distancias[k].second;
        for (int s = 0; s < cajas - 1; ++s) {
            prediccion[s] += validos[idx].splays[s] * peso;
        }
    }

    // Promedio ponderado y redondeo a 1 decimal para la mecánica del mundo real
    for (int s = 0; s < cajas - 1; ++s) {
        prediccion[s] = std::round((prediccion[s] / suma_pesos) * 10.0) / 10.0;
    }

    return prediccion;
}

PYBIND11_MODULE(motor_autosplay, m) {
    m.doc() = "Motor de IA nativo para Auto Splay - Elo Acoustics";
    m.def("registrar_decision", &registrar_decision);
    m.def("predecir_splays", &predecir_splays);
}