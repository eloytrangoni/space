#pragma once
#include <pybind11/pybind11.h>
#include <vector>
#include <string>
namespace motor_grafico {
    pybind11::object renderizar_curvatura(const pybind11::dict& geometry_data, const std::string& img_splay, const std::string& img_bumper);
    pybind11::object dibujar_lasers(const pybind11::dict& geometry_data);
    pybind11::object mapa_spl_colores(const pybind11::array_t<double>& matriz_spl, const pybind11::dict& config);
}
