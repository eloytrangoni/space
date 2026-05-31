# -*- coding: utf-8 -*-
import sys
import os
import json
import numpy as np
import zipfile
import tempfile
import faulthandler

faulthandler.enable()

print("\n[DEBUG] -> Iniciando script space.py (Versión Modular - Mics, Interacción XY y Menús Completos)...")

# --- Inicialización de Motores Nativos ---
motor_acustico = None
motor_grafico = None
motor_autosplay = None
motor_mediador = None
motor_rigging = None
motor_mic = None
error_de_importacion = ""

# ==========================================
# GESTIÓN DE BASE DE DATOS LOCAL
# ==========================================
DB_DIR = os.path.join(os.getcwd(), "elo_db")
if not os.path.exists(DB_DIR):
    os.makedirs(DB_DIR)
DB_FILE = os.path.join(DB_DIR, "db_altavoces.json")

def cargar_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except: pass
    return {}

def guardar_db():
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(DB_ALTAVOCES, f, indent=4)

DB_ALTAVOCES = cargar_db()

try: import motor_acustico; print("[DEBUG] -> motor_acustico OK")
except Exception as e: error_de_importacion += f"motor_acustico: {e}\n"

try: import motor_grafico; print("[DEBUG] -> motor_grafico OK")
except Exception as e: error_de_importacion += f"motor_grafico: {e}\n"

try: import motor_autosplay; print("[DEBUG] -> motor_autosplay OK")
except Exception as e: error_de_importacion += f"motor_autosplay: {e}\n"

try: import motor_mediador; print("[DEBUG] -> motor_mediador OK")
except Exception as e: error_de_importacion += f"motor_mediador: {e}\n"

try: import motor_rigging; print("[DEBUG] -> motor_rigging OK")
except Exception as e: error_de_importacion += f"motor_rigging: {e}\n"

try: import motor_mic; print("[DEBUG] -> motor_mic OK")
except Exception as e: error_de_importacion += f"motor_mic: {e}\n"


from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QGridLayout, QLabel, QLineEdit,
                             QPushButton, QFileDialog, QProgressBar,
                             QMessageBox, QGroupBox, QMenu, QAction,
                             QComboBox, QListWidget, QListWidgetItem, QDialog, 
                             QDialogButtonBox, QSplitter, QSizePolicy, QTabWidget)
from PyQt5.QtGui import QImage, QPainter, QPen, QColor, QFont, QLinearGradient
from PyQt5.QtCore import QThread, pyqtSignal, Qt

# ==========================================
# CONSTANTES Y TEMAS
# ==========================================
THEME_DARK = """
    QMainWindow, QWidget { background-color: #1e1e1e; color: #ffffff; font-family: 'Segoe UI'; }
    QGroupBox { border: 1px solid #555; margin-top: 25px; padding-top: 15px; font-weight: bold; }
    QGroupBox::title { subcontrol-origin: margin; left: 10px; top: -12px; padding: 5px 10px; }
    QLineEdit, QComboBox { background: #333; border: 1px solid #555; padding: 4px; border-radius: 3px; color: white; }
    QPushButton { border-radius: 4px; background: #444; color: white; padding: 5px; }
    QMenuBar { background-color: #2a2a2a; color: white; }
    QMenuBar::item:selected { background-color: #005fb8; }
    QMenu { background-color: #2a2a2a; color: white; border: 1px solid #555; }
    QMenu::item:selected { background-color: #005fb8; }
    QTabWidget::pane { border: 1px solid #555; }
    QTabBar::tab { background: #333; color: white; padding: 8px 15px; border-top-left-radius: 4px; border-top-right-radius: 4px; border: 1px solid #555; border-bottom: none; }
    QTabBar::tab:selected { background: #005fb8; font-weight: bold; }
"""

THEME_LIGHT = """
    QMainWindow, QWidget { background-color: #f5f5f5; color: #111111; font-family: 'Segoe UI'; }
    QGroupBox { border: 1px solid #ccc; margin-top: 25px; padding-top: 15px; font-weight: bold; }
    QGroupBox::title { subcontrol-origin: margin; left: 10px; top: -12px; padding: 5px 10px; }
    QLineEdit, QComboBox { background: #ffffff; border: 1px solid #ccc; padding: 4px; border-radius: 3px; color: #111111; }
    QPushButton { border-radius: 4px; background: #e0e0e0; color: #111111; padding: 5px; }
    QMenuBar { background-color: #e0e0e0; color: #111111; }
    QMenuBar::item:selected { background-color: #005fb8; color: white; }
    QMenu { background-color: #ffffff; color: #111111; border: 1px solid #ccc; }
    QMenu::item:selected { background-color: #005fb8; color: white; }
    QTabWidget::pane { border: 1px solid #ccc; }
    QTabBar::tab { background: #e0e0e0; color: #111111; padding: 8px 15px; border-top-left-radius: 4px; border-top-right-radius: 4px; border: 1px solid #ccc; border-bottom: none; }
    QTabBar::tab:selected { background: #005fb8; color: white; font-weight: bold; }
"""

FREQ_1_6_OCT = ["31.5", "35.5", "40", "45", "50", "56", "63", "71", "80", "90", "100", 
                "112", "125", "140", "160", "180", "200", "224", "250", "280", "315", 
                "355", "400", "450", "500", "560", "630", "710", "800", "900", "1000", 
                "1120", "1250", "1400", "1600", "1800", "2000", "2240", "2500", "2800", 
                "3150", "3550", "4000", "4500", "5000", "5600", "6300", "7100", "8000", 
                "9000", "10000", "11200", "12500", "14000", "16000"]

# ==========================================
# GESTOR DE ARCHIVOS - CORRECCIÓN CRÍTICA
# ==========================================
class GestorArchivosA360:
    @staticmethod
    def importar_archivo(file_path):
        meta = {}
        if zipfile.is_zipfile(file_path):
            temp_dir = tempfile.mkdtemp()
            with zipfile.ZipFile(file_path, 'r') as z:
                z.extractall(temp_dir)
            meta_path = os.path.join(temp_dir, "metadata.json")
            if os.path.exists(meta_path):
                with open(meta_path, 'r', encoding='utf-8') as f: meta = json.load(f)
        else:
            with open(file_path, 'r', encoding='utf-8') as f: meta = json.load(f)
    
        raw_marca = meta.get("gabinete", {}).get("marca", "Elo Acoustics")
        marca_unificada = "ELO ACOUSTICS" if raw_marca.upper() == "ELO ACOUSTICS" else raw_marca
        modelo = meta.get("gabinete", {}).get("modelo", "Generic Model")

        # ✅ CORRECCIÓN: Ahora extraemos los parámetros correctamente desde el JSON
        gabinete = meta.get("gabinete", {})
        dimensiones = gabinete.get("dimensiones_mm", {})
        
        motor_data = {
            "Tipo": "Line Array",
            "Alto Frontal (Y)": float(dimensiones.get("alto", 300)) / 1000.0,
            "Ancho Frontal (x)": float(dimensiones.get("ancho", 500)) / 1000.0,
            "Profundidad": float(dimensiones.get("profundidad", 474)) / 1000.0,
            "Separacion entre cajas": float(gabinete.get("separacion_entre_gabinetes_mm", 3)) / 1000.0,
            "Peso (kg)": float(gabinete.get("peso", 25)),
            "Max SPL RMS (1m)": float(gabinete.get("spl_max", 130)),
            "Splay Máximo": float(gabinete.get("splay_maximo", 5.0)),
            "Pin_X": 0.0, 
            "Pin_Z": 0.0,
            "system_response": meta.get("system_response", {"frequencies": [], "vertical": {}, "horizontal": {}})
        }
        
        temp_json_path = os.path.join(DB_DIR, f"{marca_unificada}_{modelo}_motor.json".replace(" ", "_"))
        with open(temp_json_path, 'w', encoding='utf-8') as f: 
            json.dump(motor_data, f, indent=4)
        
        # ✅ TAMBIÉN guardar el metadata.json original para que los motores C++ lo lean directamente
        meta_backup_path = os.path.join(DB_DIR, f"{marca_unificada}_{modelo}_metadata.json".replace(" ", "_"))
        with open(meta_backup_path, 'w', encoding='utf-8') as f:
            json.dump(meta, f, indent=4)
        
        print(f"[DEBUG] ✅ Motor data extraído correctamente:")
        print(f"  - Marca: {marca_unificada}")
        print(f"  - Modelo: {modelo}")
        print(f"  - Alto: {motor_data['Alto Frontal (Y)']} m")
        print(f"  - Ancho: {motor_data['Ancho Frontal (x)']} m")
        print(f"  - Separación: {motor_data['Separacion entre cajas']} m")
        print(f"  - Peso: {motor_data['Peso (kg)']} kg")
        print(f"  - Max SPL: {motor_data['Max SPL RMS (1m)']} dB")
        
        return f"{marca_unificada}_{modelo}", marca_unificada, modelo, motor_data, meta_backup_path

