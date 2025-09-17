from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6 import QtCore, QtGui, QtWidgets as QtW
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
import math
from matplotlib import cm, colors
from matplotlib.ticker import MultipleLocator
from mpl_toolkits.axes_grid1 import make_axes_locatable
from .plot_utils import (
    prepare_figure_layout,
    axis_wide_colorbar,
    center_title_over_axes,
    title_above_axes,
    reserve_axes_margins,
    shrink_axes_vertical,
)

from ..io import read_traces_txt
from ..plots import plot_tracemap
from .widgets import MplCanvas


class _WheelBlocker(QtCore.QObject):
    def eventFilter(self, obj, event):
        if event.type() == QtCore.QEvent.Wheel:
            return True  # block all wheel events
        return super().eventFilter(obj, event)


class MainWindow(QtW.QMainWindow):
    def __init__(self, parent: Optional[QtW.QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("PyFracPaQ")
        self.resize(1200, 800)

        # Data
        self._segments = []
        # Axis flip state for computations/plots
        self._flip_x = False
        self._flip_y = False

        # Central container (body only)
        central = QtW.QWidget()
        self.setCentralWidget(central)
        root = QtW.QVBoxLayout(central)

        # Body: left input panel + right content (tabs + canvas + footer)
        body = QtW.QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        # Add a subtle gap between the left panel and the central canvas for symmetry
        body.setSpacing(8)
        root.addLayout(body, 1)

        left = self._build_left_panel()
        body.addWidget(left, 0)

        right = self._build_right_panel()
        body.addWidget(right, 1)

        # No menu bar

        self.statusBar().showMessage("Ready")
        # Flip indicator on status bar
        self._flip_label = QtW.QLabel("")
        self.statusBar().addPermanentWidget(self._flip_label)
        self._update_flip_indicator()
        # Manage multiple plot windows keyed by content
        self._plot_windows = {}
        # Initial left message
        if hasattr(self, "_set_left_message"):
            self._set_left_message("Ready!")
        # Apply unified behavior to all QDoubleSpinBox: hide arrows and disable wheel
        self._apply_spinbox_preferences()

    # ----- UI builders -----
    def _build_left_panel(self) -> QtW.QWidget:
        # Left controls panel titled "Input"
        left = QtW.QGroupBox("Input")
        v = QtW.QVBoxLayout(left)
        # Acolchoado uniforme de 8 px em torno do conteúdo de Input
        v.setContentsMargins(8, 8, 8, 8)

        # Filename row + Browse
        row = QtW.QGridLayout()
        row.addWidget(QtW.QLabel("Filename"), 0, 0)
        self.edit_filename = QtW.QLineEdit()
        self.edit_filename.setPlaceholderText("[no file selected]")
        row.addWidget(self.edit_filename, 0, 1, 1, 2)
        v.addLayout(row)

        # Input file type
        type_box = QtW.QGroupBox("Input file type")
        type_layout = QtW.QGridLayout(type_box)
        self.rb_image = QtW.QRadioButton("Image file")
        self.rb_node = QtW.QRadioButton("Node file")
        self.rb_node.setChecked(True)
        type_layout.addWidget(self.rb_image, 0, 0)
        self.btn_browse = QtW.QPushButton("Browse…")
        self.btn_browse.clicked.connect(self.action_browse)
        type_layout.addWidget(self.btn_browse, 0, 1)
        type_layout.addWidget(self.rb_node, 1, 0)
        v.addWidget(type_box)

        # Image file / Hough transform options
        hough_box = QtW.QGroupBox("Image file/Hough transform option")
        hg = QtW.QGridLayout(hough_box)
        r = 0
        hg.addWidget(QtW.QLabel("Number of Hough peaks"), r, 0)
        self.edit_houghpeaks = QtW.QSpinBox(); self.edit_houghpeaks.setRange(0, 9999); self.edit_houghpeaks.setValue(1000); self.edit_houghpeaks.setEnabled(False)
        hg.addWidget(self.edit_houghpeaks, r, 1); r += 1
        hg.addWidget(QtW.QLabel("Hough threshold"), r, 0)
        self.edit_houghthreshold = QtW.QDoubleSpinBox(); self.edit_houghthreshold.setRange(0.0, 1.0); self.edit_houghthreshold.setSingleStep(0.01); self.edit_houghthreshold.setValue(0.33); self.edit_houghthreshold.setEnabled(False)
        hg.addWidget(self.edit_houghthreshold, r, 1); r += 1
        hg.addWidget(QtW.QLabel("Merge gaps less than"), r, 0)
        self.edit_fillgap = QtW.QSpinBox(); self.edit_fillgap.setRange(0, 9999); self.edit_fillgap.setValue(5); self.edit_fillgap.setEnabled(False)
        hg.addWidget(self.edit_fillgap, r, 1); r += 1
        hg.addWidget(QtW.QLabel("Discard lengths less than"), r, 0)
        self.edit_minlength = QtW.QSpinBox(); self.edit_minlength.setRange(0, 999999); self.edit_minlength.setValue(3); self.edit_minlength.setEnabled(False)
        hg.addWidget(self.edit_minlength, r, 1); r += 1
        self.rb_image.toggled.connect(self._toggle_hough_fields)
        v.addWidget(hough_box)

        # Scaling
        scale_box = QtW.QGroupBox("Scaling")
        sg = QtW.QGridLayout(scale_box)
        sg.addWidget(QtW.QLabel("(pixels/metre)"), 0, 0)
        self.edit_scale = QtW.QLineEdit(); sg.addWidget(self.edit_scale, 0, 1)
        v.addWidget(scale_box)

        # Flip + Preview (left panel controls)
        btns = QtW.QHBoxLayout()
        self.btn_flipx_left = QtW.QPushButton("Flip X-axis"); self.btn_flipx_left.setCheckable(True); self.btn_flipx_left.setChecked(self._flip_x); self.btn_flipx_left.setEnabled(False); self.btn_flipx_left.clicked.connect(self._on_flip_x)
        self.btn_flipy_left = QtW.QPushButton("Flip Y-axis"); self.btn_flipy_left.setCheckable(True); self.btn_flipy_left.setChecked(self._flip_y); self.btn_flipy_left.setEnabled(False); self.btn_flipy_left.clicked.connect(self._on_flip_y)
        self.btn_preview = QtW.QPushButton("Preview"); self.btn_preview.setEnabled(False)
        self.btn_preview.clicked.connect(self.action_preview)
        btns.addWidget(self.btn_flipx_left); btns.addWidget(self.btn_flipy_left); btns.addWidget(self.btn_preview)
        v.addLayout(btns)

        # Statistics placeholder
        stats_box = QtW.QGroupBox("Statistics for selected file")
        stats_layout = QtW.QVBoxLayout(stats_box)
        self.txt_stats = QtW.QTextEdit(); self.txt_stats.setReadOnly(True); self.txt_stats.setPlaceholderText("")
        stats_layout.addWidget(self.txt_stats)
        v.addWidget(stats_box, 1)

        v.addStretch(0)
        return left

    def _build_right_panel(self) -> QtW.QWidget:
        # Right side with tabs on top, main map canvas, and footer controls
        right = QtW.QWidget(); v = QtW.QVBoxLayout(right)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(6)

        # Tabs (disable others initially to mirror screenshot)
        self.tabs = QtW.QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setTabPosition(QtW.QTabWidget.North)
        self.tab_maps = QtW.QWidget(); self.tabs.addTab(self.tab_maps, "Maps")
        self.tab_lengths = QtW.QWidget(); self.tabs.addTab(self.tab_lengths, "Lengths")
        self.tab_angles = QtW.QWidget(); self.tabs.addTab(self.tab_angles, "Angles")
        self.tab_fluid = QtW.QWidget(); self.tabs.addTab(self.tab_fluid, "Fluid flow")
        self.tab_wavelets = QtW.QWidget(); self.tabs.addTab(self.tab_wavelets, "Wavelets")
        self.tab_graphs = QtW.QWidget(); self.tabs.addTab(self.tab_graphs, "Graphs")
        # Tabs start disabled; enable all after Preview
        # Top row: canvas on the left, tabs+paged content on the right
        top_row = QtW.QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        top_row.setSpacing(8)
        self.canvas_map = MplCanvas(width=8, height=6, dpi=100, polar=False)
        # Placeholder: match surrounding background and hide axes until data is plotted
        try:
            bg = self.palette().color(self.backgroundRole())
            self.canvas_map.set_placeholder_background(bg)
        except Exception:
            pass
        # Now that canvas exists, wire flip buttons (handlers already connected)
        top_row.addWidget(self.canvas_map, 3)
        # Rely on layout spacing only to keep symmetric gaps left/right
        # Right column holds the tabs pages on top and the footer directly below them
        right_col_w = QtW.QWidget()
        right_col = QtW.QVBoxLayout(right_col_w)
        right_col.setContentsMargins(0, 0, 0, 0)
        right_col.setSpacing(6)
        self.tabs.setContentsMargins(0, 0, 0, 0)
        right_col.addWidget(self.tabs)
        # Disable entire tabs area until Preview loads data
        self.tabs.setEnabled(False)
        top_row.addWidget(right_col_w, 2)
        v.addLayout(top_row, 1)

        # Maps tab content: options only (no canvas inside tabs)
        maps_layout = QtW.QVBoxLayout(self.tab_maps)
        # Pequeno espaço entre a barra de abas e o título do conteúdo
        maps_layout.setContentsMargins(0, 8, 0, 0)
        maps_layout.setSpacing(4)
        opts = QtW.QWidget(); og = QtW.QGridLayout(opts); og.setColumnStretch(0, 1); og.setColumnStretch(1, 1)
        # Tighten container margins to eliminate top gap
        og.setContentsMargins(0, 0, 0, 0)
        og.setHorizontalSpacing(8)
        og.setVerticalSpacing(4)

        grp_maps = QtW.QGroupBox("Maps")
        gm = QtW.QVBoxLayout(grp_maps)
        # Adicionar acolchoado nas laterais/base; topo leve para não abrir um grande vão
        gm.setContentsMargins(8, 4, 8, 8)
        gm.setSpacing(3)
        self.chk_traces_segments = QtW.QCheckBox("Traces, segments")
        # "Show nodes" subordinado (recuado e dependente de "Traces, segments")
        self.chk_show_nodes = QtW.QCheckBox("Show nodes")
        indented = QtW.QWidget(); indented_layout = QtW.QHBoxLayout(indented)
        # Mais recuo para "Show nodes"
        indented_layout.setContentsMargins(12, 0, 0, 0)
        indented_layout.setSpacing(0)
        indented_layout.addWidget(self.chk_show_nodes)
        # Construir um bloco compacto para o topo esquerdo
        traces_box = QtW.QWidget(); tv = QtW.QVBoxLayout(traces_box)
        # Recuo à esquerda e 20px acima de "Traces, segments"
        tv.setContentsMargins(4, 20, 0, 0)
        # Espaçamento maior entre "Traces, segments" e "Show nodes"
        tv.setSpacing(20)
        tv.addWidget(self.chk_traces_segments)
        tv.addWidget(indented)
        # Toggle enablement e replot quando pai muda
        self.chk_traces_segments.toggled.connect(self._toggle_traces_options)
        # Build nested groups to live inside "Maps"
        grp_fs = QtW.QGroupBox("Fracture stability")
        gf = QtW.QGridLayout(grp_fs); r = 0
        gf.setContentsMargins(4, 20, 4, 20)
        gf.setHorizontalSpacing(6)
        gf.setVerticalSpacing(20)
        self.chk_slip = QtW.QCheckBox("Slip tendency"); gf.addWidget(self.chk_slip, r, 0, 1, 2); r += 1
        self.chk_dilation = QtW.QCheckBox("Dilation tendency"); gf.addWidget(self.chk_dilation, r, 0, 1, 2); r += 1
        self.chk_suscept = QtW.QCheckBox("Fracture susceptibility"); gf.addWidget(self.chk_suscept, r, 0, 1, 2); r += 1
        self.chk_crit = QtW.QCheckBox("Critically stressed fractures"); gf.addWidget(self.chk_crit, r, 0, 1, 2); r += 1
        # Bloco de parâmetros subordinado ao "Critically stressed fractures" (recuado)
        crit_params = QtW.QWidget(); cp = QtW.QGridLayout(crit_params); cr = 0
        # Recuo menor para indicar relação com todos os 4 checkboxes
        cp.setContentsMargins(4, 0, 0, 0)
        cp.setHorizontalSpacing(6)
        cp.setVerticalSpacing(20)
        def add_param(label: str, default: float, decimals: int = 1):
            nonlocal cr
            lab = QtW.QLabel(label)
            cp.addWidget(lab, cr, 0)
            sp = QtW.QDoubleSpinBox(); sp.setRange(-1e6, 1e6); sp.setDecimals(decimals); sp.setValue(default)
            cp.addWidget(sp, cr, 1); cr += 1
            return lab, sp
        self.lbl_sigma1, self.sp_sigma1 = add_param("Sigma 1, MPa", 100.0)
        self.lbl_sigma2, self.sp_sigma2 = add_param("Sigma 2, MPa", 50.0)
        self.lbl_angle, self.sp_angle = add_param("Angle of Sigma 1 from Y-axis", 0.0, decimals=0)
        self.lbl_cohesion, self.sp_cohesion = add_param("Cohesion, MPa", 0.0)
        self.lbl_pore, self.sp_pore = add_param("Pore pressure, MPa", 0.0)
        self.lbl_fric, self.sp_fric = add_param("Friction coefficient", 0.6, decimals=2)
        # Inicialmente desabilitado até que qualquer uma das opções esteja marcada
        crit_params.setEnabled(False)
        gf.addWidget(crit_params, r, 0, 1, 2); r += 1
        # Habilitar parâmetros conforme necessidade de cada cálculo (união dos selecionados)
        def _update_stress_params_enabled(_: bool = False) -> None:
            sel_slip = self.chk_slip.isChecked()
            sel_dil = self.chk_dilation.isChecked()
            sel_susc = self.chk_suscept.isChecked()
            sel_csf = self.chk_crit.isChecked()
            any_on = sel_slip or sel_dil or sel_susc or sel_csf
            # Necessidades por cálculo
            need_basic = any_on  # sigma1, sigma2, angle usados por todos os quatro
            # Habilitação separada:
            # - cohesion e friction também para Slip/Dilation (além de Susc/CSF)
            # - pore pressure: habilitar também para Slip/Dilation (mesmo critério dos demais)
            need_muC0 = sel_slip or sel_dil or sel_susc or sel_csf
            need_pore = sel_slip or sel_dil or sel_susc or sel_csf
            # Habilitar/desabilitar bloco geral e campos específicos
            crit_params.setEnabled(any_on)
            for lab, sp in [
                (self.lbl_sigma1, self.sp_sigma1),
                (self.lbl_sigma2, self.sp_sigma2),
                (self.lbl_angle, self.sp_angle),
            ]:
                lab.setEnabled(need_basic)
                sp.setEnabled(need_basic)
            # Cohesion e friction: habilitar para Slip/Dilation/Susc/CSF
            for lab, sp in [
                (self.lbl_cohesion, self.sp_cohesion),
                (self.lbl_fric, self.sp_fric),
            ]:
                lab.setEnabled(need_muC0)
                sp.setEnabled(need_muC0)
            # Pore pressure: apenas Susc/CSF
            self.lbl_pore.setEnabled(need_pore)
            self.sp_pore.setEnabled(need_pore)
        self.chk_slip.toggled.connect(_update_stress_params_enabled)
        self.chk_dilation.toggled.connect(_update_stress_params_enabled)
        self.chk_suscept.toggled.connect(_update_stress_params_enabled)
        self.chk_crit.toggled.connect(_update_stress_params_enabled)
        # Estado inicial
        _update_stress_params_enabled()
        # Add to Maps group later via a grid

        grp_cc = QtW.QGroupBox("Colour-coded maps")
        gc = QtW.QVBoxLayout(grp_cc)
        # Topo mínimo para subir; laterais iguais aos outros grupos
        gc.setContentsMargins(4, 20, 4, 20)
        gc.setSpacing(20)
        self.chk_traces_by_len = QtW.QCheckBox("Traces, by length")
        self.chk_segments_by_len = QtW.QCheckBox("Segments, by length")
        self.chk_segments_by_strike = QtW.QCheckBox("Segments, by strike")
        gc.addWidget(self.chk_traces_by_len)
        gc.addWidget(self.chk_segments_by_len)
        gc.addWidget(self.chk_segments_by_strike)
        # Add to Maps group later via a grid

        # Use '&&' to render a literal '&' in Qt labels
        grp_id = QtW.QGroupBox("Intensity && Density")
        gi = QtW.QGridLayout(grp_id); r = 0
        gi.setContentsMargins(4, 20, 4, 20)
        gi.setHorizontalSpacing(6)
        gi.setVerticalSpacing(20)
        self.chk_est_intensity = QtW.QCheckBox("Estimated Intensity, P21"); gi.addWidget(self.chk_est_intensity, r, 0, 1, 2); r += 1
        self.chk_est_density = QtW.QCheckBox("Estimated Density, P20"); gi.addWidget(self.chk_est_density, r, 0, 1, 2); r += 1
        # Subordinados a Density (apenas habilitados quando Density está marcado) e recuados
        self.chk_showcircles = QtW.QCheckBox("Show scan circles"); self.chk_showcircles.setEnabled(False)
        ind_circles = QtW.QWidget(); ind_circles_l = QtW.QHBoxLayout(ind_circles)
        ind_circles_l.setContentsMargins(12, 0, 0, 0)
        ind_circles_l.setSpacing(6)
        ind_circles_l.addWidget(self.chk_showcircles)
        gi.addWidget(ind_circles, r, 0, 1, 2); r += 1
        # Guardar e iniciar desabilitado para que o texto fique esmaecido
        self.ind_circles = ind_circles
        self.ind_circles.setEnabled(False)
        ind_num = QtW.QWidget(); ind_num_l = QtW.QHBoxLayout(ind_num)
        ind_num_l.setContentsMargins(12, 0, 0, 0)
        ind_num_l.setSpacing(6)
        lbl_ncircles = QtW.QLabel("Number of scan circles")
        ind_num_l.addWidget(lbl_ncircles)
        self.spin_ncircles = QtW.QSpinBox(); self.spin_ncircles.setRange(0, 10000); self.spin_ncircles.setValue(12); self.spin_ncircles.setEnabled(False)
        ind_num_l.addWidget(self.spin_ncircles)
        gi.addWidget(ind_num, r, 0, 1, 2); r += 1
        # Guardar e iniciar desabilitado para refletir estado visual (texto esmaecido)
        self.ind_num = ind_num
        self.ind_num.setEnabled(False)
        def toggle_density(on: bool):
            # Habilitar/Desabilitar blocos indentados para refletir no texto (cor)
            self.ind_circles.setEnabled(on)
            self.ind_num.setEnabled(on)
            # Controles internos seguem o estado
            self.chk_showcircles.setEnabled(on)
            self.spin_ncircles.setEnabled(on)
            if not on and self.chk_showcircles.isChecked():
                # Ao desmarcar Density, desmarcar também Show scan circles
                self.chk_showcircles.setChecked(False)
        self.chk_est_density.toggled.connect(toggle_density)
        # Add to Maps group later via a grid

        # Grid interno em "Maps" para alinhar como no MATLAB
        maps_inner = QtW.QWidget(); ig = QtW.QGridLayout(maps_inner)
        ig.setContentsMargins(0, 0, 0, 0)
        ig.setHorizontalSpacing(8)
        ig.setVerticalSpacing(20)
        ig.setColumnStretch(0, 1); ig.setColumnStretch(1, 1)
        # Control vertical sizing: todos compactos; direita empilhada (Colour-coded maps em cima,
        # Intensity & Density logo abaixo)
        grp_fs.setSizePolicy(QtW.QSizePolicy.Preferred, QtW.QSizePolicy.Maximum)
        grp_cc.setSizePolicy(QtW.QSizePolicy.Preferred, QtW.QSizePolicy.Maximum)
        grp_id.setSizePolicy(QtW.QSizePolicy.Preferred, QtW.QSizePolicy.Maximum)
        traces_box.setSizePolicy(QtW.QSizePolicy.Preferred, QtW.QSizePolicy.Maximum)
        # Coluna direita empilhada: Colour-coded + Intensity & Density (mais para cima)
        right_stack = QtW.QWidget(); right_v = QtW.QVBoxLayout(right_stack)
        right_v.setContentsMargins(0, 0, 0, 0)
        right_v.setSpacing(20)
        right_v.addWidget(grp_cc)
        right_v.addWidget(grp_id)
        # Linha superior: à esquerda o bloco Traces/Show nodes; à direita a pilha direita (ocupando 2 linhas)
        ig.addWidget(traces_box, 0, 0)
        ig.addWidget(right_stack, 0, 1, 2, 1, QtCore.Qt.AlignTop)
        # Linha inferior à esquerda: Fracture stability
        ig.addWidget(grp_fs, 1, 0)
        # Não esticar para baixo; manter espaçamentos uniformes
        ig.setRowStretch(0, 0)
        ig.setRowStretch(1, 0)
        # Anchor inner grid to the very top of the "Maps" group
        gm.addWidget(maps_inner, 0, QtCore.Qt.AlignTop)

        og.addWidget(grp_maps, 0, 0, 2, 2)

        maps_layout.addWidget(opts, 1)
        # Inicializa o estado subordinado dos nós
        self._toggle_traces_options(self.chk_traces_segments.isChecked())

        # Footer: filename tag, Run, Exit, version/email and large logo
        footer = QtW.QGridLayout()
        footer.addWidget(QtW.QLabel("Filename tag for this run"), 0, 0)
        self.edit_run_tag = QtW.QLineEdit("Run1"); footer.addWidget(self.edit_run_tag, 0, 1)
        self.btn_run = QtW.QPushButton("Run"); self.btn_run.setEnabled(False); footer.addWidget(self.btn_run, 1, 0)
        self.btn_run.clicked.connect(self.action_run)
        self.btn_exit = QtW.QPushButton("Exit"); self.btn_exit.clicked.connect(self.close); footer.addWidget(self.btn_exit, 1, 1)
        # Version/email
        self.lbl_ver = QtW.QLabel("Version 2.8, March 2021   E-mail: info@fracpaq.com")
        footer.addWidget(self.lbl_ver, 2, 0, 1, 2)
        # Large logo at bottom-right
        self.lbl_biglogo = QtW.QLabel()
        self._set_big_logo()
        footer.addWidget(self.lbl_biglogo, 0, 2, 3, 1)
        footer.setColumnStretch(2, 1)
        # Place footer under the right tabs column only
        right_col.addLayout(footer)
        # Connect all checkboxes inside tabs to control Run enablement
        for cb in self.tab_maps.findChildren(QtW.QCheckBox):
            cb.toggled.connect(self._update_run_enabled)
        # Set initial state for Run
        self._update_run_enabled()
        return right

    def _apply_spinbox_preferences(self) -> None:
        # Hide up/down arrows and disable mouse wheel for all QDoubleSpinBox in the UI
        try:
            self._wheel_blocker = _WheelBlocker(self)
            # Apply to all spin boxes (integer and double)
            en_us = QtCore.QLocale(QtCore.QLocale.English, QtCore.QLocale.UnitedStates)
            for sp in self.findChildren(QtW.QAbstractSpinBox):
                sp.setButtonSymbols(QtW.QAbstractSpinBox.NoButtons)
                # Make focus explicit; prevents accidental scroll when not focused
                sp.setFocusPolicy(QtCore.Qt.StrongFocus)
                sp.installEventFilter(self._wheel_blocker)
                # Force dot as decimal separator in display/parse
                sp.setLocale(en_us)
        except Exception:
            pass

    # ----- Actions -----
    def action_open(self) -> None:
        fn, _ = QtW.QFileDialog.getOpenFileName(
            self,
            "Open traces",
            str(Path.cwd()),
            "Text Files (*.txt *.csv);;All Files (*)",
        )
        if not fn:
            return
        self.load_file(Path(fn))

    def action_browse(self) -> None:
        fn, _ = QtW.QFileDialog.getOpenFileName(
            self,
            "Select input file",
            str(Path.cwd()),
            "Text/CSV (*.txt *.csv);;SVG/Images (*.svg *.jpeg *.jpg *.tiff *.tif);;All Files (*)",
        )
        if not fn:
            return
        self.edit_filename.setText(fn)
        self.btn_preview.setEnabled(True)
        # Message after selecting a node file
        if self.rb_node.isChecked():
            self._set_left_message("Click Preview to view the file contents.")

    def action_preview(self) -> None:
        path = self.edit_filename.text().strip()
        if not path:
            QtW.QMessageBox.information(self, "No file", "Select a file first.")
            return
        # Show progress message while reading/plotting
        if self.rb_node.isChecked():
            self._set_left_message("Reading the node file...")
            QtW.QApplication.processEvents()
        self.load_file(Path(path))
        # Final message after preview is drawn
        self._set_left_message("Ready. Click Run to generate maps and graphs.")

    def action_run(self) -> None:
        # Generate plots in separate window(s)
        if not getattr(self, "_segments", []):
            QtW.QMessageBox.information(self, "No data", "Load and preview a node file first.")
            return
        # Prepare counts/title used by traces map
        n_traces = len(getattr(self, "_traces", []))
        n_segments = len(self._segments)
        n_nodes = sum((len(t.segments) + 1) for t in getattr(self, "_traces", [])) if getattr(self, "_traces", []) else 0
        title = f"Mapped traces (n = {n_traces}), segments (n = {n_segments}) & nodes (n = {n_nodes})"
        # Traces, segments (with optional Show nodes overlay)
        if self.chk_traces_segments.isChecked():
            if self.chk_show_nodes.isChecked():
                self._show_plot_window(
                    key="traces_nodes",
                    window_title="PyFracPaQ - Traces + Nodes",
                    plotter=lambda ax: self._plot_traces_with_nodes(ax, title=title),
                )
            else:
                self._show_plot_window(
                    key="traces_segments",
                    window_title="PyFracPaQ - Traces",
                    plotter=lambda ax: self._plot_traces_only(ax, title=title),
                )
        # Slip tendency related plots
        if getattr(self, "chk_slip", None) is not None and self.chk_slip.isChecked():
            self._show_plot_window(
                key="slip_tendency_map",
                window_title="PyFracPaQ - Slip Tendency",
                plotter=lambda ax: self._plot_slip_tendency(ax),
            )
            self._show_plot_window(
                key="slip_tendency_mohr",
                window_title="PyFracPaQ - Mohr Circle (Slip)",
                plotter=lambda ax: self._plot_mohr_circle(ax),
            )
            self._show_plot_window(
                key="slip_tendency_rose",
                window_title="PyFracPaQ - Rose (Slip Tendency)",
                plotter=lambda ax: self._plot_rose_slip(ax),
                polar=True,
            )
        # Dilation tendency related plots (mirror Slip pattern: map + rose)
        if getattr(self, "chk_dilation", None) is not None and self.chk_dilation.isChecked():
            self._show_plot_window(
                key="dilation_tendency_map",
                window_title="PyFracPaQ - Dilation Tendency",
                plotter=lambda ax: self._plot_dilation_tendency(ax),
            )
            # Mohr circle is the same stress space for dilation; reuse the same plotter
            self._show_plot_window(
                key="dilation_tendency_mohr",
                window_title="PyFracPaQ - Mohr Circle (Dilation)",
                plotter=lambda ax: self._plot_mohr_circle(ax),
            )
            self._show_plot_window(
                key="dilation_tendency_rose",
                window_title="PyFracPaQ - Rose (Dilation Tendency)",
                plotter=lambda ax: self._plot_rose_dilation(ax),
                polar=True,
            )
        # Fracture susceptibility related plots (map + Mohr + rose)
        if getattr(self, "chk_suscept", None) is not None and self.chk_suscept.isChecked():
            self._show_plot_window(
                key="susceptibility_map",
                window_title="PyFracPaQ - Fracture Susceptibility",
                plotter=lambda ax: self._plot_susceptibility_map(ax),
            )
            self._show_plot_window(
                key="susceptibility_mohr",
                window_title="PyFracPaQ - Mohr Circle (Susceptibility)",
                plotter=lambda ax: self._plot_mohr_circle(ax),
            )
            self._show_plot_window(
                key="susceptibility_rose",
                window_title="PyFracPaQ - Rose (Fracture Susceptibility)",
                plotter=lambda ax: self._plot_rose_susceptibility(ax),
                polar=True,
            )

        # Critically stressed fractures related plots (map + Mohr + rose)
        if getattr(self, "chk_crit", None) is not None and self.chk_crit.isChecked():
            self._show_plot_window(
                key="csf_map",
                window_title="PyFracPaQ - Critically Stressed Fractures",
                plotter=lambda ax: self._plot_csf_map(ax),
            )
            # Mohr circle (same stress space and envelope)
            self._show_plot_window(
                key="csf_mohr",
                window_title="PyFracPaQ - Mohr Circle (CSF)",
                plotter=lambda ax: self._plot_mohr_circle(ax),
            )
            self._show_plot_window(
                key="csf_rose",
                window_title="PyFracPaQ - Rose (CSF)",
                plotter=lambda ax: self._plot_rose_csf(ax),
                polar=True,
            )

    def load_file(self, path: Path) -> None:
        try:
            traces = read_traces_txt(path)
        except Exception as e:
            QtW.QMessageBox.critical(self, "Error", f"Failed to load file:\n{e}")
            return

        if not traces:
            QtW.QMessageBox.warning(self, "No data", "No valid segments found in file.")
            return

        # Flatten segments for plotting; keep traces for stats
        self._traces = traces
        self._segments = [s for t in traces for s in t.segments]
        self.edit_filename.setText(str(path))
        self.statusBar().showMessage("Ready. Click Run to generate maps and graphs.")
        # Enable flip controls (both left and right, if present)
        for b in [getattr(self, 'btn_flipx', None), getattr(self, 'btn_flipy', None),
                  getattr(self, 'btn_flipx_left', None), getattr(self, 'btn_flipy_left', None)]:
            if b is not None:
                b.setEnabled(True)

        self._update_stats()
        # Show preview in the embedded canvas
        self._replot_map()
        # Enable tabs and all pages after a successful Preview
        self.tabs.setEnabled(True)
        try:
            for i in range(self.tabs.count()):
                self.tabs.setTabEnabled(i, True)
        except Exception:
            pass
        self._replot_rose()
        self._update_run_enabled()

    # ----- Plot helpers -----
    def _replot_map(self) -> None:
        ax = self.canvas_map.ax
        ax.clear()
        if self._segments:
            # Switch to white plotting background and show axes
            try:
                self.canvas_map.set_plot_background_white()
            except Exception:
                pass
            # Preview always shows traces; nodes only if enabled and checked
            show_nodes = bool(self.chk_show_nodes.isEnabled() and self.chk_show_nodes.isChecked())
            plot_tracemap(self._segments, ax=ax, show_nodes=show_nodes)
        else:
            # No data: return to placeholder background and hide axes
            try:
                bg = self.palette().color(self.backgroundRole())
                self.canvas_map.set_placeholder_background(bg)
            except Exception:
                pass
        self.canvas_map.draw_idle()

    def _clear_map_canvas(self) -> None:
        ax = self.canvas_map.ax
        ax.clear()
        self.canvas_map.draw_idle()

    def _replot_rose(self) -> None:
        # No rose on initial screen; placeholder
        pass

    def action_save_figures(self) -> None:
        if not self._segments:
            QtW.QMessageBox.information(self, "Nothing to save", "Load traces first.")
            return
        fn, _ = QtW.QFileDialog.getSaveFileName(
            self,
            "Save figure prefix",
            "figures",
            "PNG (*.png);;SVG (*.svg);;PDF (*.pdf)",
        )
        if not fn:
            return
        # Salva com sufixos padrão
        base = Path(fn)
        # Garantir extensão do filtro escolhido
        if base.suffix.lower() not in {".png", ".svg", ".pdf"}:
            base = base.with_suffix(".png")
        # Save only map on this screen
        self._replot_map()
        self.canvas_map.figure.savefig(base.with_name(base.stem + "_tracemap" + base.suffix))
        self.statusBar().showMessage(f"Saved figures to {base.parent}")

    # ----- Helpers -----
    def _set_left_message(self, text: str) -> None:
        # Use only the main status bar for messages
        if self.statusBar() is not None and text is not None:
            self.statusBar().showMessage(text)
    def _update_stats(self) -> None:
        if not hasattr(self, "txt_stats"):
            return
        traces = getattr(self, "_traces", [])
        if not traces:
            self.txt_stats.clear()
            return
        xs = []
        ys = []
        n_segments = 0
        n_nodes = 0
        for t in traces:
            # Accumulate per-trace nodes and segments
            n_segments += len(t.segments)
            n_nodes += len(t.segments) + 1
            for s in t.segments:
                xs.extend([s.x1, s.x2])
                ys.extend([s.y1, s.y2])
        xmin, xmax = min(xs), max(xs)
        ymin, ymax = min(ys), max(ys)
        n_traces = len(traces)
        lines = [
            f"Min. X coordinate: {xmin:g}",
            f"Min. Y coordinate: {ymin:g}",
            f"Max. X coordinate: {xmax:g}",
            f"Max. Y coordinate: {ymax:g}",
            f"Number of traces: {n_traces}",
            f"Number of segments: {n_segments}",
            f"Number of nodes: {n_nodes}",
        ]
        self.txt_stats.setPlainText("\n".join(lines))

    def _set_small_header_icon(self) -> None:
        for p in [
            Path("FracPaQ_MATLAB/FracPaQicon.jpeg"),
            Path("FracPaQ_MATLAB/FracPaQicon.jpg"),
            Path("FracPaQ_MATLAB/FracPaQicon.png"),
        ]:
            if p.exists():
                pix = QtGui.QPixmap(str(p))
                self.lbl_title_icon.setPixmap(pix.scaledToHeight(40, QtCore.Qt.SmoothTransformation))
                break

    def _set_big_logo(self) -> None:
        for p in [
            Path("FracPaQ_MATLAB/FracPaQlogo.jpeg"),
            Path("FracPaQ_MATLAB/FracPaQlogo.jpg"),
            Path("FracPaQ_MATLAB/FracPaQlogo.png"),
        ]:
            if p.exists():
                pix = QtGui.QPixmap(str(p))
                self.lbl_biglogo.setPixmap(pix.scaledToHeight(80, QtCore.Qt.SmoothTransformation))
                break

    def _toggle_hough_fields(self, on: bool) -> None:
        for w in [self.edit_houghpeaks, self.edit_houghthreshold, self.edit_fillgap, self.edit_minlength]:
            w.setEnabled(on)

    def _not_implemented(self) -> None:
        QtW.QMessageBox.information(self, "Not implemented", "This action is not implemented yet in PyFracPaQ.")

    def _toggle_traces_options(self, on: bool) -> None:
        # Habilita/desabilita "Show nodes" subordinado a "Traces, segments"
        self.chk_show_nodes.setEnabled(on)
        if not on and self.chk_show_nodes.isChecked():
            # If parent unchecked, also uncheck child
            self.chk_show_nodes.setChecked(False)
        # Embedded canvas no longer reflects immediate plot
        self._update_run_enabled()

    def _show_plot_window(self, key: str, window_title: str, plotter, polar: bool = False) -> None:
        # If already visible, just raise/activate; don't replot to avoid flicker
        win = self._plot_windows.get(key)
        if win is not None and win.isVisible():
            win.raise_(); win.activateWindow(); return
        # Create window on first use or if it was closed/hidden
        if win is None:
            win = QtW.QMainWindow(self)
            cw = QtW.QWidget(); lay = QtW.QVBoxLayout(cw)
            canvas = MplCanvas(width=8, height=6, dpi=100, polar=polar)
            # Add Matplotlib nav toolbar (zoom, pan, save)
            toolbar = NavigationToolbar(canvas, win)
            lay.addWidget(toolbar)
            lay.addWidget(canvas)
            win.setCentralWidget(cw)
            win._canvas = canvas
            win._toolbar = toolbar
            # Prefer manual layout control for attached colorbars and tight titles
            try:
                win._canvas.figure.set_constrained_layout(False)
                # For Matplotlib >=3.8
                win._canvas.figure.set_layout_engine(None)
            except Exception:
                pass
            # Default window sizing (no special case); allow user to resize as needed
            self._plot_windows[key] = win
        else:
            # Ensure toolbar exists if window persisted without it
            if not hasattr(win, "_toolbar"):
                cw = win.centralWidget()
                if cw is not None and hasattr(cw, 'layout'):
                    layout = cw.layout()
                    toolbar = NavigationToolbar(win._canvas, win)
                    layout.insertWidget(0, toolbar)
                    win._toolbar = toolbar
            # Ensure canvas projection matches requested 'polar'
            want = 'polar' if polar else 'rectilinear'
            try:
                has = getattr(win._canvas.ax, 'name', 'rectilinear')
            except Exception:
                has = 'rectilinear'
            if has != want:
                cw = win.centralWidget()
                layout = cw.layout()
                # Remove old canvas widget
                layout.removeWidget(win._canvas)
                win._canvas.setParent(None)
                # Create new canvas with correct projection and insert after toolbar
                canvas = MplCanvas(width=8, height=6, dpi=100, polar=polar)
                layout.addWidget(canvas)
                win._canvas = canvas
                try:
                    win._canvas.figure.set_constrained_layout(False)
                    win._canvas.figure.set_layout_engine(None)
                except Exception:
                    pass
        # Store base title and apply flip suffix
        win._base_title = getattr(win, '_base_title', window_title)
        win.setWindowTitle(win._base_title + self._flip_title_suffix())
        # Plot content
        ax = win._canvas.ax
        ax.clear()
        # Remove any auxiliary axes (e.g., colorbars) from previous plots in this window
        try:
            fig = win._canvas.figure
            for ax2 in list(fig.axes):
                if ax2 is not ax:
                    ax2.remove()
        except Exception:
            pass
        plotter(ax)
        win._canvas.draw_idle()
        win.show()

    def _plot_traces_only(self, ax, title: str) -> None:
        # Plot all segments as lines, equal aspect, labels and MATLAB-style title
        plot_tracemap(self._segments, ax=ax, show_nodes=False)
        # Fit limits to data
        xs = [c for s in self._segments for c in (s.x1, s.x2)]
        ys = [c for s in self._segments for c in (s.y1, s.y2)]
        if xs and ys:
            ax.set_xlim(min(xs), max(xs)); ax.set_ylim(min(ys), max(ys))
        # Visual axis flips to mirror preview
        self._apply_axis_flip_visual(ax)
        # Reserve fixed margins to create a slightly larger gap between title and axes box
        prepare_figure_layout(ax.figure)
        reserve_axes_margins(ax, top=0.10, bottom=0.10)
        #shrink_axes_vertical(ax, factor=1.00)
        # Title anchored to the figure (does not move with axes) and slightly raised
        #center_title_over_axes(ax.figure, ax, title, y=0.99, top=0.92)
        #fig = ax.figure
        #divider = make_axes_locatable(ax)
        #cax = divider.append_axes("bottom", size="6%", pad=0.70)
        #cax.set_axis_off()
        #cax.set_facecolor('none')
        #cax.set_in_layout(True) 
        title_above_axes(ax, title, offset_points=16.5, top=0.95, adjust_layout=False)

    def _plot_traces_with_nodes(self, ax, title: str) -> None:
        # Draw traces first
        plot_tracemap(self._segments, ax=ax, show_nodes=False)
        # Nodes styling (inspired by MATLAB):
        # - Segment endpoints: black filled circles
        # - Segment midpoints: red filled squares
        # - Trace midpoints: green filled triangles (computed along polyline length)
        # Endpoints
        ex = []; ey = []
        mx = []; my = []  # segment midpoints
        for s in self._segments:
            ex.extend([s.x1, s.x2]); ey.extend([s.y1, s.y2])
            mx.append((s.x1 + s.x2) / 2.0); my.append((s.y1 + s.y2) / 2.0)
        if ex:
            ax.plot(
                ex,
                ey,
                linestyle='None',
                marker='o',
                markersize=5,
                markerfacecolor='none',
                markeredgecolor='k',
            )
        if mx:
            ax.plot(
                mx,
                my,
                linestyle='None',
                marker='s',
                markersize=5,
                markerfacecolor='none',
                markeredgecolor='r',
            )
        # Trace midpoints: position at half of cumulative length along the polyline
        tx = []; ty = []
        for t in getattr(self, "_traces", []):
            segs = t.segments
            if not segs:
                continue
            total = sum(s.length() for s in segs)
            if total <= 0:
                # Fallback: simple average of end points
                x1, y1 = segs[0].x1, segs[0].y1
                x2, y2 = segs[-1].x2, segs[-1].y2
                tx.append((x1 + x2) / 2.0); ty.append((y1 + y2) / 2.0)
                continue
            half = total / 2.0
            acc = 0.0
            found = False
            for s in segs:
                L = s.length()
                if acc + L >= half and L > 0:
                    rem = half - acc
                    r = rem / L
                    x = s.x1 + r * (s.x2 - s.x1)
                    y = s.y1 + r * (s.y2 - s.y1)
                    tx.append(x); ty.append(y)
                    found = True
                    break
                acc += L
            if not found:
                # Numerical edge case: place at last endpoint
                tx.append(segs[-1].x2); ty.append(segs[-1].y2)
        if tx:
            ax.plot(
                tx,
                ty,
                linestyle='None',
                marker='^',
                markersize=5,
                markerfacecolor='none',
                markeredgecolor='g',
            )
        # Limits, labels, title
        xs = [c for s in self._segments for c in (s.x1, s.x2)]
        ys = [c for s in self._segments for c in (s.y1, s.y2)]
        if xs and ys:
            ax.set_xlim(min(xs), max(xs)); ax.set_ylim(min(ys), max(ys))
        ax.set_aspect('equal', adjustable='box')
        ax.set_xlabel('X, pixels'); ax.set_ylabel('Y, pixels')
        # Visual axis flips to mirror preview
        self._apply_axis_flip_visual(ax)
        # Reserve fixed margins to create a slightly larger gap between title and axes box
        prepare_figure_layout(ax.figure)
        reserve_axes_margins(ax, top=0.10, bottom=0.10)
        #shrink_axes_vertical(ax, factor=1.00)
        # Title anchored to the figure (does not move with axes) and slightly raised
        #center_title_over_axes(ax.figure, ax, title, y=0.99, top=0.92)
        fig = ax.figure
        divider = make_axes_locatable(ax)
        cax = divider.append_axes("bottom", size="6%", pad=0.70)
        cax.set_axis_off()
        cax.set_facecolor('none')
        cax.set_in_layout(True) 
        title_above_axes(ax, title, offset_points=16.5, top=0.95, adjust_layout=False)

    def _flip_title_suffix(self) -> str:
        parts = []
        if self._flip_x:
            parts.append("X")
        if self._flip_y:
            parts.append("Y")
        return "" if not parts else " [Flip " + ",".join(parts) + "]"

    def _update_flip_indicator(self) -> None:
        parts = []
        if self._flip_x:
            parts.append("X")
        if self._flip_y:
            parts.append("Y")
        txt = "Flip: none" if not parts else f"Flip: {','.join(parts)}"
        self._flip_label.setText(txt)

    def _update_plot_window_titles(self) -> None:
        for win in self._plot_windows.values():
            try:
                base = getattr(win, '_base_title', win.windowTitle())
                win._base_title = base
                win.setWindowTitle(base + self._flip_title_suffix())
            except Exception:
                pass

    def _apply_flip_to_open_plots(self) -> None:
        # Apply visual flips to all open non-polar plots and redraw
        for win in self._plot_windows.values():
            try:
                ax = win._canvas.ax
                proj_name = getattr(ax, 'name', 'rectilinear')
                if proj_name != 'polar':
                    self._apply_axis_flip_visual(ax)
                    win._canvas.draw_idle()
            except Exception:
                pass

    def _on_flip_x(self) -> None:
        # Toggle state and invert preview axis
        self._flip_x = not self._flip_x
        # Sync both flip buttons (left/right) if present
        for b in [getattr(self, 'btn_flipx', None), getattr(self, 'btn_flipx_left', None)]:
            if b is not None:
                b.setChecked(self._flip_x)
        try:
            self.canvas_map.ax.invert_xaxis()
            self.canvas_map.draw_idle()
        except Exception:
            pass
        # Update indicators and apply to open plots
        self._update_flip_indicator()
        self._update_plot_window_titles()
        self._apply_flip_to_open_plots()

    def _on_flip_y(self) -> None:
        self._flip_y = not self._flip_y
        for b in [getattr(self, 'btn_flipy', None), getattr(self, 'btn_flipy_left', None)]:
            if b is not None:
                b.setChecked(self._flip_y)
        try:
            self.canvas_map.ax.invert_yaxis()
            self.canvas_map.draw_idle()
        except Exception:
            pass
        self._update_flip_indicator()
        self._update_plot_window_titles()
        self._apply_flip_to_open_plots()

    def _compute_slip_arrays(self, sigma1: float, sigma2: float, theta_sigma1: float):
        # Returns (segment_angles_deg_from_North, sigma_n array, tau array, TsNorm array)
        # Convert segment angle from X-axis (our data) to North-based (MATLAB style): angN = (90 - angX)
        angs = []
        sigmans = []
        taus = []
        ratios_theta = []
        for s in self._segments:
            angX = s.angle_deg()
            angN = (90.0 - angX) % 180.0
            # Apply axis flips to the angle (reverseAxis behavior)
            if self._flip_x:
                angN = (180.0 - angN) % 180.0
            if self._flip_y:
                angN = (180.0 - angN) % 180.0
            alpha = (angN + 90.0) - theta_sigma1
            sn = 0.5 * (sigma1 + sigma2) + 0.5 * (sigma1 - sigma2) * math.cos(math.radians(2.0 * alpha))
            tau = -0.5 * (sigma1 - sigma2) * math.sin(math.radians(2.0 * alpha))
            angs.append(angN)
            sigmans.append(sn)
            taus.append(tau)
            ratios_theta.append(abs(tau)/abs(sn) if abs(sn) > 0 else 0.0)
        # Tsmax with alpha0 = angN + 90 (independent of theta), and without flips per MATLAB
        ratios0 = []
        for s in self._segments:
            angX = s.angle_deg()
            angN = (90.0 - angX) % 180.0
            alpha0 = angN + 90.0
            sn0 = 0.5 * (sigma1 + sigma2) + 0.5 * (sigma1 - sigma2) * math.cos(math.radians(2.0 * alpha0))
            tau0 = -0.5 * (sigma1 - sigma2) * math.sin(math.radians(2.0 * alpha0))
            ratios0.append(abs(tau0)/abs(sn0) if abs(sn0) > 0 else 0.0)
        Tsmax = max(ratios0) if ratios0 else 1.0
        if Tsmax <= 0:
            Tsmax = 1.0
        TsNorm = [max(0.0, min(1.0, r / Tsmax)) for r in ratios_theta]
        return angs, sigmans, taus, TsNorm

    def _plot_slip_tendency(self, ax) -> None:
        sigma1 = float(self.sp_sigma1.value()) if hasattr(self, 'sp_sigma1') else 100.0
        sigma2 = float(self.sp_sigma2.value()) if hasattr(self, 'sp_sigma2') else 50.0
        theta_sigma1 = float(self.sp_angle.value()) if hasattr(self, 'sp_angle') else 0.0
        if not self._segments:
            return
        angs, sigmans, taus, TsNorm = self._compute_slip_arrays(sigma1, sigma2, theta_sigma1)
        cmap = cm.get_cmap('jet', 100)
        norm = colors.Normalize(vmin=0.0, vmax=1.0)
        xs_all = []
        ys_all = []
        for s, tsn in zip(self._segments, TsNorm):
            ax.plot([s.x1, s.x2], [s.y1, s.y2], color=cmap(norm(tsn)), lw=0.75)
            xs_all.extend([s.x1, s.x2]); ys_all.extend([s.y1, s.y2])
        if xs_all and ys_all:
            ax.set_xlim(min(xs_all), max(xs_all))
            ax.set_ylim(min(ys_all), max(ys_all))
        ax.set_aspect('equal', adjustable='box')
        ax.set_xlabel('X, pixels')
        ax.set_ylabel('Y, pixels')
        # Visual axis flips to mirror preview
        self._apply_axis_flip_visual(ax)
        # Disable auto layout to respect manual margins and colorbar placement
        prepare_figure_layout(ax.figure)
        # Reserve margins to create gap between title and axes (stable manual layout)
        reserve_axes_margins(ax, top=0.10, bottom=0.10)
        mappable = cm.ScalarMappable(norm=norm, cmap=cmap)
        mappable.set_array([])
        # Place colorbar directly below axes and match x-axis width (original behavior)
        fig = ax.figure
        divider = make_axes_locatable(ax)
        cax = divider.append_axes("bottom", size="6%", pad=0.70)
        cbar = fig.colorbar(mappable, cax=cax, orientation='horizontal')
        cbar.set_label('Normalised slip tendency', labelpad=6)
        # Show ticks from 0 to 1 every 0.1
        try:
            ticks = [i/10 for i in range(0, 11)]
            cbar.set_ticks(ticks)
        except Exception:
            pass
        # Title above axes with reserved top margin (keep adjust_layout off for stability)
        title_str = (
            fr"Normalised slip tendency for $\sigma_1$ = {sigma1:g} MPa, "
            fr"$\sigma_2$ = {sigma2:g} MPa, $\theta$ = {theta_sigma1:g}$^\circ$"
        )
        title_above_axes(ax, title_str, offset_points=15, top=0.95, adjust_layout=False)

    def _plot_dilation_tendency(self, ax) -> None:
        # Map: colour-coded by dilation tendency T_d = (sigma1 - sn) / (sigma1 - sigma2)
        sigma1 = float(self.sp_sigma1.value()) if hasattr(self, 'sp_sigma1') else 100.0
        sigma2 = float(self.sp_sigma2.value()) if hasattr(self, 'sp_sigma2') else 50.0
        theta_sigma1 = float(self.sp_angle.value()) if hasattr(self, 'sp_angle') else 0.0
        if not self._segments:
            return
        # Reuse stress arrays (sn from slip computation)
        _, sigmans, _, _ = self._compute_slip_arrays(sigma1, sigma2, theta_sigma1)
        cmap = cm.get_cmap('jet', 100)
        xs_all, ys_all = [], []
        for s, sn in zip(self._segments, sigmans):
            denom = (sigma1 - sigma2) if abs(sigma1 - sigma2) > 1e-12 else 1.0
            td = max(0.0, min(1.0, (sigma1 - sn) / denom))
            ax.plot([s.x1, s.x2], [s.y1, s.y2], color=cmap(td), lw=0.75)
            xs_all.extend([s.x1, s.x2]); ys_all.extend([s.y1, s.y2])
        if xs_all and ys_all:
            ax.set_xlim(min(xs_all), max(xs_all))
            ax.set_ylim(min(ys_all), max(ys_all))
        ax.set_aspect('equal', adjustable='box')
        ax.set_xlabel('X, pixels')
        ax.set_ylabel('Y, pixels')
        self._apply_axis_flip_visual(ax)
        # Disable auto layout and reserve margins before creating colorbar
        prepare_figure_layout(ax.figure)
        reserve_axes_margins(ax, top=0.10, bottom=0.10)
        # Colorbar (stable divider-based layout)
        norm = colors.Normalize(vmin=0.0, vmax=1.0)
        mappable = cm.ScalarMappable(norm=norm, cmap=cmap); mappable.set_array([])
        fig = ax.figure
        divider = make_axes_locatable(ax)
        cax = divider.append_axes("bottom", size="6%", pad=0.70)
        cbar = fig.colorbar(mappable, cax=cax, orientation='horizontal')
        cbar.set_label('Dilation tendency', labelpad=6)
        try:
            cbar.set_ticks([i/10 for i in range(0, 11)])
        except Exception:
            pass
        # Title above axes (keep adjust_layout off for stability)
        title_str = (
            fr"Dilation tendency for $\sigma_1$ = {sigma1:g} MPa, "
            fr"$\sigma_2$ = {sigma2:g} MPa, $\theta$ = {theta_sigma1:g}$^\circ$"
        )
        title_above_axes(ax, title_str, offset_points=15, top=0.95, adjust_layout=False)

    def _plot_susceptibility_map(self, ax) -> None:
        import numpy as np
        # Map: colour-coded by fracture susceptibility S = |tau| / (mu * max(0, sn - pf) + C0), clipped to [0,1]
        sigma1 = float(self.sp_sigma1.value()) if hasattr(self, 'sp_sigma1') else 100.0
        sigma2 = float(self.sp_sigma2.value()) if hasattr(self, 'sp_sigma2') else 50.0
        theta_sigma1 = float(self.sp_angle.value()) if hasattr(self, 'sp_angle') else 0.0
        C0 = float(self.sp_cohesion.value()) if hasattr(self, 'sp_cohesion') else 0.0
        mu = float(self.sp_fric.value()) if hasattr(self, 'sp_fric') else 0.6
        pf = float(self.sp_pore.value()) if hasattr(self, 'sp_pore') else 0.0
        if not self._segments:
            return
        _, sigmans, taus, _ = self._compute_slip_arrays(sigma1, sigma2, theta_sigma1)
        # Continuous inverted palette (no discretization). Match MATLAB definition:
        # Sf = |sn| - pf - (|tau| - C0)/mu  [MPa]
        cmap = cm.get_cmap('jet_r', 256)
        # Compute susceptibility values first to set dynamic color range
        mu_eff = mu if abs(mu) > 1e-12 else 1e-12
        Svals = []
        for sn, t in zip(sigmans, taus):
            sf = abs(sn) - pf - (abs(t) - C0) / mu_eff
            Svals.append(sf)
        if Svals:
            vmin, vmax = min(Svals), max(Svals)
            # Avoid zero-width range
            if abs(vmax - vmin) < 1e-12:
                vmax = vmin + 1.0
        else:
            vmin, vmax = 0.0, 1.0
        norm = colors.Normalize(vmin=vmin, vmax=vmax)
        xs_all = []
        ys_all = []
        for s, sn, t in zip(self._segments, sigmans, taus):
            sf = abs(sn) - pf - (abs(t) - C0) / mu_eff
            ax.plot([s.x1, s.x2], [s.y1, s.y2], color=cmap(norm(sf)), lw=0.75)
            xs_all.extend([s.x1, s.x2]); ys_all.extend([s.y1, s.y2])
        if xs_all and ys_all:
            ax.set_xlim(min(xs_all), max(xs_all))
            ax.set_ylim(min(ys_all), max(ys_all))
        ax.set_aspect('equal', adjustable='box')
        ax.set_xlabel('X, pixels')
        ax.set_ylabel('Y, pixels')
        self._apply_axis_flip_visual(ax)
        # Disable auto layout and reserve margins before creating colorbar
        prepare_figure_layout(ax.figure)
        reserve_axes_margins(ax, top=0.10, bottom=0.10)
        # Colorbar (stable divider-based layout)
        mappable = cm.ScalarMappable(norm=norm, cmap=cmap); mappable.set_array([])
        fig = ax.figure
        divider = make_axes_locatable(ax)
        cax = divider.append_axes("bottom", size="6%", pad=0.70)
        cbar = fig.colorbar(mappable, cax=cax, orientation='horizontal')
        cbar.set_label(r'Fracture susceptibility ($\Delta P_f$), MPa', labelpad=4)
        # Persist chosen ticks/range to reuse in rose without changing map's ticks
        try:
            self._susc_ticks = [float(t) for t in getattr(cbar, 'get_ticks', lambda: [])()]
        except Exception:
            try:
                self._susc_ticks = [float(tick) for tick in cbar.ax.get_xticks()]
            except Exception:
                self._susc_ticks = None
        self._susc_vmin = vmin
        self._susc_vmax = vmax
        # Title above axes (keep adjust_layout off for stability)
        title_str = (
            fr"Fracture susceptibility for $\sigma_1$ = {sigma1:g} MPa, "
            fr"$\sigma_2$ = {sigma2:g} MPa, $\theta$ = {theta_sigma1:g}$^\circ$"
        )
        title_above_axes(ax, title_str, offset_points=15, top=0.95, adjust_layout=False)

    def _apply_axis_flip_visual(self, ax) -> None:
        try:
            # Reset to normal first to ensure deterministic state
            ax.set_xlim(sorted(ax.get_xlim()))
            ax.set_ylim(sorted(ax.get_ylim()))
            if self._flip_x:
                ax.invert_xaxis()
            if self._flip_y:
                ax.invert_yaxis()
        except Exception:
            pass

    def _plot_mohr_circle(self, ax) -> None:
        sigma1 = float(self.sp_sigma1.value()) if hasattr(self, 'sp_sigma1') else 100.0
        sigma2 = float(self.sp_sigma2.value()) if hasattr(self, 'sp_sigma2') else 50.0
        theta_sigma1 = float(self.sp_angle.value()) if hasattr(self, 'sp_angle') else 0.0
        C0 = float(self.sp_cohesion.value()) if hasattr(self, 'sp_cohesion') else 0.0
        mu = float(self.sp_fric.value()) if hasattr(self, 'sp_fric') else 0.6
        pf = float(self.sp_pore.value()) if hasattr(self, 'sp_pore') else 0.0
        # Compute (σn, τ) for all segments (flip/θ-aware) to overlay on the circle
        _, sigmans, taus, _ = self._compute_slip_arrays(sigma1, sigma2, theta_sigma1)
        # Circle parameters (draw only upper half; y >= 0)
        center = 0.5 * (sigma1 + sigma2)
        radius = 0.5 * abs(sigma1 - sigma2)
        th = [i * math.pi / 180.0 for i in range(0, 181)]  # 0..180 deg
        xs = [center + radius * math.cos(t) for t in th]
        ys = [radius * math.sin(t) for t in th]
        # Prepare manual layout
        fig = ax.figure
        prepare_figure_layout(fig)
        # Draw circle, axes and envelope (upper branch only)
        ax.plot(xs, ys, color='0.2', lw=1.2, label='Stress')
        ax.axhline(0.0, color='0.6', lw=0.8)
        # Failure envelope (upper branch). Extend to the x-axis intercept (tau=0)
        # tau = mu*(sn - pf) + C0 => sn_intercept = pf - C0/mu (if mu != 0)
        if abs(mu) > 1e-12:
            x_zero = pf - (C0 / mu)
        else:
            x_zero = None
        # Right extent beyond sigma1 to show line clearly
        x_right = max(sigma1, center + radius * 1.2)
        if x_zero is not None:
            x_env = [min(x_zero, x_right), max(x_zero, x_right)]
        else:
            x_env = [min(sigma2, center - radius * 1.2), x_right]
        y_env = [max(0.0, mu * (x - pf) + C0) for x in x_env]
        ax.plot(x_env, y_env, 'r--', lw=1.2, label='Sliding or Failure')
        # Labels and limits
        ax.set_xlabel('Normal stress, MPa')
        ax.set_ylabel('Shear stress, MPa')
        ax.set_aspect('equal', adjustable='box')
        # Fit limits: x start at -5, y starts at 0 (positive only)
        x_max = max(xs + [x_env[1]])
        y_max = max([0.0] + ys + y_env)
        ax.set_xlim(-5, x_max)
        ax.set_ylim(0, 1.05 * y_max)
        # Harmonize major tick spacing across X and Y: use the smaller step
        try:
            xt = sorted(set(float(v) for v in ax.get_xticks()))
            yt = sorted(set(float(v) for v in ax.get_yticks()))
            def _step(vals):
                diffs = [b - a for a, b in zip(vals, vals[1:])]
                pos = [d for d in diffs if d > 1e-9]
                return min(pos) if pos else None
            sx = _step(xt)
            sy = _step(yt)
            if sx and sy:
                s = min(sx, sy)
                ax.xaxis.set_major_locator(MultipleLocator(s))
                ax.yaxis.set_major_locator(MultipleLocator(s))
        except Exception:
            pass
        # Major grid to aid reading (minor grid remains off)
        try:
            ax.grid(True, which='major', axis='both', color='0.88', linewidth=0.6)
        except Exception:
            pass
        # Legend inside the plot (upper-left)
        ax.legend(
            loc='upper left',
            frameon=True,
            fontsize=9,
            handlelength=2.0,
        )
        # Title close above the axes border (consistent spacing with Slip Tendency)
        title_str = rf"Mohr diagram $\mu$={mu:g}, $C_0$={C0:g} MPa"
        # Lift the title a bit more to separate from the axes box
        title_above_axes(ax, title_str, offset_points=15, top=0.95)

    def _plot_csf_map(self, ax) -> None:
        import numpy as np
        sigma1 = float(self.sp_sigma1.value()) if hasattr(self, 'sp_sigma1') else 100.0
        sigma2 = float(self.sp_sigma2.value()) if hasattr(self, 'sp_sigma2') else 50.0
        theta_sigma1 = float(self.sp_angle.value()) if hasattr(self, 'sp_angle') else 0.0
        C0 = float(self.sp_cohesion.value()) if hasattr(self, 'sp_cohesion') else 0.0
        mu = float(self.sp_fric.value()) if hasattr(self, 'sp_fric') else 0.6
        pf = float(self.sp_pore.value()) if hasattr(self, 'sp_pore') else 0.0
        if not self._segments:
            return
        _, sigmans, taus, _ = self._compute_slip_arrays(sigma1, sigma2, theta_sigma1)
        # Classification per MATLAB: CSF if |tau| >= mu*(|sn| - pf) + C0
        csf_vals = []
        for sn, t in zip(sigmans, taus):
            sn_a = abs(sn)
            t_a = abs(t)
            csf = 1 if (t_a >= (mu * (sn_a - pf) + C0)) else 0
            csf_vals.append(csf)
        # Two-color discrete map
        cmap = colors.ListedColormap([cm.get_cmap('jet')(0.10), cm.get_cmap('jet')(0.90)])
        norm = colors.BoundaryNorm(boundaries=[-0.5, 0.5, 1.5], ncolors=cmap.N)
        xs_all = []
        ys_all = []
        for s, csf in zip(self._segments, csf_vals):
            ax.plot([s.x1, s.x2], [s.y1, s.y2], color=cmap(norm(csf)), lw=0.75)
            xs_all.extend([s.x1, s.x2]); ys_all.extend([s.y1, s.y2])
        if xs_all and ys_all:
            ax.set_xlim(min(xs_all), max(xs_all))
            ax.set_ylim(min(ys_all), max(ys_all))
        ax.set_aspect('equal', adjustable='box')
        ax.set_xlabel('X, pixels')
        ax.set_ylabel('Y, pixels')
        self._apply_axis_flip_visual(ax)
        # Disable auto layout and reserve margins before creating colorbar
        prepare_figure_layout(ax.figure)
        reserve_axes_margins(ax, top=0.10, bottom=0.10)
        # Colorbar with categorical ticks/labels (stable divider-based layout)
        mappable = cm.ScalarMappable(norm=norm, cmap=cmap); mappable.set_array([])
        fig = ax.figure
        divider = make_axes_locatable(ax)
        cax = divider.append_axes("bottom", size="6%", pad=0.70)
        cbar = fig.colorbar(mappable, cax=cax, orientation='horizontal')
        cbar.set_label(fr'Critically Stressed Fractures, $P_f$={pf:g} MPa', labelpad=4)
        try:
            cbar.set_ticks([0, 1])
            cbar.set_ticklabels(['Non-CSF', 'CSF'])
        except Exception:
            pass
        # Title above axes (keep adjust_layout off for stability)
        title_str = (
            fr"Critically stressed fractures $\sigma_1$' = {sigma1 - pf:g} MPa, "
            fr"$\sigma_2$' = {sigma2 - pf:g} MPa, $\theta$ = {theta_sigma1:g}$^\circ$"
        )
        title_above_axes(ax, title_str, offset_points=15, top=0.95, adjust_layout=False)

    def _plot_rose_csf(self, ax) -> None:
        import numpy as np
        sigma1 = float(self.sp_sigma1.value()) if hasattr(self, 'sp_sigma1') else 100.0
        sigma2 = float(self.sp_sigma2.value()) if hasattr(self, 'sp_sigma2') else 50.0
        theta_sigma1 = float(self.sp_angle.value()) if hasattr(self, 'sp_angle') else 0.0
        C0 = float(self.sp_cohesion.value()) if hasattr(self, 'sp_cohesion') else 0.0
        mu = float(self.sp_fric.value()) if hasattr(self, 'sp_fric') else 0.6
        pf = float(self.sp_pore.value()) if hasattr(self, 'sp_pore') else 0.0
        angs, sigmans, taus, _ = self._compute_slip_arrays(sigma1, sigma2, theta_sigma1)
        if not angs:
            return
        # Duplicate angles for 0..360 coverage, and compute CSF flag per segment
        csf = [1 if (abs(t) >= (mu * (abs(sn) - pf) + C0)) else 0 for sn, t in zip(sigmans, taus)]
        angs2 = angs + [((a + 180.0) % 360.0) for a in angs]
        csf2 = csf + csf
        dir_bins = 36
        theta_edges = np.linspace(0, 2*np.pi, dir_bins + 1)
        theta = np.deg2rad(angs2)
        if self._flip_x:
            theta = (np.pi - theta)
        if self._flip_y:
            theta = (-theta)
        theta = (theta + 2*np.pi) % (2*np.pi)
        inds = np.digitize(theta, theta_edges) - 1
        means = np.zeros(dir_bins); counts = np.zeros(dir_bins)
        for i, val in zip(inds, csf2):
            if 0 <= i < dir_bins:
                means[i] += val; counts[i] += 1
        with np.errstate(invalid='ignore'):
            means = np.divide(means, counts, out=np.zeros_like(means), where=counts>0)
        # Polar setup
        ax.set_theta_zero_location('N'); ax.set_theta_direction(-1)
        try:
            ax.set_xticklabels([]); ax.set_yticks([]); ax.set_rticks([]); ax.set_rgrids([]); ax.grid(False); ax.set_frame_on(False)
            sp = ax.spines.get('polar');
            if sp is not None: sp.set_visible(False)
        except Exception:
            pass
        widths = 2*np.pi / dir_bins
        total = counts.sum()
        if total > 0:
            frac = counts / total; radii = np.sqrt(frac); max_frac = float(frac.max())
        else:
            radii = counts; max_frac = 0.0
        # Reference levels (equal-area): select outer rim based on max percentage present
        perc_levels = [1, 5, 10, 20, 30, 50]
        max_perc = max_frac * 100.0
        show_to_perc = next((pl for pl in perc_levels if max_perc <= pl), perc_levels[-1])
        show_to = show_to_perc / 100.0
        # Two-level color mapping (Non-CSF, CSF)
        cmap = colors.ListedColormap([cm.get_cmap('jet')(0.10), cm.get_cmap('jet')(0.90)])
        # Convert mean to discrete class: >=0.5 -> CSF
        classes = (means >= 0.5).astype(int)
        for i in range(dir_bins):
            col = cmap(classes[i])
            ax.bar(theta_edges[i], radii[i], width=widths, bottom=0.0, align='edge', color=col, edgecolor='white', alpha=0.95)
        # Margins and colorbar
        reserve_axes_margins(ax, top=0.05, bottom=0.13)
        shrink_axes_vertical(ax, factor=0.90)
        # Custom colorbar with two categories
        norm = colors.BoundaryNorm(boundaries=[-0.5, 0.5, 1.5], ncolors=cmap.N)
        mappable = cm.ScalarMappable(norm=norm, cmap=cmap); mappable.set_array([])
        cbar = axis_wide_colorbar(
            ax,
            mappable,
            location='bottom',
            size='5%',
            pad=0.00,
            label=r'Critically Stressed Fractures',
            gid='rose_csf_cbar',
        )
        try:
            cbar.set_ticks([0, 1]); cbar.set_ticklabels(['Non-CSF', 'CSF'])
        except Exception:
            pass
        # Rim and overlays: draw equal-area reference circles and labels (%, up to show_to_perc)
        r_edge = float(np.sqrt(show_to)) if show_to > 0 else 1.0
        ax.set_ylim(0, r_edge)
        thetas_full = np.linspace(0, 2*np.pi, 361)
        for pperc in perc_levels:
            if pperc <= show_to_perc:
                r = np.sqrt(pperc/100.0)
                ax.plot(thetas_full, np.full_like(thetas_full, r), color='k', lw=0.6)
                ax.text(np.pi, r, f"{pperc}%", ha='right', va='center', fontsize=8,
                        bbox=dict(facecolor='white', edgecolor='none', pad=0.2))
        for ang in (0.0, np.pi/2, np.pi, 3*np.pi/2):
            ax.plot([ang, ang], [0, r_edge], color='k', lw=0.5)
        theta_sig = np.deg2rad(theta_sigma1)
        ax.plot([theta_sig, theta_sig], [0, r_edge], color='r', lw=1.2)
        ax.plot([theta_sig + np.pi, theta_sig + np.pi], [0, r_edge], color='r', lw=1.2)
        try:
            ax.text(theta_sig, r_edge*1.005, r"Azimuth $\sigma_1$", ha='center', va='bottom', fontsize=9, clip_on=False, bbox=dict(facecolor='white', edgecolor='none', pad=0.2))
        except Exception:
            pass
        # Slightly higher nudge to visually match other roses on some backends
        title_above_axes(ax, r'Segment angles (equal area), colour-coded by CSF', offset_points=32, top=0.96, adjust_layout=False)

    def _plot_rose_slip(self, ax) -> None:
        import numpy as np
        sigma1 = float(self.sp_sigma1.value()) if hasattr(self, 'sp_sigma1') else 100.0
        sigma2 = float(self.sp_sigma2.value()) if hasattr(self, 'sp_sigma2') else 50.0
        theta_sigma1 = float(self.sp_angle.value()) if hasattr(self, 'sp_angle') else 0.0
        angs, _, _, TsNorm = self._compute_slip_arrays(sigma1, sigma2, theta_sigma1)
        if not angs:
            return
        # Duplicate for 0..360 coverage
        angs2 = angs + [((a + 180.0) % 360.0) for a in angs]
        ts2 = TsNorm + TsNorm
        # Decouple angular resolution from colour resolution to better match MATLAB
        dir_bins = 36  # finer angular division (e.g., 10° sectors)
        theta_edges = np.linspace(0, 2*np.pi, dir_bins + 1)
        theta = np.deg2rad(angs2)
        # Apply axis flips to polar angles (cartesian x-right, y-up -> polar E=0, clockwise)
        if self._flip_x:
            theta = (np.pi - theta)
        if self._flip_y:
            theta = (-theta)
        theta = (theta + 2*np.pi) % (2*np.pi)
        inds = np.digitize(theta, theta_edges) - 1
        means = np.zeros(dir_bins)
        counts = np.zeros(dir_bins)
        for i, val in zip(inds, ts2):
            if 0 <= i < dir_bins:
                means[i] += val
                counts[i] += 1
        with np.errstate(invalid='ignore'):
            means = np.divide(means, counts, out=np.zeros_like(means), where=counts>0)
        # Align orientation with MATLAB: rotate 90° left (North at top)
        ax.set_theta_zero_location('N')
        ax.set_theta_direction(-1)
        # Remove default exterior angle labels, radial ticks, grid and outer rim
        try:
            ax.set_xticklabels([])
            ax.set_yticks([])
            ax.set_rticks([])
            ax.set_rgrids([])
            ax.grid(False)
            ax.set_frame_on(False)
            # Hide polar spine if present
            sp = ax.spines.get('polar')
            if sp is not None:
                sp.set_visible(False)
        except Exception:
            pass
        widths = 2*np.pi / dir_bins
        # Equal-area scaling: radius ∝ sqrt(fraction of total)
        total = counts.sum()
        if total > 0:
            frac = counts / total
            radii = np.sqrt(frac)
            max_frac = float(frac.max())
        else:
            radii = counts
            max_frac = 0.0
        # Determine the last reference circle to show based on the next bracket
        # above the observed maximum percentage (1, 5, 10, 20, 30, 50)
        perc_levels = [1, 5, 10, 20, 30, 50]
        max_perc = max_frac * 100.0
        show_to_perc = perc_levels[-1]
        for pl in perc_levels:
            if max_perc <= pl:
                show_to_perc = pl
                break
        show_to = show_to_perc / 100.0
        # Discrete colours for Ts using independent levels following MATLAB rule:
        # levels = (360/delta)/2 + 1 ≈ dir_bins/2 + 1
        color_levels = int(dir_bins // 2 + 1)
        bounds = np.linspace(0.0, 1.0, color_levels + 1)
        # Slip rose uses standard 'jet' palette
        cmap = cm.get_cmap('jet', 256)
        norm = colors.BoundaryNorm(boundaries=bounds, ncolors=cmap.N, clip=True)
        for i in range(dir_bins):
            col = cmap(norm(means[i]))
            ax.bar(
                theta_edges[i], radii[i], width=widths, bottom=0.0, align='edge',
                color=col, edgecolor='white', alpha=0.95
            )
        # Reserve margins so title/colorbar fit; lower the plot slightly (keeps spacing to title/Azimuth)
        reserve_axes_margins(ax, top=0.05, bottom=0.13)
        # Reduce the polar plot height by ~10% to create a bit more space
        # around title and colorbar without changing their positions.
        shrink_axes_vertical(ax, factor=0.90)
        # Discrete colorbar aligned with the axis width
        mappable = cm.ScalarMappable(norm=norm, cmap=cmap)
        mappable.set_array([])
        # Show labelled ticks every 0.1 (keep internal discrete bounds at color_levels)
        ticks = np.linspace(0.0, 1.0, 11)
        axis_wide_colorbar(
            ax,
            mappable,
            location='bottom',
            size='5%',
            pad=0.00,
            ticks=ticks,
            label=r'Normalised slip tendency, $T_s$',
            gid='rose_ts_cbar',
        )
        # Set radial limit so the outer reference circle is the plot rim
        try:
            r_edge = float(np.sqrt(show_to))
        except Exception:
            r_edge = 1.0
        ax.set_ylim(0, r_edge)
        # Draw reference circles and labels (after bars) up to the chosen bracket
        thetas_full = np.linspace(0, 2*np.pi, 361)
        for pperc in perc_levels:
            if pperc <= show_to_perc:
                p = pperc / 100.0
                r = np.sqrt(p)
                ax.plot(thetas_full, np.full_like(thetas_full, r), color='k', lw=0.6)
                ax.text(
                    np.pi, r, f"{pperc}%", ha='right', va='center', fontsize=8,
                    bbox=dict(facecolor='white', edgecolor='none', pad=0.2)
                )
        # Add cross lines (horizontal and vertical through the origin)
        for ang in (0.0, np.pi/2, np.pi, 3*np.pi/2):
            ax.plot([ang, ang], [0, r_edge], color='k', lw=0.5)
        # Add σ1 azimuth line in red across the circle
        theta_sig = np.deg2rad(theta_sigma1)
        ax.plot([theta_sig, theta_sig], [0, r_edge], color='r', lw=1.2)
        ax.plot([theta_sig + np.pi, theta_sig + np.pi], [0, r_edge], color='r', lw=1.2)
        # Label the σ1 azimuth just outside the rim on the positive direction
        try:
            ax.text(
                theta_sig, r_edge*1.005, r"Azimuth $\sigma_1$",
                ha='center', va='bottom', fontsize=9, clip_on=False,
                bbox=dict(facecolor='white', edgecolor='none', pad=0.2)
            )
        except Exception:
            pass
        # Title above axes without adjusting layout (reserved margins handle space)
        title_above_axes(ax, r'Segment angles (equal area), colour-coded by $T_s$', offset_points=30, top=0.96, adjust_layout=False)

    def _plot_rose_dilation(self, ax) -> None:
        import numpy as np
        sigma1 = float(self.sp_sigma1.value()) if hasattr(self, 'sp_sigma1') else 100.0
        sigma2 = float(self.sp_sigma2.value()) if hasattr(self, 'sp_sigma2') else 50.0
        theta_sigma1 = float(self.sp_angle.value()) if hasattr(self, 'sp_angle') else 0.0
        # Compute sn with flip-aware angles
        angs, sigmans, _, _ = self._compute_slip_arrays(sigma1, sigma2, theta_sigma1)
        if not angs:
            return
        # Dilation tendency per segment
        denom = (sigma1 - sigma2) if abs(sigma1 - sigma2) > 1e-12 else 1.0
        Td = [max(0.0, min(1.0, (sigma1 - sn) / denom)) for sn in sigmans]
        # Duplicate for 0..360 coverage
        angs2 = angs + [((a + 180.0) % 360.0) for a in angs]
        td2 = Td + Td
        # Angular bins and statistics
        dir_bins = 36
        theta_edges = np.linspace(0, 2*np.pi, dir_bins + 1)
        theta = np.deg2rad(angs2)
        if self._flip_x:
            theta = (np.pi - theta)
        if self._flip_y:
            theta = (-theta)
        theta = (theta + 2*np.pi) % (2*np.pi)
        inds = np.digitize(theta, theta_edges) - 1
        means = np.zeros(dir_bins); counts = np.zeros(dir_bins)
        for i, val in zip(inds, td2):
            if 0 <= i < dir_bins:
                means[i] += val; counts[i] += 1
        with np.errstate(invalid='ignore'):
            means = np.divide(means, counts, out=np.zeros_like(means), where=counts>0)
        # Polar setup
        ax.set_theta_zero_location('N'); ax.set_theta_direction(-1)
        try:
            ax.set_xticklabels([]); ax.set_yticks([]); ax.set_rticks([]); ax.set_rgrids([]); ax.grid(False); ax.set_frame_on(False)
            sp = ax.spines.get('polar');
            if sp is not None: sp.set_visible(False)
        except Exception:
            pass
        widths = 2*np.pi / dir_bins
        total = counts.sum()
        if total > 0:
            frac = counts / total; radii = np.sqrt(frac); max_frac = float(frac.max())
        else:
            radii = counts; max_frac = 0.0
        # Reference levels
        perc_levels = [1, 5, 10, 20, 30, 50]
        max_perc = max_frac * 100.0
        show_to_perc = next((pl for pl in perc_levels if max_perc <= pl), perc_levels[-1])
        show_to = show_to_perc / 100.0
        # Colors
        color_levels = int(dir_bins // 2 + 1)
        bounds = np.linspace(0.0, 1.0, color_levels + 1)
        cmap = cm.get_cmap('jet', 256)
        norm = colors.BoundaryNorm(boundaries=bounds, ncolors=cmap.N, clip=True)
        for i in range(dir_bins):
            col = cmap(norm(means[i]))
            ax.bar(theta_edges[i], radii[i], width=widths, bottom=0.0, align='edge', color=col, edgecolor='white', alpha=0.95)
        # Margins and colorbar
        reserve_axes_margins(ax, top=0.05, bottom=0.13)
        # Create a bit more headroom for title/colorbar consistency with slip rose
        shrink_axes_vertical(ax, factor=0.90)
        mappable = cm.ScalarMappable(norm=norm, cmap=cmap); mappable.set_array([])
        ticks = np.linspace(0.0, 1.0, 11)
        axis_wide_colorbar(ax, mappable, location='bottom', size='5%', pad=0.00, ticks=ticks, label=r'Dilation tendency, $T_d$', gid='rose_td_cbar')
        # Rim and overlays
        try:
            r_edge = float(np.sqrt(show_to))
        except Exception:
            r_edge = 1.0
        ax.set_ylim(0, r_edge)
        thetas_full = np.linspace(0, 2*np.pi, 361)
        for pperc in perc_levels:
            if pperc <= show_to_perc:
                r = np.sqrt(pperc/100.0)
                ax.plot(thetas_full, np.full_like(thetas_full, r), color='k', lw=0.6)
                ax.text(np.pi, r, f"{pperc}%", ha='right', va='center', fontsize=8, bbox=dict(facecolor='white', edgecolor='none', pad=0.2))
        for ang in (0.0, np.pi/2, np.pi, 3*np.pi/2):
            ax.plot([ang, ang], [0, r_edge], color='k', lw=0.5)
        theta_sig = np.deg2rad(theta_sigma1)
        ax.plot([theta_sig, theta_sig], [0, r_edge], color='r', lw=1.2)
        ax.plot([theta_sig + np.pi, theta_sig + np.pi], [0, r_edge], color='r', lw=1.2)
        try:
            ax.text(theta_sig, r_edge*1.005, r"Azimuth $\sigma_1$", ha='center', va='bottom', fontsize=9, clip_on=False, bbox=dict(facecolor='white', edgecolor='none', pad=0.2))
        except Exception:
            pass
        title_above_axes(ax, r'Segment angles (equal area), colour-coded by $T_d$', offset_points=30, top=0.96, adjust_layout=False)

    def _plot_rose_susceptibility(self, ax) -> None:
        import numpy as np
        sigma1 = float(self.sp_sigma1.value()) if hasattr(self, 'sp_sigma1') else 100.0
        sigma2 = float(self.sp_sigma2.value()) if hasattr(self, 'sp_sigma2') else 50.0
        theta_sigma1 = float(self.sp_angle.value()) if hasattr(self, 'sp_angle') else 0.0
        C0 = float(self.sp_cohesion.value()) if hasattr(self, 'sp_cohesion') else 0.0
        mu = float(self.sp_fric.value()) if hasattr(self, 'sp_fric') else 0.6
        pf = float(self.sp_pore.value()) if hasattr(self, 'sp_pore') else 0.0
        # Compute sn,tau with flip-aware angles
        angs, sigmans, taus, _ = self._compute_slip_arrays(sigma1, sigma2, theta_sigma1)
        if not angs:
            return
        # Susceptibility per segment (ΔPf in MPa), consistent with map
        mu_eff = mu if abs(mu) > 1e-12 else 1e-12
        Sfs = [abs(sn) - pf - (abs(t) - C0) / mu_eff for sn, t in zip(sigmans, taus)]
        # Duplicate for 0..360 coverage
        angs2 = angs + [((a + 180.0) % 360.0) for a in angs]
        s2 = Sfs + Sfs
        # Angular bins and statistics
        dir_bins = 36
        theta_edges = np.linspace(0, 2*np.pi, dir_bins + 1)
        theta = np.deg2rad(angs2)
        if self._flip_x:
            theta = (np.pi - theta)
        if self._flip_y:
            theta = (-theta)
        theta = (theta + 2*np.pi) % (2*np.pi)
        inds = np.digitize(theta, theta_edges) - 1
        means = np.zeros(dir_bins); counts = np.zeros(dir_bins)
        for i, val in zip(inds, s2):
            if 0 <= i < dir_bins:
                means[i] += val; counts[i] += 1
        with np.errstate(invalid='ignore'):
            means = np.divide(means, counts, out=np.zeros_like(means), where=counts>0)
        # Polar setup
        ax.set_theta_zero_location('N'); ax.set_theta_direction(-1)
        try:
            ax.set_xticklabels([]); ax.set_yticks([]); ax.set_rticks([]); ax.set_rgrids([]); ax.grid(False); ax.set_frame_on(False)
            sp = ax.spines.get('polar');
            if sp is not None: sp.set_visible(False)
        except Exception:
            pass
        widths = 2*np.pi / dir_bins
        total = counts.sum()
        if total > 0:
            frac = counts / total; radii = np.sqrt(frac); max_frac = float(frac.max())
        else:
            radii = counts; max_frac = 0.0
        # Reference levels
        perc_levels = [1, 5, 10, 20, 30, 50]
        max_perc = max_frac * 100.0
        show_to_perc = next((pl for pl in perc_levels if max_perc <= pl), perc_levels[-1])
        show_to = show_to_perc / 100.0
        # Colors: discrete variation like Slip/Dilation roses, but using Sf range [vmin, vmax]
        cmap = cm.get_cmap('jet_r', 256)
        if Sfs:
            vmin = float(np.min(Sfs)); vmax = float(np.max(Sfs))
            if abs(vmax - vmin) < 1e-12:
                vmax = vmin + 1.0
        else:
            vmin, vmax = 0.0, 1.0
        color_levels = int(dir_bins // 2 + 1)
        bounds = np.linspace(vmin, vmax, color_levels + 1)
        norm = colors.BoundaryNorm(boundaries=bounds, ncolors=cmap.N, clip=True)
        for i in range(dir_bins):
            col = cmap(norm(means[i]))
            ax.bar(theta_edges[i], radii[i], width=widths, bottom=0.0, align='edge', color=col, edgecolor='white', alpha=0.95)
        # Margins and colorbar (match Slip/Dilation roses)
        reserve_axes_margins(ax, top=0.05, bottom=0.13)
        shrink_axes_vertical(ax, factor=0.90)
        mappable = cm.ScalarMappable(norm=norm, cmap=cmap); mappable.set_array([])
        # Colorbar with later tick locator adjustment to match MATLAB "nice" ticks
        cbar = axis_wide_colorbar(
            ax,
            mappable,
            location='bottom',
            size='5%',
            pad=0.00,
            label=r'Fracture susceptibility ($\Delta P_f$), MPa',
            gid='rose_susc_cbar',
        )
        try:
            import numpy as _np
            from math import floor, log10, ceil
            span = max(1e-12, float(vmax - vmin))
            target = 8
            base_pow = 10.0 ** floor(log10(span / target))
            best = None
            for m in (1, 2, 5, 10):
                step = m * base_pow
                n = int(_np.floor(vmax / step) - _np.ceil(vmin / step) + 1)
                score = abs(n - target)
                if best is None or score < best[0]:
                    best = (score, step, n)
            step = best[1]
            # Do not extend below vmin to avoid empty band; extend only top to a nice value
            start = _np.ceil(vmin / step) * step
            end = _np.ceil(vmax / step) * step
            ticks = _np.arange(start, end + 0.5 * step, step)
            ticks = _np.round(ticks, 10)
            if ticks.size >= 2:
                cbar.set_ticks(ticks)
        except Exception:
            pass
        # Rim and overlays
        try:
            r_edge = float(np.sqrt(show_to))
        except Exception:
            r_edge = 1.0
        ax.set_ylim(0, r_edge)
        thetas_full = np.linspace(0, 2*np.pi, 361)
        for pperc in perc_levels:
            if pperc <= show_to_perc:
                r = np.sqrt(pperc/100.0)
                ax.plot(thetas_full, np.full_like(thetas_full, r), color='k', lw=0.6)
                ax.text(np.pi, r, f"{pperc}%", ha='right', va='center', fontsize=8, bbox=dict(facecolor='white', edgecolor='none', pad=0.2))
        for ang in (0.0, np.pi/2, np.pi, 3*np.pi/2):
            ax.plot([ang, ang], [0, r_edge], color='k', lw=0.5)
        theta_sig = np.deg2rad(theta_sigma1)
        ax.plot([theta_sig, theta_sig], [0, r_edge], color='r', lw=1.2)
        ax.plot([theta_sig + np.pi, theta_sig + np.pi], [0, r_edge], color='r', lw=1.2)
        try:
            ax.text(theta_sig, r_edge*1.005, r"Azimuth $\sigma_1$", ha='center', va='bottom', fontsize=9, clip_on=False, bbox=dict(facecolor='white', edgecolor='none', pad=0.2))
        except Exception:
            pass
        title_above_axes(ax, r'Segment angles (equal area), colour-coded by $S_f$', offset_points=30, top=0.96, adjust_layout=False)

    def _update_run_enabled(self) -> None:
        # Enable Run if any checkbox in tabs is checked and data is loaded
        if not hasattr(self, "btn_run"):
            return
        checks = self.tab_maps.findChildren(QtW.QCheckBox)
        any_checked = any(cb.isChecked() for cb in checks)
        self.btn_run.setEnabled(bool(getattr(self, "_segments", [])) and any_checked)
