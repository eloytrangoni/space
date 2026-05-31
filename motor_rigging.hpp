#pragma once
#include <pybind11/pybind11.h>
#include <vector>
#include <string>
namespace motor_rigging {
    pybind11::dict calcular_geometria_rigging(const std::string& json_path, int num_boxes, double bumper_height, double bumper_tilt, const std::vector<double>& splays, const pybind11::dict& params);
    pybind11::dict calcular_centro_gravedad(const pybind11::dict& geometry);
    pybind11::dict calcular_pin_points(const pybind11::dict& bumper, const pybind11::dict& gabinetes);
}