# ==========================================
# WORKERS Y CLASES DE UI INFERIOR
# ==========================================
class CalculoMapeoWorker(QThread):
    calculo_terminado = pyqtSignal(np.ndarray, np.ndarray, str)

    def __init__(self, tipo_mapeo, json_path, geometria, grid_1, grid_2, freq, param_extra, temp, hum):
        super().__init__()
        self.tipo_mapeo = tipo_mapeo
        self.json_path = json_path
        self.geometria = geometria
        self.grid_1 = grid_1
        self.grid_2 = grid_2
        self.freq = freq
        self.param_extra = param_extra
        self.temp = temp
        self.hum = hum
        self.resultado_matriz = None

    def run(self):
        if motor_acustico is None: return
        try:
            if self.tipo_mapeo == "lateral":
                self.resultado_matriz = motor_acustico.calcular_mapeo_spl(
                    self.json_path, self.geometria, self.grid_1, self.grid_2, self.freq, self.temp, self.hum
                )
                self.calculo_terminado.emit(self.grid_1, self.grid_2, "lateral")
                
            elif self.tipo_mapeo == "superior":
                self.resultado_matriz = motor_acustico.calcular_mapeo_spl_sup(
                    self.json_path, self.geometria, self.grid_1, self.grid_2, self.freq, self.param_extra, self.temp, self.hum
                )
                self.calculo_terminado.emit(self.grid_1, self.grid_2, "superior")
        except Exception as e:
            print(f"[ERROR HILO] Falló cálculo nativo: {e}")
            self.resultado_matriz = np.array([[]])
            self.calculo_terminado.emit(self.grid_1, self.grid_2, self.tipo_mapeo)


