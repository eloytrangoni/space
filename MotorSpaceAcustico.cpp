#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/numpy.h>
#include <cmath>
#include <vector>
#include <string>
#include <fstream>
#include <unordered_map>
#include <algorithm>
#include <omp.h>
#include "json.hpp" 

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

namespace py = pybind11;
using json = nlohmann::json;

std::unordered_map<std::string, json>& get_db() {
    static std::unordered_map<std::string, json> instance;
    return instance;
}

void cargar_json_motor(const std::string& json_path) {
    auto& db = get_db();
    if (db.find(json_path) == db.end()) {
        std::ifstream file(json_path);
        if (file.is_open()) {
            try { json j; file >> j; db[json_path] = j; } catch (...) {}
        }
    }
}

struct CajaGeom {
    double x, y, z, angle, spl_max;
};

std::vector<CajaGeom> extraer_geometria(const std::string& json_path, const py::list& geometria) {
    auto& db = get_db();
    double spl_max_global = 130.0; 
    
    if (db.find(json_path) != db.end() && db[json_path].is_object()) {
        spl_max_global = db[json_path].value("Max SPL RMS (1m)", 130.0);
    }

    std::vector<CajaGeom> cajas;
    cajas.reserve(py::len(geometria));
    
    for (size_t i = 0; i < py::len(geometria); ++i) {
        py::dict box = geometria[i].cast<py::dict>();
        CajaGeom cg;
        cg.x = box.contains("x") ? box["x"].cast<double>() : 0.0;
        cg.y = box.contains("y") ? box["y"].cast<double>() : 0.0; 
        cg.z = box.contains("z") ? box["z"].cast<double>() : 0.0;
        cg.angle = box.contains("angle") ? box["angle"].cast<double>() : 0.0;
        cg.spl_max = spl_max_global;
        cajas.push_back(cg);
    }
    return cajas;
}

double obtener_directividad(double angulo_deg, bool is_vertical) {
    while (angulo_deg <= -180.0) angulo_deg += 360.0;
    while (angulo_deg > 180.0) angulo_deg -= 360.0;
    double rad = angulo_deg * M_PI / 180.0;
    double atenuacion = 20.0 * std::log10(std::max(0.01, 0.5 + 0.5 * std::cos(rad)));
    return std::max(-40.0, atenuacion); 
}

// --- CÁLCULO LATERAL CORREGIDO A 2D ---
py::array_t<double> calcular_mapeo_spl(const std::string& json_path, const py::list& geometria, py::array_t<double> grid_x, py::array_t<double> grid_z, double freq, double temp, double hum) {
    py::buffer_info buf_x = grid_x.request();
    py::buffer_info buf_z = grid_z.request();
    
    double* ptr_x = static_cast<double*>(buf_x.ptr);
    double* ptr_z = static_cast<double*>(buf_z.ptr);
    int nx = buf_x.size;
    int nz = buf_z.size;
    
    // CREACIÓN DE MATRIZ 2D EXACTA
    auto result = py::array_t<double>({nz, nx});
    py::buffer_info buf_res = result.request();
    double* ptr_res = static_cast<double*>(buf_res.ptr);

    std::vector<CajaGeom> cajas = extraer_geometria(json_path, geometria);
    double c = 331.4 + 0.6 * temp; 
    double k = (freq > 0.0) ? (2.0 * M_PI * freq) / c : 0.0; 
    double air_absorption = (temp > 25.0 && hum < 50.0) ? 0.04 : 0.01;

    py::gil_scoped_release release;
    
    #pragma omp parallel for collapse(2)
    for(int i = 0; i < nz; i++) {
        for(int j = 0; j < nx; j++) {
            double calc_x = ptr_x[j];
            double calc_z = ptr_z[i];
            
            double p_real_total = 0.0;
            double p_imag_total = 0.0;
            
            for(const auto& caja : cajas) {
                double dx = calc_x - caja.x;
                double dz = calc_z - caja.z;
                double dist = std::max(0.1, std::sqrt(dx*dx + dz*dz)); 
                
                double angulo_absoluto = std::atan2(dz, dx) * 180.0 / M_PI;
                double angulo_relativo = angulo_absoluto - caja.angle;
                double atenuacion_dir = obtener_directividad(angulo_relativo, true);
                
                double spl_caja = caja.spl_max - 20.0 * std::log10(dist) - (air_absorption * dist) + atenuacion_dir;
                double p_amp = std::pow(10.0, spl_caja / 20.0);
                double fase = -k * dist;
                
                p_real_total += p_amp * std::cos(fase);
                p_imag_total += p_amp * std::sin(fase);
            }
            
            double p_rms = std::sqrt(p_real_total * p_real_total + p_imag_total * p_imag_total);
            ptr_res[i * nx + j] = (p_rms > 1e-10) ? 20.0 * std::log10(p_rms) : 0.0;
        }
    }

    return result;
}

