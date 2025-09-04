from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6 import QtCore, QtGui, QtWidgets as QtW

from ..io import read_traces_txt
from ..plots import plot_tracemap
from .widgets import MplCanvas


class MainWindow(QtW.QMainWindow):
    def __init__(self, parent: Optional[QtW.QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("FracPy")
        self.resize(1200, 800)

        # Data
        self._segments = []

        # Central container (body only)
        central = QtW.QWidget()
        self.setCentralWidget(central)
        root = QtW.QVBoxLayout(central)

        # Body: left input panel + right content (tabs + canvas + footer)
        body = QtW.QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        root.addLayout(body, 1)

        left = self._build_left_panel()
        body.addWidget(left, 0)

        right = self._build_right_panel()
        body.addWidget(right, 1)

        # Menu / toolbar
        open_act = QtGui.QAction("Open...", self)
        open_act.triggered.connect(self.action_open)
        file_menu = self.menuBar().addMenu("File")
        file_menu.addAction(open_act)

        self.statusBar().showMessage("Ready")
        self._plot_window = None
        # Initial left message
        if hasattr(self, "_set_left_message"):
            self._set_left_message("Ready!")

    # ----- UI builders -----
    def _build_left_panel(self) -> QtW.QWidget:
        # Left controls panel titled "Input"
        left = QtW.QGroupBox("Input")
        v = QtW.QVBoxLayout(left)

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

        # Flip + Preview
        self.btn_flipx = QtW.QPushButton("Flip X-axis"); self.btn_flipx.setEnabled(False)
        self.btn_flipy = QtW.QPushButton("Flip Y-axis"); self.btn_flipy.setEnabled(False)
        self.btn_preview = QtW.QPushButton("Preview"); self.btn_preview.setEnabled(False)
        self.btn_preview.clicked.connect(self.action_preview)
        btns = QtW.QHBoxLayout(); btns.addWidget(self.btn_flipx); btns.addWidget(self.btn_flipy); btns.addWidget(self.btn_preview)
        v.addLayout(btns)

        # Statistics placeholder
        stats_box = QtW.QGroupBox("Statistics for selected file")
        stats_layout = QtW.QVBoxLayout(stats_box)
        self.txt_stats = QtW.QTextEdit(); self.txt_stats.setReadOnly(True); self.txt_stats.setPlaceholderText("")
        stats_layout.addWidget(self.txt_stats)
        v.addWidget(stats_box, 1)

        v.addStretch(0)
        return left

        # Plots options (como no MATLAB)
        plots_box = QtW.QGroupBox("Plots")
        pg = QtW.QGridLayout(plots_box)
        r = 0
        self.chk_histolen = QtW.QCheckBox("Length histogram")
        pg.addWidget(self.chk_histolen, r, 0)
        pg.addWidget(QtW.QLabel("bins"), r, 1)
        self.cmb_len_bins = QtW.QComboBox(); self.cmb_len_bins.addItems(["10","20","30","50"]); self.cmb_len_bins.setCurrentIndex(1)
        self.cmb_len_bins.setEnabled(False)
        pg.addWidget(self.cmb_len_bins, r, 2)
        r += 1
        self.chk_histoang = QtW.QCheckBox("Angle histogram")
        pg.addWidget(self.chk_histoang, r, 0)
        pg.addWidget(QtW.QLabel("bins"), r, 1)
        self.cmb_ang_bins = QtW.QComboBox(); self.cmb_ang_bins.addItems(["12","18","36"]); self.cmb_ang_bins.setCurrentIndex(1)
        self.cmb_ang_bins.setEnabled(False)
        pg.addWidget(self.cmb_ang_bins, r, 2)
        r += 1
        self.chk_rose = QtW.QCheckBox("Rose diagram")
        pg.addWidget(self.chk_rose, r, 0)
        pg.addWidget(QtW.QLabel("bins"), r, 1)
        self.cmb_rose_bins = QtW.QComboBox(); self.cmb_rose_bins.addItems(["12","18","36"]); self.cmb_rose_bins.setCurrentIndex(1)
        self.cmb_rose_bins.setEnabled(False)
        pg.addWidget(self.cmb_rose_bins, r, 2)
        r += 1
        self.lbl_degfromnorth = QtW.QLabel("deg from North")
        self.edit_degfromnorth = QtW.QSpinBox(); self.edit_degfromnorth.setRange(-180, 180); self.edit_degfromnorth.setEnabled(False)
        pg.addWidget(self.lbl_degfromnorth, r, 0)
        pg.addWidget(self.edit_degfromnorth, r, 2)
        r += 1
        self.chk_roselenw = QtW.QCheckBox("Length-weighted rose"); self.chk_roselenw.setEnabled(False)
        self.chk_showrosemean = QtW.QCheckBox("Show rose mean"); self.chk_showrosemean.setEnabled(False)
        self.chk_rosecolour = QtW.QCheckBox("Colour rose"); self.chk_rosecolour.setEnabled(False)
        pg.addWidget(self.chk_roselenw, r, 0); pg.addWidget(self.chk_showrosemean, r, 1); pg.addWidget(self.chk_rosecolour, r, 2)
        r += 1
        # Enable/disable like MATLAB
        self.chk_histoang.toggled.connect(lambda on: self.cmb_ang_bins.setEnabled(on))
        self.chk_histolen.toggled.connect(lambda on: self.cmb_len_bins.setEnabled(on))
        def toggle_rose(on: bool):
            self.cmb_rose_bins.setEnabled(on)
            self.edit_degfromnorth.setEnabled(on); self.lbl_degfromnorth.setEnabled(on)
            self.chk_roselenw.setEnabled(on); self.chk_showrosemean.setEnabled(on); self.chk_rosecolour.setEnabled(on)
            self.canvas_rose_parent.setVisible(on)
            self._replot_rose()
        self.chk_rose.toggled.connect(toggle_rose)
        self.cmb_rose_bins.currentIndexChanged.connect(self._replot_rose)
        v.addWidget(plots_box)

        # Maps options
        maps_box = QtW.QGroupBox("Maps")
        mg = QtW.QGridLayout(maps_box)
        r = 0
        self.chk_intensity = QtW.QCheckBox("Intensity map"); mg.addWidget(self.chk_intensity, r, 0); r += 1
        self.chk_density = QtW.QCheckBox("Density map"); mg.addWidget(self.chk_density, r, 0); r += 1
        self.chk_showcircles = QtW.QCheckBox("Show scan circles"); self.chk_showcircles.setEnabled(False)
        mg.addWidget(self.chk_showcircles, r, 0)
        mg.addWidget(QtW.QLabel("# scan circles"), r, 1)
        self.edit_numscancircles = QtW.QSpinBox(); self.edit_numscancircles.setRange(0, 10000); self.edit_numscancircles.setEnabled(False)
        mg.addWidget(self.edit_numscancircles, r, 2); r += 1
        # Enable/disable like MATLAB
        def toggle_circles(_: bool):
            on = self.chk_intensity.isChecked() or self.chk_density.isChecked()
            self.chk_showcircles.setEnabled(on)
            self.edit_numscancircles.setEnabled(on)
        self.chk_intensity.toggled.connect(toggle_circles)
        self.chk_density.toggled.connect(toggle_circles)
        v.addWidget(maps_box)

        # Triangles / censoring
        tri_box = QtW.QGroupBox("Sampling / censoring")
        tg = QtW.QGridLayout(tri_box); r = 0
        self.chk_triangle = QtW.QCheckBox("Triangle grid"); tg.addWidget(self.chk_triangle, r, 0)
        tg.addWidget(QtW.QLabel("# blocks (map)"), r, 1)
        self.edit_numblocksmap = QtW.QSpinBox(); self.edit_numblocksmap.setRange(0, 10000); self.edit_numblocksmap.setEnabled(False)
        tg.addWidget(self.edit_numblocksmap, r, 2); r += 1
        tg.addWidget(QtW.QLabel("pixels I→Y"), r, 1)
        self.edit_numpixelsItoY = QtW.QSpinBox(); self.edit_numpixelsItoY.setRange(0, 10000); self.edit_numpixelsItoY.setEnabled(False)
        tg.addWidget(self.edit_numpixelsItoY, r, 2); r += 1
        self.chk_censor = QtW.QCheckBox("Censor edges"); tg.addWidget(self.chk_censor, r, 0); r += 1
        # Toggle like MATLAB
        def toggle_triangle(on: bool):
            self.edit_numblocksmap.setEnabled(on); self.edit_numpixelsItoY.setEnabled(on)
        self.chk_triangle.toggled.connect(toggle_triangle)
        v.addWidget(tri_box)

        # Fluid / permeability ellipse (placeholders)
        fluid_box = QtW.QGroupBox("Fluid / aperture")
        fg = QtW.QGridLayout(fluid_box); r = 0
        self.chk_permellipse = QtW.QCheckBox("Permeability ellipse"); fg.addWidget(self.chk_permellipse, r, 0); r += 1
        fg.addWidget(QtW.QLabel("Aperture factor"), r, 0); self.edit_aperturefactor = QtW.QDoubleSpinBox(); self.edit_aperturefactor.setEnabled(False); fg.addWidget(self.edit_aperturefactor, r, 2); r += 1
        fg.addWidget(QtW.QLabel("Aperture exponent"), r, 0); self.edit_apertureexponent = QtW.QDoubleSpinBox(); self.edit_apertureexponent.setEnabled(False); fg.addWidget(self.edit_apertureexponent, r, 2); r += 1
        fg.addWidget(QtW.QLabel("lambda"), r, 0); self.edit_lambda = QtW.QDoubleSpinBox(); self.edit_lambda.setEnabled(False); fg.addWidget(self.edit_lambda, r, 2); r += 1
        fg.addWidget(QtW.QLabel("Fixed aperture"), r, 0); self.edit_fixedaperture = QtW.QDoubleSpinBox(); self.edit_fixedaperture.setEnabled(False); fg.addWidget(self.edit_fixedaperture, r, 2); r += 1
        self.rb_fixedap = QtW.QRadioButton("Fixed"); self.rb_scaledap = QtW.QRadioButton("Scaled"); self.rb_fixedap.setEnabled(False); self.rb_scaledap.setEnabled(False)
        fg.addWidget(self.rb_fixedap, r, 0); fg.addWidget(self.rb_scaledap, r, 1); r += 1
        def toggle_perm(on: bool):
            for w in [self.edit_aperturefactor, self.edit_apertureexponent, self.edit_lambda, self.edit_fixedaperture, self.rb_fixedap, self.rb_scaledap]:
                w.setEnabled(on)
        self.chk_permellipse.toggled.connect(toggle_perm)
        v.addWidget(fluid_box)

        # Flip axes and select graph endpoints
        self.btn_flipx = QtW.QPushButton("Flip X"); self.btn_flipx.clicked.connect(lambda: (self.canvas_map.ax.invert_xaxis(), self.canvas_map.draw_idle()))
        self.btn_flipy = QtW.QPushButton("Flip Y"); self.btn_flipy.clicked.connect(lambda: (self.canvas_map.ax.invert_yaxis(), self.canvas_map.draw_idle()))
        self.btn_select_graph = QtW.QPushButton("Select graph endpoints…"); self.btn_select_graph.clicked.connect(self._not_implemented)
        v.addWidget(self.btn_flipx)
        v.addWidget(self.btn_flipy)
        v.addWidget(self.btn_select_graph)

        # Botão para salvar figuras (equivalente a imprimir/exportar)
        self.btn_save = QtW.QPushButton("Save figures…")
        self.btn_save.clicked.connect(self.action_save_figures)
        v.addWidget(self.btn_save)

        v.addStretch(1)

        # Right plots area: grande área do mapa e, abaixo, rosa (ocultável)
        right = QtW.QWidget(); right_layout = QtW.QVBoxLayout(right)
        self.canvas_map = MplCanvas(width=7, height=6, dpi=100, polar=False)
        right_layout.addWidget(self.canvas_map)
        self.canvas_rose_parent = QtW.QGroupBox("Rose Diagram"); self.canvas_rose_parent.setVisible(False)
        rose_layout = QtW.QVBoxLayout(self.canvas_rose_parent)
        self.canvas_rose = MplCanvas(width=6, height=4, dpi=100, polar=True)
        rose_layout.addWidget(self.canvas_rose)
        right_layout.addWidget(self.canvas_rose_parent)

        layout.addWidget(controls, 0)
        layout.addWidget(right, 1)

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
        for i in range(1, self.tabs.count()):
            self.tabs.setTabEnabled(i, False)
        # Top row: canvas on the left, tabs+paged content on the right
        top_row = QtW.QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        self.canvas_map = MplCanvas(width=8, height=6, dpi=100, polar=False)
        # Now that canvas exists, wire flip buttons
        self.btn_flipx.clicked.connect(lambda: (self.canvas_map.ax.invert_xaxis(), self.canvas_map.draw_idle()))
        self.btn_flipy.clicked.connect(lambda: (self.canvas_map.ax.invert_yaxis(), self.canvas_map.draw_idle()))
        top_row.addWidget(self.canvas_map, 3)
        # Right column holds the tabs pages on top and the footer directly below them
        right_col_w = QtW.QWidget()
        right_col = QtW.QVBoxLayout(right_col_w)
        right_col.setContentsMargins(0, 0, 0, 0)
        right_col.setSpacing(6)
        self.tabs.setContentsMargins(0, 0, 0, 0)
        right_col.addWidget(self.tabs)
        top_row.addWidget(right_col_w, 2)
        v.addLayout(top_row, 1)

        # Maps tab content: options only (no canvas inside tabs)
        maps_layout = QtW.QVBoxLayout(self.tab_maps)
        maps_layout.setContentsMargins(2, 2, 2, 2)
        maps_layout.setSpacing(4)
        opts = QtW.QWidget(); og = QtW.QGridLayout(opts); og.setColumnStretch(0, 1); og.setColumnStretch(1, 1)
        og.setContentsMargins(2, 2, 2, 2)
        og.setHorizontalSpacing(8)
        og.setVerticalSpacing(4)

        grp_maps = QtW.QGroupBox("Maps")
        gm = QtW.QVBoxLayout(grp_maps)
        # Compact, uniform margins and spacing (reduce top padding)
        gm.setContentsMargins(4, 4, 4, 4)
        gm.setSpacing(3)
        self.chk_traces_segments = QtW.QCheckBox("Traces, segments"); self.chk_traces_segments.setChecked(True)
        # "Show nodes" subordinado (recuado e dependente de "Traces, segments")
        self.chk_show_nodes = QtW.QCheckBox("Show nodes")
        indented = QtW.QWidget(); indented_layout = QtW.QHBoxLayout(indented)
        indented_layout.setContentsMargins(10, 0, 0, 0)
        indented_layout.setSpacing(0)
        indented_layout.addWidget(self.chk_show_nodes)
        # Construir um bloco compacto para o topo esquerdo
        traces_box = QtW.QWidget(); tv = QtW.QVBoxLayout(traces_box)
        tv.setContentsMargins(0, 0, 0, 0)
        # Espaçamento entre linhas igual aos demais grupos
        tv.setSpacing(4)
        tv.addWidget(self.chk_traces_segments)
        tv.addWidget(indented)
        # Toggle enablement e replot quando pai muda
        self.chk_traces_segments.toggled.connect(self._toggle_traces_options)
        # Build nested groups to live inside "Maps"
        grp_fs = QtW.QGroupBox("Fracture stability")
        gf = QtW.QGridLayout(grp_fs); r = 0
        gf.setContentsMargins(4, 4, 4, 4)
        gf.setHorizontalSpacing(6)
        gf.setVerticalSpacing(3)
        self.chk_slip = QtW.QCheckBox("Slip tendency"); gf.addWidget(self.chk_slip, r, 0, 1, 2); r += 1
        self.chk_dilation = QtW.QCheckBox("Dilation tendency"); gf.addWidget(self.chk_dilation, r, 0, 1, 2); r += 1
        self.chk_suscept = QtW.QCheckBox("Fracture susceptibility"); gf.addWidget(self.chk_suscept, r, 0, 1, 2); r += 1
        self.chk_crit = QtW.QCheckBox("Critically stressed fractures"); gf.addWidget(self.chk_crit, r, 0, 1, 2); r += 1
        def add_param(label: str, default: float, decimals: int = 1):
            nonlocal r
            gf.addWidget(QtW.QLabel(label), r, 0)
            sp = QtW.QDoubleSpinBox(); sp.setRange(-1e6, 1e6); sp.setDecimals(decimals); sp.setValue(default); sp.setEnabled(False)
            gf.addWidget(sp, r, 1); r += 1
            return sp
        self.sp_sigma1 = add_param("Sigma 1, MPa", 100.0)
        self.sp_sigma2 = add_param("Sigma 2, MPa", 50.0)
        self.sp_angle = add_param("Angle of Sigma 1 from Y-axis", 0.0, decimals=0)
        self.sp_cohesion = add_param("Cohesion, MPa", 0.0)
        self.sp_pore = add_param("Pore pressure, MPa", 0.0)
        self.sp_fric = add_param("Friction coefficient", 0.6, decimals=2)
        # Add to Maps group later via a grid

        grp_cc = QtW.QGroupBox("Colour-coded maps")
        gc = QtW.QVBoxLayout(grp_cc)
        gc.setContentsMargins(4, 4, 4, 4)
        gc.setSpacing(3)
        self.chk_traces_by_len = QtW.QCheckBox("Traces, by length")
        self.chk_segments_by_len = QtW.QCheckBox("Segments, by length")
        self.chk_segments_by_strike = QtW.QCheckBox("Segments, by strike"); self.chk_segments_by_strike.setChecked(True)
        gc.addWidget(self.chk_traces_by_len)
        gc.addWidget(self.chk_segments_by_len)
        gc.addWidget(self.chk_segments_by_strike)
        # Add to Maps group later via a grid

        grp_id = QtW.QGroupBox("Intensity & Density")
        gi = QtW.QGridLayout(grp_id); r = 0
        gi.setContentsMargins(4, 4, 4, 4)
        gi.setHorizontalSpacing(6)
        gi.setVerticalSpacing(3)
        self.chk_est_intensity = QtW.QCheckBox("Estimated Intensity, P21"); gi.addWidget(self.chk_est_intensity, r, 0, 1, 2); r += 1
        self.chk_est_density = QtW.QCheckBox("Estimated Density, P20"); gi.addWidget(self.chk_est_density, r, 0, 1, 2); r += 1
        self.chk_showcircles = QtW.QCheckBox("Show scan circles"); self.chk_showcircles.setEnabled(False); gi.addWidget(self.chk_showcircles, r, 0, 1, 2); r += 1
        gi.addWidget(QtW.QLabel("Number of scan circles"), r, 0)
        self.spin_ncircles = QtW.QSpinBox(); self.spin_ncircles.setRange(0, 10000); self.spin_ncircles.setValue(12); self.spin_ncircles.setEnabled(False)
        gi.addWidget(self.spin_ncircles, r, 1); r += 1
        def toggle_circles(_: bool):
            on = self.chk_est_intensity.isChecked() or self.chk_est_density.isChecked()
            self.chk_showcircles.setEnabled(on)
            self.spin_ncircles.setEnabled(on and self.chk_showcircles.isChecked())
        self.chk_est_intensity.toggled.connect(toggle_circles)
        self.chk_est_density.toggled.connect(toggle_circles)
        self.chk_showcircles.toggled.connect(lambda on: self.spin_ncircles.setEnabled(on))
        # Add to Maps group later via a grid

        # Grid interno em "Maps" para alinhar como no MATLAB
        maps_inner = QtW.QWidget(); ig = QtW.QGridLayout(maps_inner)
        ig.setContentsMargins(0, 0, 0, 0)
        ig.setHorizontalSpacing(8)
        ig.setVerticalSpacing(4)
        ig.setColumnStretch(0, 1); ig.setColumnStretch(1, 1)
        # Control vertical sizing: todos compactos; direita empilhada (Colour-coded maps em cima,
        # Intensity & Density logo abaixo)
        grp_fs.setSizePolicy(QtW.QSizePolicy.Preferred, QtW.QSizePolicy.Maximum)
        grp_cc.setSizePolicy(QtW.QSizePolicy.Preferred, QtW.QSizePolicy.Maximum)
        grp_id.setSizePolicy(QtW.QSizePolicy.Preferred, QtW.QSizePolicy.Maximum)
        traces_box.setSizePolicy(QtW.QSizePolicy.Preferred, QtW.QSizePolicy.Maximum)
        # Linha superior: à esquerda o bloco Traces/Show nodes; à direita Colour-coded maps
        ig.addWidget(traces_box, 0, 0)
        ig.addWidget(grp_cc, 0, 1)
        # Linha inferior: à esquerda Fracture stability; à direita Intensity & Density
        ig.addWidget(grp_fs, 1, 0)
        ig.addWidget(grp_id, 1, 1)
        # Não esticar para baixo; manter espaçamentos uniformes
        ig.setRowStretch(0, 0)
        ig.setRowStretch(1, 0)
        gm.addWidget(maps_inner)

        og.addWidget(grp_maps, 0, 0, 2, 2)

        maps_layout.addWidget(opts, 1)
        # Inicializa o estado subordinado dos nós
        self._toggle_traces_options(self.chk_traces_segments.isChecked())

        # Footer: filename tag, Run, Exit, version/email and large logo
        footer = QtW.QGridLayout()
        footer.addWidget(QtW.QLabel("Filename tag for this run"), 0, 0)
        self.edit_run_tag = QtW.QLineEdit("Run1"); footer.addWidget(self.edit_run_tag, 0, 1)
        self.btn_run = QtW.QPushButton("Run"); self.btn_run.setEnabled(False); footer.addWidget(self.btn_run, 1, 0)
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
        # Generate plots in a separate window
        if not getattr(self, "_segments", []):
            QtW.QMessageBox.information(self, "No data", "Load and preview a node file first.")
            return
        self._open_plot_window()

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
        self.btn_flipx.setEnabled(True); self.btn_flipy.setEnabled(True)

        self._update_stats()
        # Show preview in the embedded canvas
        self._replot_map()
        self._replot_rose()
        self._update_run_enabled()

    # ----- Plot helpers -----
    def _replot_map(self) -> None:
        ax = self.canvas_map.ax
        ax.clear()
        if self._segments:
            # Preview always shows traces; nodes only if enabled and checked
            show_nodes = bool(self.chk_show_nodes.isEnabled() and self.chk_show_nodes.isChecked())
            plot_tracemap(self._segments, ax=ax, show_nodes=show_nodes)
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
        QtW.QMessageBox.information(self, "Not implemented", "This action is not implemented yet in FracPy.")

    def _toggle_traces_options(self, on: bool) -> None:
        # Habilita/desabilita "Show nodes" subordinado a "Traces, segments"
        self.chk_show_nodes.setEnabled(on)
        if not on and self.chk_show_nodes.isChecked():
            # If parent unchecked, also uncheck child
            self.chk_show_nodes.setChecked(False)
        # Embedded canvas no longer reflects immediate plot
        self._update_run_enabled()

    def _open_plot_window(self) -> None:
        # Create or reuse a separate window for plots
        if self._plot_window is None:
            self._plot_window = QtW.QMainWindow(self)
            self._plot_window.setWindowTitle("FracPy - Maps")
            cw = QtW.QWidget(); lay = QtW.QVBoxLayout(cw)
            canvas = MplCanvas(width=8, height=6, dpi=100, polar=False)
            lay.addWidget(canvas)
            self._plot_window.setCentralWidget(cw)
            self._plot_window._canvas = canvas  # store
        # Plot according to options
        ax = self._plot_window._canvas.ax
        ax.clear()
        if self.chk_traces_segments.isChecked():
            show_nodes = self.chk_show_nodes.isChecked()
            plot_tracemap(self._segments, ax=ax, show_nodes=show_nodes)
        self._plot_window._canvas.draw_idle()
        self._plot_window.show()

    def _update_run_enabled(self) -> None:
        # Enable Run if any checkbox in tabs is checked and data is loaded
        if not hasattr(self, "btn_run"):
            return
        checks = self.tab_maps.findChildren(QtW.QCheckBox)
        any_checked = any(cb.isChecked() for cb in checks)
        self.btn_run.setEnabled(bool(getattr(self, "_segments", [])) and any_checked)
