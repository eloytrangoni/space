cmake_minimum_required(VERSION 3.15)
project(MotorSpace)

# Configuración de C++
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# OpenMP para paralelización
find_package(OpenMP REQUIRED)

# Pybind11
find_package(pybind11 REQUIRED)

# Numpy y Python
find_package(Python COMPONENTS Interpreter Development NumPy REQUIRED)

# ==========================================
# Motor Acústico
# ==========================================
pybind11_add_module(motor_acustico src/MotorSpaceAcustico.cpp)
target_link_libraries(motor_acustico PRIVATE OpenMP::OpenMP_CXX)
target_include_directories(motor_acustico PRIVATE ${Python_INCLUDE_DIRS} ${Python_NumPy_INCLUDE_DIRS})

# ==========================================
# Motor Gráfico
# ==========================================
pybind11_add_module(motor_grafico src/MotorSpaceGrafico.cpp)
target_link_libraries(motor_grafico PRIVATE OpenMP::OpenMP_CXX)
target_include_directories(motor_grafico PRIVATE ${Python_INCLUDE_DIRS} ${Python_NumPy_INCLUDE_DIRS})

# ==========================================
# Motor Auto Splay
# ==========================================
pybind11_add_module(motor_autosplay src/MotorSpaceAutoSplay.cpp)
target_include_directories(motor_autosplay PRIVATE ${Python_INCLUDE_DIRS})

# ==========================================
# Motor Rigging
# ==========================================
pybind11_add_module(motor_rigging src/MotorSpaceRigging.cpp)
target_include_directories(motor_rigging PRIVATE ${Python_INCLUDE_DIRS})

# ==========================================
# Motor Micrófono
# ==========================================
pybind11_add_module(motor_mic src/MotorSpaceMic.cpp)
target_include_directories(motor_mic PRIVATE ${Python_INCLUDE_DIRS})

# ==========================================
# Motor Mediador
# ==========================================
pybind11_add_module(motor_mediador src/MotorSpaceMediador.cpp)
target_include_directories(motor_mediador PRIVATE ${Python_INCLUDE_DIRS})

# Configuración por plataforma
if(WIN32)
    set_target_properties(motor_acustico motor_grafico motor_autosplay motor_rigging motor_mic motor_mediador
        PROPERTIES SUFFIX ".pyd")
elseif(APPLE)
    set_target_properties(motor_acustico motor_grafico motor_autosplay motor_rigging motor_mic motor_mediador
        PROPERTIES SUFFIX ".so")
endif()

# Output directory
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib)