// --- CÁLCULO SUPERIOR CORREGIDO A 2D ---
py::array_t<double> calcular_mapeo_spl_sup(const std::string& json_path, const py::list& geometria, py::array_t<double> grid_x, py::array_t<double> grid_y, double freq, double aud_escucha, double temp, double hum) {
    py::buffer_info buf_x = grid_x.request();
    py::buffer_info buf_y = grid_y.request();
    
    double* ptr_x = static_cast<double*>(buf_x.ptr);
    double* ptr_y = static_cast<double*>(buf_y.ptr);
    int nx = buf_x.size;
    int ny = buf_y.size;
    
    // CREACIÓN DE MATRIZ 2D EXACTA
    auto result = py::array_t<double>({ny, nx});
    py::buffer_info buf_res = result.request();
    double* ptr_res = static_cast<double*>(buf_res.ptr);

    std::vector<CajaGeom> cajas = extraer_geometria(json_path, geometria);
    double c = 331.4 + 0.6 * temp;
    double k = (freq > 0.0) ? (2.0 * M_PI * freq) / c : 0.0;
    double air_absorption = (temp > 25.0 && hum < 50.0) ? 0.04 : 0.01;

    py::gil_scoped_release release;
    
    #pragma omp parallel for collapse(2)
    for(int i = 0; i < ny; i++) {
        for(int j = 0; j < nx; j++) {
            double calc_x = ptr_x[j];
            double calc_y = ptr_y[i];
            
            double p_real_total = 0.0;
            double p_imag_total = 0.0;
            
            for(const auto& caja : cajas) {
                double dx = calc_x - caja.x;
                double dy = calc_y - caja.y;
                double dz = aud_escucha - caja.z; 
                double dist_3d = std::max(0.1, std::sqrt(dx*dx + dy*dy + dz*dz));
                
                double angulo_absoluto = std::atan2(dy, dx) * 180.0 / M_PI;
                double angulo_relativo = angulo_absoluto; 
                double atenuacion_dir = obtener_directividad(angulo_relativo, false);
                
                double spl_caja = caja.spl_max - 20.0 * std::log10(dist_3d) - (air_absorption * dist_3d) + atenuacion_dir;
                double p_amp = std::pow(10.0, spl_caja / 20.0);
                double fase = -k * dist_3d;
                
                p_real_total += p_amp * std::cos(fase);
                p_imag_total += p_amp * std::sin(fase);
            }
            
            double p_rms = std::sqrt(p_real_total * p_real_total + p_imag_total * p_imag_total);
            ptr_res[i * nx + j] = (p_rms > 1e-10) ? 20.0 * std::log10(p_rms) : 0.0;
        }
    }

    return result;
}

PYBIND11_MODULE(motor_acustico, m) {
    m.doc() = "Motor acustico avanzado HPC - Elo Acoustics"; 
    m.def("cargar_json_motor", &cargar_json_motor); 
    m.def("calcular_mapeo_spl", &calcular_mapeo_spl);
    m.def("calcular_mapeo_spl_sup", &calcular_mapeo_spl_sup);
}