class FreqResponseCanvas(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.mic_id = None
        self.is_light = False
        self.setMinimumSize(300, 200)
        self.pad_l = 50  
        self.pad_b = 30  
        self.pad_t = 40  # Padding superior para no pisar el título

    def set_mic(self, mic_id):
        self.mic_id = mic_id
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        bg_color = QColor(255, 255, 255) if self.is_light else QColor(25, 25, 25)
        text_color = Qt.black if self.is_light else Qt.white
        
        painter.fillRect(self.rect(), bg_color)
        w, h = self.width(), self.height()
        
        # Título
        painter.setPen(text_color)
        painter.setFont(QFont("Segoe UI", 10, QFont.Bold))
        if not self.mic_id or self.mic_id == "Mics...":
            painter.drawText(self.rect(), Qt.AlignCenter, "Seleccione un micrófono para ver su respuesta")
            return
        
        painter.drawText(self.pad_l + 10, 25, f"Respuesta de Frecuencia: {self.mic_id}")
        
        usable_w = w - self.pad_l
        usable_h = h - self.pad_b - self.pad_t

        painter.setFont(QFont("Arial", 8))
        
        # --- Eje Y: Amplitud (-24 dB a +24 dB con paso de 3 dB) ---
        grid_line_0db = QColor(0, 0, 0, 150) if self.is_light else QColor(255, 255, 255, 150)
        grid_line_norm = QColor(0, 0, 0, 50) if self.is_light else QColor(100, 100, 100, 50)
        
        for db in range(-24, 25, 3):
            y = self.pad_t + int(usable_h * (24 - db) / 48)
            
            if db == 0:
                painter.setPen(QPen(grid_line_0db, 2))
            else:
                painter.setPen(QPen(grid_line_norm, 1, Qt.DashLine))
            
            painter.drawLine(self.pad_l, y, w, y)
            
            painter.setPen(text_color)
            texto_db = f"+{db} dB" if db > 0 else f"{db} dB"
            painter.drawText(5, y + 4, texto_db)

        # --- Eje X: Frecuencia (Escala Logarítmica 20Hz a 20kHz) ---
        freqs_principales = [20, 50, 100, 500, 1000, 5000, 10000, 20000]
        freqs_secundarias = [30, 40, 60, 70, 80, 90, 200, 300, 400, 600, 700, 800, 900, 
                             2000, 3000, 4000, 6000, 7000, 8000, 9000]
        
        log20 = np.log10(20)
        log20k = np.log10(20000)
        
        # Secundarias
        painter.setPen(QPen(grid_line_norm, 1, Qt.DotLine))
        for f in freqs_secundarias:
            x = self.pad_l + int(usable_w * (np.log10(f) - log20) / (log20k - log20))
            painter.drawLine(x, self.pad_t, x, h - self.pad_b)
            
        # Principales
        grid_line_main_x = QColor(0, 0, 0, 100) if self.is_light else QColor(150, 150, 150, 100)
        painter.setPen(QPen(grid_line_main_x, 1))
        for f in freqs_principales:
            x = self.pad_l + int(usable_w * (np.log10(f) - log20) / (log20k - log20))
            painter.drawLine(x, self.pad_t, x, h - self.pad_b)
            
            lbl = f"{f//1000}k" if f >= 1000 else str(f)
            painter.setPen(text_color)
            painter.drawText(x - 10, h - 10, lbl)
            painter.setPen(QPen(grid_line_main_x, 1))

        # --- Curva de Simulación (Mock) ---
        painter.setPen(QPen(QColor(0, 215, 120), 2))
        path = []
        for px in range(self.pad_l, w, 2):
            y = self.pad_t + (usable_h / 2) - 30 * np.sin((px - self.pad_l)/30.0) - 10 * np.cos((px - self.pad_l)/10.0)
            y = max(self.pad_t, min(self.pad_t + usable_h, y))
            path.append((px, int(y)))
            
        for i in range(len(path)-1):
            painter.drawLine(path[i][0], path[i][1], path[i+1][0], path[i+1][1])


class FastSPLCanvas(QWidget):
    posicion_registrada = pyqtSignal(str, str, float, float, str) 
    posicion_movida = pyqtSignal(str, str, float, float, str)

    def __init__(self, tipo_vista="lateral", parent=None):
        super().__init__(parent)
        self.tipo_vista = tipo_vista
        self.is_light = False
        self.setMouseTracking(True)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumSize(300, 200)

        self.qimage = None
        self.geometria = None
        self.grid_x = None
        self.grid_z = None
        self.mostrar_mapeo = True

        self.modo_colocacion = None 
        self.item_colocando_id = None
        self.item_arrastrado = None 
        self.mouse_x = 0
        self.mouse_y = 0
        self.fuentes_coords = {} 
        self.mics_coords = {}    
        self.aud_largo = 50.0
        self.aud_ancho = 20.0
        self.aud_alto = 8.0

    def actualizar_dimensiones(self, largo, ancho, alto):
        self.aud_largo = largo
        self.aud_ancho = ancho
        self.aud_alto = alto
        self.update()

    def set_data(self, rgba_array, grid_x, grid_z, geometria):
        self.grid_x = grid_x
        self.grid_z = grid_z
        self.geometria = geometria
        if rgba_array is not None and rgba_array.size > 0:
            h, w, ch = rgba_array.shape
            self.qimage = QImage(rgba_array.tobytes(), w, h, w * ch, QImage.Format_RGBA8888)
        else: self.qimage = None
        self.update()

    def iniciar_colocacion(self, tipo, item_id):
        self.modo_colocacion = tipo
        self.item_colocando_id = item_id
        self.setCursor(Qt.CrossCursor)

    def rx_to_px(self, rx): return int((rx / self.aud_largo) * self.width()) if self.aud_largo else 0
    def ry_to_py(self, ry):
        if not self.aud_ancho: return 0
        return int((1.0 - (ry + self.aud_ancho / 2) / self.aud_ancho) * self.height())
    def px_to_rx(self, px): return (px / self.width()) * self.aud_largo
    def py_to_ry(self, py): return (1.0 - py / self.height()) * self.aud_ancho - (self.aud_ancho / 2)

    def _get_z_bounds(self):
        if self.grid_z is not None and len(self.grid_z) > 0: return self.grid_z[0], self.grid_z[-1]
        return 0.0, self.aud_alto + 2.0

    def _get_x_bounds(self):
        if self.grid_x is not None and len(self.grid_x) > 0: return self.grid_x[0], self.grid_x[-1]
        return 0.0, self.aud_largo

    def rx_to_px_lat(self, rx):
        xmin, xmax = self._get_x_bounds()
        rango = xmax - xmin
        return int(((rx - xmin) / rango) * self.width()) if rango else 0
    
    def rz_to_py_lat(self, rz):
        zmin, zmax = self._get_z_bounds()
        rango = zmax - zmin
        return int((1.0 - (rz - zmin) / rango) * self.height()) if rango else 0

    def px_to_rx_lat(self, px):
        xmin, xmax = self._get_x_bounds()
        return xmin + (px / self.width()) * (xmax - xmin)

    def py_to_rz_lat(self, py):
        zmin, zmax = self._get_z_bounds()
        return zmin + (1.0 - py / self.height()) * (zmax - zmin)

    def mouseMoveEvent(self, event):
        self.mouse_x = event.x()
        self.mouse_y = event.y()

        if self.item_arrastrado:
            tipo, item_id = self.item_arrastrado
            if self.tipo_vista == "superior":
                rx = self.px_to_rx(self.mouse_x)
                ry = self.py_to_ry(self.mouse_y)
                self.posicion_movida.emit(tipo, item_id, rx, ry, self.tipo_vista)
            elif self.tipo_vista == "lateral":
                rx = self.px_to_rx_lat(self.mouse_x)
                rz = self.py_to_rz_lat(self.mouse_y)
                self.posicion_movida.emit(tipo, item_id, rx, rz, self.tipo_vista)

        self.update()

    def mousePressEvent(self, event):
        if self.modo_colocacion:
            if self.tipo_vista == "superior":
                rx = self.px_to_rx(event.x())
                ry = self.py_to_ry(event.y())
                self.posicion_registrada.emit(self.modo_colocacion, self.item_colocando_id, rx, ry, self.tipo_vista)
            self.modo_colocacion = None
            self.item_colocando_id = None
            self.setCursor(Qt.ArrowCursor)
        else:
            umbral_px = 12
            if self.tipo_vista == "superior":
                for mid, (mx, my) in self.mics_coords.items():
                    if abs(self.rx_to_px(mx) - event.x()) < umbral_px and abs(self.ry_to_py(my) - event.y()) < umbral_px:
                        self.item_arrastrado = ("mic", mid); return
                for fid, (fx, fy) in self.fuentes_coords.items():
                    if abs(self.rx_to_px(fx) - event.x()) < umbral_px and abs(self.ry_to_py(fy) - event.y()) < umbral_px:
                        self.item_arrastrado = ("fuente", fid); return
            elif self.tipo_vista == "lateral":
                for mid, (mx, mz) in self.mics_coords.items():
                    if abs(self.rx_to_px_lat(mx) - event.x()) < umbral_px and abs(self.rz_to_py_lat(mz) - event.y()) < umbral_px:
                        self.item_arrastrado = ("mic", mid); return

    def mouseReleaseEvent(self, event):
        self.item_arrastrado = None

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        bg_color = QColor(255, 255, 255) if self.is_light else QColor(25, 25, 25)
        text_color = Qt.black if self.is_light else Qt.white
        painter.fillRect(self.rect(), bg_color)

        if self.mostrar_mapeo and self.qimage and not self.qimage.isNull():
            scaled_img = self.qimage.scaled(self.size(), Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
            painter.drawImage(0, 0, scaled_img)

        painter.setFont(QFont("Arial", 8))
        grid_color_line = QColor(0, 0, 0, 40) if self.is_light else QColor(255, 255, 255, 60)
        grid_color_text = QColor(0, 0, 0, 180) if self.is_light else QColor(255, 255, 255, 180)
        
        paso_m = 5.0 if self.aud_largo < 40 else 10.0

        if self.tipo_vista == "superior":
            for mx in np.arange(0, self.aud_largo + 1, paso_m):
                px = self.rx_to_px(mx)
                painter.setPen(QPen(grid_color_line, 1, Qt.DashLine))
                painter.drawLine(px, 0, px, self.height())
                painter.setPen(grid_color_text)
                painter.drawText(px + 4, self.height() - 5, f"{int(mx)}m")
            for my in np.arange(-self.aud_ancho/2, self.aud_ancho/2 + 1, paso_m):
                py = self.ry_to_py(my)
                painter.setPen(QPen(grid_color_line, 1, Qt.DashLine))
                painter.drawLine(0, py, self.width(), py)
                painter.setPen(grid_color_text)
                painter.drawText(5, py - 4, f"{int(my)}m")
                
        elif self.tipo_vista == "lateral":
            for mx in np.arange(0, self.aud_largo + 1, paso_m):
                px = self.rx_to_px_lat(mx)
                painter.setPen(QPen(grid_color_line, 1, Qt.DashLine))
                painter.drawLine(px, 0, px, self.height())
                painter.setPen(grid_color_text)
                painter.drawText(px + 4, self.height() - 5, f"{int(mx)}m")
            for mz in np.arange(0, self.aud_alto + 1, 2.0):
                pz = self.rz_to_py_lat(mz)
                painter.setPen(QPen(grid_color_line, 1, Qt.DashLine))
                painter.drawLine(0, pz, self.width(), pz)
                painter.setPen(grid_color_text)
                painter.drawText(5, pz - 4, f"{int(mz)}m")

        if self.tipo_vista == "lateral":
            if self.geometria and self.grid_x is not None and self.grid_z is not None:
                xmin, xmax = self.grid_x[0], self.grid_x[-1]
                zmin, zmax = self.grid_z[0], self.grid_z[-1]
                w_canvas, h_canvas = self.width(), self.height()
                pen_lines = QPen(QColor(0, 255, 0, 180), 2)
                for box in self.geometria:
                    bx, bz, ang = box["x"], box["z"], box["angle"]
                    px = int((bx - xmin) / (xmax - xmin) * w_canvas)
                    pz = int(h_canvas - (bz - zmin) / (zmax - zmin) * h_canvas)
                    painter.setPen(pen_lines)
                    painter.drawPoint(px, pz)
            
            painter.setFont(QFont("Arial", 8, QFont.Bold))
            for mid, (mx, mz) in self.mics_coords.items():
                px, pz = self.rx_to_px_lat(mx), self.rz_to_py_lat(mz)
                painter.setPen(Qt.black)
                painter.setBrush(QColor(0, 215, 120))
                painter.drawEllipse(px - 6, pz - 6, 12, 12)
                painter.setPen(text_color)
                painter.drawText(px + 10, pz + 4, f"{mid} ({mz:.1f}m)")

        if self.tipo_vista == "superior":
            painter.setFont(QFont("Arial", 8, QFont.Bold))
            for fid, (fx, fy) in self.fuentes_coords.items():
                px, py = self.rx_to_px(fx), self.ry_to_py(fy)
                painter.setPen(Qt.white)
                painter.setBrush(QColor(0, 120, 215))
                painter.drawRect(px - 8, py - 8, 16, 16)
                painter.setPen(text_color)
                painter.drawText(px + 12, py + 4, fid)

            for mid, (mx, my) in self.mics_coords.items():
                px, py = self.rx_to_px(mx), self.ry_to_py(my)
                painter.setPen(Qt.black)
                painter.setBrush(QColor(0, 215, 120))
                painter.drawEllipse(px - 6, py - 6, 12, 12)
                painter.setPen(text_color)
                painter.drawText(px + 10, py + 4, mid)

            if self.modo_colocacion:
                painter.setPen(text_color)
                if self.modo_colocacion == "fuente":
                    painter.setBrush(QColor(0, 120, 215))
                    painter.drawRect(self.mouse_x - 8, self.mouse_y - 8, 16, 16)
                    painter.drawText(self.mouse_x + 12, self.mouse_y + 4, f"[{self.item_colocando_id}]")
                elif self.modo_colocacion == "mic":
                    painter.setBrush(QColor(0, 215, 120))
                    painter.drawEllipse(self.mouse_x - 6, self.mouse_y - 6, 12, 12)
                    painter.drawText(self.mouse_x + 10, self.mouse_y + 4, f"{self.item_colocando_id}")

        painter.setPen(text_color)
        painter.setFont(QFont("Segoe UI", 10, QFont.Bold))
        titulo_seccion = "VISTA SUPERIOR" if self.tipo_vista == "superior" else "VISTA LATERAL"
        painter.drawText(15, 25, titulo_seccion)


class RiggingCanvas(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.geometria = None
        self.num_boxes = 0
        self.is_light = False
        self.setMinimumSize(250, 300)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def actualizar_rigging(self, geometria, num_boxes):
        self.geometria = geometria
        self.num_boxes = num_boxes
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        bg_color = QColor(240, 240, 240) if self.is_light else QColor(35, 35, 35)
        text_color = Qt.black if self.is_light else Qt.white
        
        painter.fillRect(self.rect(), bg_color)
        painter.setPen(text_color)
        painter.setFont(QFont("Segoe UI", 10, QFont.Bold))
        painter.drawText(10, 20, "VISTA RIGGING")

        if not self.geometria: return

        painter.setPen(QPen(QColor(100, 100, 100), 4))
        painter.drawLine(50, 60, 200, 60)
         
        pen_box = QPen(QColor(0, 95, 184), 2)
        brush_box = QColor(180, 180, 180) if self.is_light else QColor(40, 40, 40)
        start_y = 70
        
        for i in range(min(len(self.geometria), self.num_boxes)):
            ang = self.geometria[i].get("angle", 0)
            painter.save()
            painter.translate(125, start_y + (i * 35))
            painter.rotate(max(0, ang)) 
            painter.setPen(pen_box)
            painter.setBrush(brush_box)
            painter.drawRect(-60, 0, 120, 28)
            
            painter.setPen(Qt.black if self.is_light else Qt.yellow)
            painter.setFont(QFont("Arial", 7, QFont.Bold))
            painter.drawText(-50, 18, f"Caja {i+1} ({ang}°)")
            painter.restore()


class ScaleSPLWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(80)
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.step = 1.0
        self.is_light = False

    def set_step(self, step):
        self.step = step
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        h, w = self.height(), self.width()
        
        bg_color = QColor(255, 255, 255) if self.is_light else QColor(25, 25, 25)
        text_color = Qt.black if self.is_light else Qt.white
        painter.fillRect(self.rect(), bg_color)

        grad = QLinearGradient(0, 0, 0, h - 60)
        grad.setColorAt(0.0, QColor(255, 0, 0))     
        grad.setColorAt(0.3, QColor(255, 255, 0))   
        grad.setColorAt(0.7, QColor(0, 255, 0))     
        grad.setColorAt(1.0, QColor(0, 0, 255))     

        painter.fillRect(5, 30, 20, h - 60, grad)
        painter.setPen(text_color)
        painter.setFont(QFont("Segoe UI", 8, QFont.Bold))
        
        db_min, db_max = 85, 120
        usable_h = h - 60
        
        if self.step <= 1.0:
            steps = 7
            for i in range(steps + 1):
                val = db_max - i * (db_max - db_min) / steps
                y_pos = 30 + int(i * usable_h / steps)
                painter.drawText(30, y_pos + 4, f"{int(val)} dB")
        else:
            num_marcas = int((db_max - db_min) / self.step)
            for i in range(num_marcas + 1):
                val = db_max - i * self.step
                y_pos = 30 + int(i * usable_h / num_marcas)
                painter.drawText(30, y_pos + 4, f"{int(val)} dB")

# ==========================================
# WIDGETS MODULARES
# ==========================================
class PanelSplays(QGroupBox):
    splay_modificado = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__("Splay Manual Inter-Gabinete", parent)
        self.lay = QGridLayout(self)
        self.combos = []
        self.opciones_splay = ["0.0", "1.0", "2.0", "3.0", "4.0", "5.0", "6.0", "7.5", "10.0", "12.0"]
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def generar_controles(self, num_cajas, splays_previos=None):
        if splays_previos is None: splays_previos = self.get_splays()

        for i in reversed(range(self.lay.count())): 
            widget = self.lay.itemAt(i).widget()
            if widget: widget.deleteLater()
        self.combos.clear()
        
        num_splays = max(0, num_cajas - 1)
        for i in range(num_splays):
            lbl = QLabel(f"C{i+1}-C{i+2}:")
            cmb = QComboBox()
            cmb.addItems(self.opciones_splay)
            if i < len(splays_previos):
                idx = cmb.findText(str(splays_previos[i]))
                if idx >= 0: cmb.setCurrentIndex(idx)
            
            cmb.currentIndexChanged.connect(self.on_splay_changed)
            self.combos.append(cmb)
            row = i // 2
            col = (i % 2) * 2
            self.lay.addWidget(lbl, row, col)
            self.lay.addWidget(cmb, row, col + 1)
            
    def get_splays(self): return [float(cmb.currentText()) for cmb in self.combos]
        
    def set_splays(self, splays):
        for cmb, val in zip(self.combos, splays):
            idx = cmb.findText(str(val))
            if idx >= 0:
                cmb.blockSignals(True); cmb.setCurrentIndex(idx); cmb.blockSignals(False)
        self.splay_modificado.emit()

    def on_splay_changed(self): self.splay_modificado.emit()


# ==========================================
# DIÁLOGOS
# ==========================================
class ProyectoDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Crear Nuevo Proyecto")
        self.resize(350, 220)
        self.setModal(True)
        layout = QGridLayout(self)
        self.txt_evento = QLineEdit()
        self.txt_fecha = QLineEdit()
        self.txt_lugar = QLineEdit()
        self.txt_resp = QLineEdit()
        layout.addWidget(QLabel("Evento:"), 0, 0); layout.addWidget(self.txt_evento, 0, 1)
        layout.addWidget(QLabel("Fecha:"), 1, 0); layout.addWidget(self.txt_fecha, 1, 1)
        layout.addWidget(QLabel("Lugar:"), 2, 0); layout.addWidget(self.txt_lugar, 2, 1)
        layout.addWidget(QLabel("Responsable:"), 3, 0); layout.addWidget(self.txt_resp, 3, 1)

        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        self.btn_crear = self.buttons.button(QDialogButtonBox.Ok)
        self.btn_crear.setText("Crear")
        self.btn_crear.setEnabled(False)
        layout.addWidget(self.buttons, 4, 0, 1, 2)

        for txt in [self.txt_evento, self.txt_fecha, self.txt_lugar, self.txt_resp]:
            txt.textChanged.connect(self.validar_campos)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

    def validar_campos(self):
        valido = all(t.text().strip() for t in [self.txt_evento, self.txt_fecha, self.txt_lugar, self.txt_resp])
        self.btn_crear.setEnabled(valido)


class AdministrarAltavocesDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Administrar Archivos .a360")
        self.resize(450, 300)
        self.setModal(True)
        layout = QVBoxLayout(self)
        self.lista_ui = QListWidget()
        self.lista_ui.setSelectionMode(QListWidget.MultiSelection)
        layout.addWidget(QLabel("Modelos en Base de Datos Interna:"))
        layout.addWidget(self.lista_ui)
        
        self.btn_eliminar = QPushButton("Eliminar")
        self.btn_eliminar.setStyleSheet("background-color: #d9534f; color: white; padding: 6px;")
        layout.addWidget(self.btn_eliminar, alignment=Qt.AlignRight)

        self.btn_eliminar.clicked.connect(self.eliminar_seleccionados)
        self.refrescar_lista()

    def refrescar_lista(self):
        self.lista_ui.clear()
        for key, info in DB_ALTAVOCES.items():
            item = QListWidgetItem(f"{info['Marca']} - {info['Modelo']}")
            item.setData(Qt.UserRole, key)
            self.lista_ui.addItem(item)

    def eliminar_seleccionados(self):
        items = self.lista_ui.selectedItems()
        for item in items:
            key = item.data(Qt.UserRole)
            if key in DB_ALTAVOCES:
                path = DB_ALTAVOCES[key].get("file_path", "")
                if os.path.exists(path):
                    try: os.remove(path)
                    except: pass
                del DB_ALTAVOCES[key]
        guardar_db()
        self.refrescar_lista()


class AgregarFuenteDialog(QDialog):
    def __init__(self, db_altavoces, parent=None):
        super().__init__(parent)
        self.db_altavoces = db_altavoces
        self.setWindowTitle("Agregar Nueva Fuente Acústica")
        self.resize(400, 250)
        self.setModal(True)
        layout = QGridLayout(self)
        
        self.combo_rol = QComboBox()
        self.combo_rol.addItems(["PA Main L", "PA Main R", "OUTFILL L", "OUTFILL R", "FRONTFILL", "DELAY", "SUB ARRAY"])
        
        self.combo_marca = QComboBox()
        self.combo_marca.addItem("Seleccione Marca")
        self.combo_marca.addItems(sorted(list(set([info["Marca"] for info in self.db_altavoces.values()]))))
        
        self.combo_modelo = QComboBox()
        self.combo_modelo.addItem("Seleccione Modelo")
        self.txt_id = QLineEdit()
        
        layout.addWidget(QLabel("Rol del Sistema:"), 0, 0); layout.addWidget(self.combo_rol, 0, 1)
        layout.addWidget(QLabel("Marca:"), 1, 0); layout.addWidget(self.combo_marca, 1, 1)
        layout.addWidget(QLabel("Modelo:"), 2, 0); layout.addWidget(self.combo_modelo, 2, 1)
        layout.addWidget(QLabel("Identificador:"), 3, 0); layout.addWidget(self.txt_id, 3, 1)
        
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        layout.addWidget(self.buttons, 4, 0, 1, 2)
        
        self.combo_marca.currentIndexChanged.connect(self.filtrar_modelos)
        self.combo_rol.currentIndexChanged.connect(self.autocompletar_id)
        self.buttons.accepted.connect(self.validar_y_aceptar)
        self.buttons.rejected.connect(self.reject)
        self.autocompletar_id()

    def filtrar_modelos(self):
        marca_sel = self.combo_marca.currentText()
        self.combo_modelo.clear(); self.combo_modelo.addItem("Seleccione Modelo")
        for key, info in self.db_altavoces.items():
            if info["Marca"] == marca_sel: self.combo_modelo.addItem(info["Modelo"], key)

    def autocompletar_id(self):
        if not self.txt_id.text().strip() or self.txt_id.text() in [self.combo_rol.itemText(i) for i in range(self.combo_rol.count())]:
            self.txt_id.setText(self.combo_rol.currentText())

    def validar_y_aceptar(self):
        if self.combo_marca.currentIndex() == 0 or self.combo_modelo.currentIndex() == 0 or not self.txt_id.text().strip():
            return QMessageBox.warning(self, "Incompletos", "Seleccione Marca, Modelo y asigne Identificador.")
        self.accept()


# ==========================================
# MAIN WINDOW
# ==========================================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Elo Acoustics - Simulador IA Avanzado")
        self.resize(1500, 900)
        
        self.proyecto_habilitado = False
        self.ambiente_temp = 20.0
        self.ambiente_hum = 60.0
        self.json_path = ""
        self.geometria_actual = []
        self.mapeo_activo = True
        
        self.fuentes_proyecto = {}       
        self.fuente_actual_key = None    
        self.microfonos_proyecto = {}
        self.mic_counter = 0

        self.matriz_lateral_raw = None
        self.matriz_superior_raw = None
        self.grid_x_actual = None
        self.grid_z_actual = None
        self.grid_y_actual = None
        
        self.mediador = motor_mediador.MediadorCache() if motor_mediador else None
    
        self.setStyleSheet(THEME_DARK)
        self.init_ui()
 
        if error_de_importacion != "":
            QMessageBox.critical(self, "Dependencia", f"Faltan motores C++.\n\nDetalles:\n{error_de_importacion}")

    def init_ui(self):
        menu_bar = self.menuBar()
        menu_archivo = menu_bar.addMenu("Archivo")
        menu_archivo.addAction("Nuevo Proyecto", self.ui_nuevo_proyecto)
        menu_archivo.addAction("Abrir Proyecto", self.ui_abrir_proyecto)
        menu_archivo.addAction("Guardar Proyecto", self.ui_guardar_proyecto)
        menu_archivo.addSeparator()
        menu_archivo.addAction("Importar Archivo .a360", self.cargar_archivo_altavoz)
        menu_archivo.addAction("Administrar Archivos .a360", self.ui_administrar_altavoces)

        menu_config = menu_bar.addMenu("Configuración")
        menu_config.addAction("Ambiente", self.ui_configurar_ambiente)
        menu_tema = menu_config.addMenu("Tema")
        
        # Conexiones mejoradas de tema
        menu_tema.addAction("Oscuro", lambda: self.cambiar_tema(False))
        menu_tema.addAction("Claro", lambda: self.cambiar_tema(True))

        widget_central = QWidget()
        self.setCentralWidget(widget_central)
        layout_master = QVBoxLayout(widget_central)

        # TOOLBAR SECUNDARIA
        panel_secundario = QHBoxLayout()
        self.btn_toggle_mapeo = QPushButton("Mostrar Mapeo: ON")
        self.btn_toggle_mapeo.setStyleSheet("background-color: #005fb8; font-weight: bold;")
        self.btn_toggle_mapeo.clicked.connect(self.toggle_mapeo_global)
        
        self.combo_escala_spl = QComboBox()
        self.combo_escala_spl.addItems(["1 Color - 1 db", "1 Color - 3 db", "1 Color - 6 db", "1 Color - 9 db"])
        self.combo_escala_spl.currentIndexChanged.connect(self.actualizar_renderizado_colores)

        self.combo_banda = QComboBox(); self.combo_banda.addItems(["3 octavas", "1 octava", "1/3 octava", "1/6 octava"]); self.combo_banda.setCurrentText("1 octava")
        self.combo_freq = QComboBox(); self.combo_freq.addItems(FREQ_1_6_OCT); self.combo_freq.setCurrentText("1000")
        
        self.btn_autosplay = QPushButton("✨ Auto Splay IA")
        self.btn_autosplay.setStyleSheet("background-color: #8a2be2; color: white; font-weight: bold;")
        self.btn_autosplay.clicked.connect(self.llamar_autosplay_ia)
        
        self.btn_calcular = QPushButton("Generar Predicción")
        self.btn_calcular.setStyleSheet("background-color: #28a745; color: white; font-weight: bold;")
        self.btn_calcular.clicked.connect(self.procesar_calculos_sistema)
        
        self.btn_agregar_fuente = QPushButton("➕ Agregar Fuente")
        self.btn_agregar_fuente.setStyleSheet("background-color: #0078d4; color: white; font-weight: bold;")
        self.btn_agregar_fuente.clicked.connect(self.ui_agregar_fuente)
        
        self.combo_fuente_activa = QComboBox()
        self.combo_fuente_activa.addItem("Fuentes...")
        self.combo_fuente_activa.currentIndexChanged.connect(self.sincronizar_fuente_seleccionada)

        self.btn_agregar_mic = QPushButton("🎙️ Agregar Mic")
        self.btn_agregar_mic.setStyleSheet("background-color: #20b2aa; color: white; font-weight: bold;")
        self.btn_agregar_mic.clicked.connect(self.ui_agregar_mic)

        self.combo_mics = QComboBox()
        self.combo_mics.addItem("Mics...")
        self.combo_mics.currentTextChanged.connect(self.actualizar_mic_freq_resp)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setMaximumWidth(100)

        panel_secundario.addWidget(self.btn_toggle_mapeo)
        panel_secundario.addWidget(QLabel("Escala SPL:"))
        panel_secundario.addWidget(self.combo_escala_spl)
        panel_secundario.addWidget(QLabel("Banda:"))
        panel_secundario.addWidget(self.combo_banda)
        panel_secundario.addWidget(QLabel("FC:"))
        panel_secundario.addWidget(self.combo_freq)
        panel_secundario.addWidget(self.btn_autosplay)
        panel_secundario.addWidget(self.btn_calcular)
        panel_secundario.addWidget(self.btn_agregar_fuente)
        panel_secundario.addWidget(self.combo_fuente_activa)
        panel_secundario.addWidget(self.btn_agregar_mic)
        panel_secundario.addWidget(self.combo_mics)
        panel_secundario.addWidget(self.progress_bar)
        panel_secundario.addStretch()
        layout_master.addLayout(panel_secundario)

        # ÁREA DE TRABAJO SPLITTER
        splitter_principal = QSplitter(Qt.Horizontal)
        splitter_principal.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout_master.addWidget(splitter_principal)

        # PANEL IZQUIERDO: Comandos
        panel_comandos = QWidget()
        panel_comandos.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        lay_comandos = QVBoxLayout(panel_comandos)
        lay_comandos.setContentsMargins(0, 0, 0, 0)
        
        group_audiencia = QGroupBox("Zona de Audiencia")
        lay_aud = QGridLayout(group_audiencia)
        self.txt_aud_ancho = QLineEdit("20"); self.txt_aud_largo = QLineEdit("50"); self.txt_aud_alto = QLineEdit("8")
        lay_aud.addWidget(QLabel("Ancho [m]:"), 0, 0); lay_aud.addWidget(self.txt_aud_ancho, 0, 1)
        lay_aud.addWidget(QLabel("Largo [m]:"), 1, 0); lay_aud.addWidget(self.txt_aud_largo, 1, 1)
        lay_aud.addWidget(QLabel("Alto [m]:"), 2, 0); lay_aud.addWidget(self.txt_aud_alto, 2, 1)
        lay_comandos.addWidget(group_audiencia)

        group_rigging_data = QGroupBox("Datos de Rigging")
        lay_rig = QGridLayout(group_rigging_data)
        self.txt_cajas = QLineEdit("6")
        self.txt_cajas.textChanged.connect(self.on_cajas_changed)
        self.txt_h_bumper = QLineEdit("6.0")
        self.txt_tilt_bumper = QLineEdit("0.0")
        self.lbl_pin_point = QLabel("PUNTO DE BUMPER: --")
        self.lbl_pin_point.setStyleSheet("color: #00ff00; font-weight: bold;")
        lay_rig.addWidget(QLabel("Cant. Gabinetes:"), 0, 0); lay_rig.addWidget(self.txt_cajas, 0, 1)
        lay_rig.addWidget(QLabel("Altura Sistema [m]:"), 1, 0); lay_rig.addWidget(self.txt_h_bumper, 1, 1)
        lay_rig.addWidget(QLabel("Angulación Bumper [°]:"), 2, 0); lay_rig.addWidget(self.txt_tilt_bumper, 2, 1)
        lay_rig.addWidget(self.lbl_pin_point, 3, 0, 1, 2)
        lay_comandos.addWidget(group_rigging_data)

        self.panel_splays = PanelSplays()
        self.panel_splays.generar_controles(int(self.txt_cajas.text()))
        self.panel_splays.splay_modificado.connect(self.actualizar_vistas_tiempo_real)
        lay_comandos.addWidget(self.panel_splays)

        lay_comandos.addStretch()
        splitter_principal.addWidget(panel_comandos)

        # PANEL CENTRAL: Gráficos SPL
        panel_centro = QWidget()
        panel_centro.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        lay_centro = QHBoxLayout(panel_centro)
        lay_centro.setContentsMargins(0, 0, 0, 0)
        
        splitter_canvas = QSplitter(Qt.Vertical) 
        splitter_canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        self.canvas_spl_superior = FastSPLCanvas(tipo_vista="superior")
        
        self.tabs_lateral = QTabWidget()
        self.canvas_spl_lateral = FastSPLCanvas(tipo_vista="lateral")
        self.canvas_freq_resp = FreqResponseCanvas()
        
        self.tabs_lateral.addTab(self.canvas_spl_lateral, "Vista Lateral (SPL)")
        self.tabs_lateral.addTab(self.canvas_freq_resp, "Respuesta de Frecuencia")
        
        self.canvas_spl_superior.posicion_registrada.connect(self.on_item_placed_or_moved)
        self.canvas_spl_superior.posicion_movida.connect(self.on_item_placed_or_moved)
        self.canvas_spl_lateral.posicion_movida.connect(self.on_item_placed_or_moved)
        
        self.txt_aud_largo.textChanged.connect(self.sincronizar_dimensiones_audiencia)
        self.txt_aud_ancho.textChanged.connect(self.sincronizar_dimensiones_audiencia)
        self.txt_aud_alto.textChanged.connect(self.sincronizar_dimensiones_audiencia)
        self.sincronizar_dimensiones_audiencia()

        splitter_canvas.addWidget(self.canvas_spl_superior)
        splitter_canvas.addWidget(self.tabs_lateral)
        
        lay_centro.addWidget(splitter_canvas)
        self.barra_escala_spl = ScaleSPLWidget()
        lay_centro.addWidget(self.barra_escala_spl)
        splitter_principal.addWidget(panel_centro)

        # PANEL DERECHO: Rigging
        panel_derecho = QWidget()
        panel_derecho.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        lay_derecho = QVBoxLayout(panel_derecho)
        lay_derecho.setContentsMargins(0, 0, 0, 0)
        self.canvas_rigging = RiggingCanvas()
        lay_derecho.addWidget(self.canvas_rigging, stretch=2)

        group_reservado = QGroupBox("Métricas Estructurales")
        lay_res = QVBoxLayout(group_reservado)
        self.lbl_peso = QLabel("Peso Total: -- kg")
        self.lbl_ancho_curvado = QLabel("Ancho del Sistema Curvado: -- m")
        self.lbl_despeje_suelo = QLabel("Despeje del Suelo (Clearance): -- m")
        lay_res.addWidget(self.lbl_peso); lay_res.addWidget(self.lbl_ancho_curvado); lay_res.addWidget(self.lbl_despeje_suelo)
        lay_derecho.addWidget(group_reservado, stretch=1)
        splitter_principal.addWidget(panel_derecho)

        splitter_principal.setSizes([280, 600, 250])
        
        self.set_controles_habilitados(False)

    # --- Lógica de Interfaz y Canvas Interactivo ---
    def cambiar_tema(self, is_light):
        self.setStyleSheet(THEME_LIGHT if is_light else THEME_DARK)
        self.canvas_spl_superior.is_light = is_light
        self.canvas_spl_lateral.is_light = is_light
        self.canvas_freq_resp.is_light = is_light
        self.canvas_rigging.is_light = is_light
        self.barra_escala_spl.is_light = is_light
        
        self.canvas_spl_superior.update()
        self.canvas_spl_lateral.update()
        self.canvas_freq_resp.update()
        self.canvas_rigging.update()
        self.barra_escala_spl.update()

    def set_controles_habilitados(self, state):
        self.btn_calcular.setEnabled(state)
        self.btn_autosplay.setEnabled(state)
        self.btn_agregar_fuente.setEnabled(state) 
        self.btn_agregar_mic.setEnabled(state)
        self.txt_aud_ancho.setEnabled(state)
        self.txt_aud_largo.setEnabled(state)
        self.txt_aud_alto.setEnabled(state)
        self.txt_cajas.setEnabled(state)
        self.txt_h_bumper.setEnabled(state)
        self.txt_tilt_bumper.setEnabled(state)
        self.panel_splays.setEnabled(state)

    def sincronizar_dimensiones_audiencia(self):
        try:
            l = float(self.txt_aud_largo.text())
            a = float(self.txt_aud_ancho.text())
            h = float(self.txt_aud_alto.text())
            self.canvas_spl_superior.actualizar_dimensiones(l, a, h)
            self.canvas_spl_lateral.actualizar_dimensiones(l, a, h)
        except: pass

    def on_item_placed_or_moved(self, tipo, item_id, val1, val2, vista):
        if vista == "superior":
            if tipo == "fuente" and item_id in self.fuentes_proyecto:
                self.fuentes_proyecto[item_id]["pos_x"] = val1
                self.fuentes_proyecto[item_id]["pos_y"] = val2
            elif tipo == "mic" and item_id in self.microfonos_proyecto:
                self.microfonos_proyecto[item_id]["pos_x"] = val1
                self.microfonos_proyecto[item_id]["pos_y"] = val2
        elif vista == "lateral":
            if tipo == "mic" and item_id in self.microfonos_proyecto:
                self.microfonos_proyecto[item_id]["pos_x"] = val1
                self.microfonos_proyecto[item_id]["pos_z"] = val2
        self.sincronizar_items_visuales()

    def sincronizar_items_visuales(self):
        self.canvas_spl_superior.fuentes_coords = {k: (v["pos_x"], v["pos_y"]) for k, v in self.fuentes_proyecto.items()}
        self.canvas_spl_superior.mics_coords = {k: (v["pos_x"], v["pos_y"]) for k, v in self.microfonos_proyecto.items()}
        self.canvas_spl_lateral.mics_coords = {k: (v["pos_x"], v.get("pos_z", 1.7)) for k, v in self.microfonos_proyecto.items()}
        
        self.canvas_spl_superior.update()
        self.canvas_spl_lateral.update()

    def actualizar_mic_freq_resp(self, mic_id):
        self.canvas_freq_resp.set_mic(mic_id)

    def on_cajas_changed(self):
        try:
            val = int(self.txt_cajas.text())
            if val > 0:
                self.panel_splays.generar_controles(val)
                self.actualizar_vistas_tiempo_real()
        except ValueError: pass

    def toggle_mapeo_global(self):
        self.mapeo_activo = not self.mapeo_activo
        self.btn_toggle_mapeo.setText(f"Mostrar Mapeo: {'ON' if self.mapeo_activo else 'OFF'}")
        self.canvas_spl_superior.mostrar_mapeo = self.mapeo_activo
        self.canvas_spl_lateral.mostrar_mapeo = self.mapeo_activo
        self.canvas_spl_superior.update()
        self.canvas_spl_lateral.update()

    # --- Archivos y Configuración ---
    def ui_nuevo_proyecto(self):
        dlg = ProyectoDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            self.proyecto_habilitado = True
            self.set_controles_habilitados(True)
            QMessageBox.information(self, "Proyecto", f"Proyecto '{dlg.txt_evento.text()}' inicializado.")

    def ui_abrir_proyecto(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Abrir", "", "Space (*.space)")
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f: data = json.load(f)
                self.ambiente_temp = data.get("temperatura", 20.0)
                self.ambiente_hum = data.get("humedad", 60.0)
                self.txt_aud_ancho.setText(str(data.get("ancho", 20)))
                self.txt_aud_largo.setText(str(data.get("largo", 50)))
                self.txt_aud_alto.setText(str(data.get("alto", 8)))
                self.proyecto_habilitado = True
                self.set_controles_habilitados(True)
            except Exception as e: QMessageBox.critical(self, "Error", str(e))

    def ui_guardar_proyecto(self):
        if not self.proyecto_habilitado: return
        file_path, _ = QFileDialog.getSaveFileName(self, "Guardar", "", "Space (*.space)")
        if file_path:
            try:
                estado = {
                    "temperatura": self.ambiente_temp, "humedad": self.ambiente_hum,
                    "ancho": float(self.txt_aud_ancho.text()), "largo": float(self.txt_aud_largo.text()),
                    "alto": float(self.txt_aud_alto.text())
                }
                with open(file_path, 'w', encoding='utf-8') as f: json.dump(estado, f)
            except Exception as e: QMessageBox.critical(self, "Error", str(e))

    def ui_configurar_ambiente(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Entorno")
        lay = QGridLayout(dialog)
        txt_t = QLineEdit(str(self.ambiente_temp)); txt_h = QLineEdit(str(self.ambiente_hum))
        lay.addWidget(QLabel("Temp (°C):"), 0, 0); lay.addWidget(txt_t, 0, 1)
        lay.addWidget(QLabel("Hum (%):"), 1, 0); lay.addWidget(txt_h, 1, 1)
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, dialog)
        lay.addWidget(bb, 2, 0, 1, 2)
        bb.accepted.connect(dialog.accept); bb.rejected.connect(dialog.reject)
        if dialog.exec_() == QDialog.Accepted:
            try: self.ambiente_temp, self.ambiente_hum = float(txt_t.text()), float(txt_h.text())
            except: pass

    # --- Gestión de Fuentes y Mics ---
    def cargar_archivo_altavoz(self):
        if motor_acustico is None: return QMessageBox.warning(self, "Atención", "Motor acústico no disponible.")
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(self, "Importar .a360", "", "Archivos (*.a360 *.json)", options=options)
        if file_path:
            try:
                db_key, marca, modelo, motor_data, tmp_path = GestorArchivosA360.importar_archivo(file_path)
                DB_ALTAVOCES[db_key] = {"Marca": marca, "Modelo": modelo, "data": motor_data, "file_path": tmp_path}
                guardar_db()
                QMessageBox.information(self, "Éxito", f"Contenedor {marca} importado y guardado correctamente.")
            except Exception as e: QMessageBox.critical(self, "Error", str(e))

    def ui_administrar_altavoces(self):
        AdministrarAltavocesDialog(self).exec_()

    def ui_agregar_fuente(self):
        dlg = AgregarFuenteDialog(DB_ALTAVOCES, self)
        if dlg.exec_() == QDialog.Accepted:
            id_fuente = dlg.txt_id.text().strip()
            db_key = dlg.combo_modelo.currentData() 
            if id_fuente in self.fuentes_proyecto: return QMessageBox.warning(self, "Duplicado", "La fuente ya existe.")
            self.fuentes_proyecto[id_fuente] = {
                "rol": dlg.combo_rol.currentText(), "db_key": db_key,
                "cajas": "6", "h_bumper": "6.0", "tilt_bumper": "0.0",
                "splays": [0.0, 0.0, 0.0, 0.0, 0.0], "geometria": [],
                "pos_x": 0.0, "pos_y": 0.0
            }
            self.combo_fuente_activa.addItem(f"{id_fuente} ({dlg.combo_rol.currentText()})", id_fuente)
            self.combo_fuente_activa.setCurrentIndex(self.combo_fuente_activa.findData(id_fuente))
            self.canvas_spl_superior.iniciar_colocacion("fuente", id_fuente)

    def ui_agregar_mic(self):
        self.mic_counter += 1
        mic_id = f"M{self.mic_counter}"
        self.microfonos_proyecto[mic_id] = {"pos_x": 0.0, "pos_y": 0.0, "pos_z": 1.7}
        self.combo_mics.addItem(mic_id)
        self.combo_mics.setCurrentText(mic_id)
        self.canvas_spl_superior.iniciar_colocacion("mic", mic_id)

    def guardar_estado_fuente_actual(self):
        if self.fuente_actual_key and self.fuente_actual_key in self.fuentes_proyecto:
            estado = self.fuentes_proyecto[self.fuente_actual_key]
            estado["cajas"] = self.txt_cajas.text()
            estado["h_bumper"] = self.txt_h_bumper.text()
            estado["tilt_bumper"] = self.txt_tilt_bumper.text()
            estado["splays"] = self.panel_splays.get_splays()

    def sincronizar_fuente_seleccionada(self, index):
        self.guardar_estado_fuente_actual()
        if index <= 0:
            self.fuente_actual_key = None; return
            
        id_fuente = self.combo_fuente_activa.itemData(index)
        self.fuente_actual_key = id_fuente
        estado_nuevo = self.fuentes_proyecto[id_fuente]
        
        self.txt_cajas.blockSignals(True); self.txt_h_bumper.blockSignals(True); self.txt_tilt_bumper.blockSignals(True)
        try:
            self.txt_cajas.setText(estado_nuevo["cajas"])
            self.txt_h_bumper.setText(estado_nuevo["h_bumper"])
            self.txt_tilt_bumper.setText(estado_nuevo["tilt_bumper"])
            
            cajas_num = int(estado_nuevo["cajas"]) if estado_nuevo["cajas"].isdigit() else 1
            self.panel_splays.generar_controles(cajas_num, estado_nuevo["splays"])
            
            db_key = estado_nuevo["db_key"]
            if db_key in DB_ALTAVOCES:
                self.json_path = DB_ALTAVOCES[db_key].get("file_path", "")
                if motor_acustico: motor_acustico.cargar_json_motor(self.json_path)
                if motor_rigging: motor_rigging.cargar_json_rigging(self.json_path)
                
            self.actualizar_vistas_tiempo_real()
        finally:
            self.txt_cajas.blockSignals(False); self.txt_h_bumper.blockSignals(False); self.txt_tilt_bumper.blockSignals(False)

    # --- Motores y Predicción ---
    def actualizar_vistas_tiempo_real(self):
        try:
            num_boxes = int(self.txt_cajas.text())
            splays = self.panel_splays.get_splays()
            geom_mock = []
            hz, curr_angle = float(self.txt_h_bumper.text()), float(self.txt_tilt_bumper.text())
            for i in range(num_boxes):
                geom_mock.append({"x": 0.0, "z": hz - (i * 0.4), "angle": curr_angle})
                if i < len(splays): curr_angle += splays[i] 
            self.canvas_rigging.actualizar_rigging(geom_mock, num_boxes)
        except: pass

    def llamar_autosplay_ia(self):
        if motor_autosplay is None: return
        try:
            cajas = int(self.txt_cajas.text())
            prediccion_splays = motor_autosplay.predecir_splays(cajas, float(self.txt_h_bumper.text()), float(self.txt_tilt_bumper.text()))
            self.panel_splays.set_splays(prediccion_splays)
            self.btn_autosplay.setText("✅ Ángulos Aplicados")
        except Exception as e: QMessageBox.warning(self, "Error IA", str(e))

    def procesar_calculos_sistema(self):
        self.guardar_estado_fuente_actual()
        if not (motor_acustico and motor_rigging and self.mediador) or not self.json_path:
            return QMessageBox.warning(self, "Aviso", "Motores C++ o archivo base no disponibles.")

        try:
            motor_acustico.cargar_json_motor(self.json_path)
            motor_rigging.cargar_json_rigging(self.json_path)
            
            num_boxes = int(self.txt_cajas.text())
            h_b, t_b = float(self.txt_h_bumper.text()), float(self.txt_tilt_bumper.text())
            splays = self.panel_splays.get_splays()
            
            if self.mediador.requiere_recalculo_rigging(self.json_path, num_boxes, h_b, t_b, splays):
                self.geometria_actual = motor_rigging.calcular_geometria_rigging(self.json_path, num_boxes, h_b, t_b, splays)
                self.mediador.guardar_geometria(self.geometria_actual)
            else:
                self.geometria_actual = self.mediador.obtener_geometria()

            if not self.geometria_actual: return

            metrics = motor_rigging.calcular_metricas_sistema(self.json_path, num_boxes, self.geometria_actual)
            self.lbl_peso.setText(f"Peso Total: {metrics.get('peso_total', 0.0):.2f} kg")
            self.lbl_ancho_curvado.setText(f"Ancho Curvado: {metrics.get('longitud_arreglo', 0.0) * 0.88:.2f} m")
            self.lbl_despeje_suelo.setText(f"Clearance: {metrics.get('clearance', 0.0):.2f} m")
            self.lbl_pin_point.setText(f"Pin Point Sugerido: Centro # {int(abs(t_b) + 3)}")

            l_aud, h_aud = float(self.txt_aud_largo.text()), float(self.txt_aud_alto.text())
            ancho_aud = float(self.txt_aud_ancho.text())
            
            self.grid_x_actual = np.linspace(0.0, l_aud, 160)
            self.grid_z_actual = np.linspace(-2.0, h_aud + 4.0, 100)
            self.grid_y_actual = np.linspace(-ancho_aud/2, ancho_aud/2, 100)

            self.canvas_spl_superior.set_data(None, self.grid_x_actual, self.grid_y_actual, self.geometria_actual)
            self.canvas_rigging.actualizar_rigging(self.geometria_actual, num_boxes)

            self.matriz_lateral_raw = None
            self.matriz_superior_raw = None
            self.progress_bar.setValue(20)
            self.btn_calcular.setEnabled(False)

            self.worker_lateral = CalculoMapeoWorker("lateral", self.json_path, self.geometria_actual, self.grid_x_actual, self.grid_z_actual, float(self.combo_freq.currentText()), 0.0, self.ambiente_temp, self.ambiente_hum)
            self.worker_lateral.calculo_terminado.connect(self.finalizar_calculo_hilo)
            self.worker_lateral.start()
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e)); self.btn_calcular.setEnabled(True)

    def finalizar_calculo_hilo(self, g1, g2, tipo):
        if tipo == "lateral":
            if self.worker_lateral.resultado_matriz is None or self.worker_lateral.resultado_matriz.size == 0: 
                self.btn_calcular.setEnabled(True); return
            self.matriz_lateral_raw = self.worker_lateral.resultado_matriz
            self.progress_bar.setValue(60)
            
            self.worker_superior = CalculoMapeoWorker("superior", self.json_path, self.geometria_actual, g1, self.grid_y_actual, float(self.combo_freq.currentText()), 1.7, self.ambiente_temp, self.ambiente_hum)
            self.worker_superior.calculo_terminado.connect(self.finalizar_calculo_hilo)
            self.worker_superior.start()

        elif tipo == "superior":
            if self.worker_superior.resultado_matriz is None or self.worker_superior.resultado_matriz.size == 0: 
                self.btn_calcular.setEnabled(True); return
            self.matriz_superior_raw = self.worker_superior.resultado_matriz
            self.progress_bar.setValue(100)
            self.btn_calcular.setEnabled(True)
            
        self.actualizar_renderizado_colores()

    def actualizar_renderizado_colores(self):
        if not hasattr(self, 'combo_escala_spl'): return
        texto_escala = self.combo_escala_spl.currentText()
        if "3 db" in texto_escala: step = 3.0
        elif "6 db" in texto_escala: step = 6.0
        elif "9 db" in texto_escala: step = 9.0
        else: step = 1.0

        self.barra_escala_spl.set_step(step)

        if self.matriz_lateral_raw is not None and self.matriz_lateral_raw.size > 0:
            mat_cuant = np.floor(self.matriz_lateral_raw / step) * step
            rgba = motor_grafico.renderizar_mapa_colores(np.ascontiguousarray(np.flipud(mat_cuant)), 85.0, 120.0)
            self.canvas_spl_lateral.set_data(rgba, self.grid_x_actual, self.grid_z_actual, self.geometria_actual)

        if self.matriz_superior_raw is not None and self.matriz_superior_raw.size > 0:
            mat_cuant_sup = np.floor(self.matriz_superior_raw / step) * step
            rgba_sup = motor_grafico.renderizar_mapa_colores(np.ascontiguousarray(np.flipud(mat_cuant_sup)), 85.0, 120.0)
            self.canvas_spl_superior.set_data(rgba_sup, self.grid_x_actual, self.grid_y_actual, self.geometria_actual)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
