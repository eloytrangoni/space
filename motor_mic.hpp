#pragma once
#include <pybind11/pybind11.h>
#include <vector>
#include <string>
namespace motor_mic {
    pybind11::object calcular_respuesta_freq(const pybind11::array_t<double>& matriz_spl, const pybind11::list& mic_positions, const pybind11::dict& geometry, const pybind11::dict& ambiente);
}
