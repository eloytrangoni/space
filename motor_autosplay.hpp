#pragma once
#include <pybind11/pybind11.h>
#include <vector>
#include <string>
namespace motor_autosplay {
    std::vector<double> predecir_splays(const pybind11::dict& area_audiencia, int num_boxes, const std::string& tipo, const pybind11::dict& ubicaciones, const pybind11::dict& historial);
}
