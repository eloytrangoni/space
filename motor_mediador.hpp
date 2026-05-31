#pragma once
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <vector>
#include <string>
class MediadorCache {
public:
    void set_proyecto(const std::string& archivo_a360);
    void update_params(const pybind11::dict& params);
    void build_full_state();
    pybind11::dict get_rigging();
    pybind11::dict get_spl();
    pybind11::dict get_graficos();
    pybind11::dict get_curva_mic();
};
