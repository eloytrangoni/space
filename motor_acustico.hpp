#pragma once
#include <pybind11/pybind11.h>
#include <vector>
#include <string>
namespace motor_acustico {
    pybind11::dict calcular_mapeo_spl(const std::string& json_path, const pybind11::list& geometria,
                                      const pybind11::array_t<double>& grid_x,
                                      const pybind11::array_t<double>& grid_z,
                                      double freq, double temp, double hum, const std::string& archivo_med_h, const std::string& archivo_med_v);
}
