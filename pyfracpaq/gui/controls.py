"""Build reference-named Qt controls and apply contextual enablement."""

from PySide6.QtCore import QLocale, Qt
from PySide6.QtGui import QDoubleValidator, QFont, QIntValidator, QPixmap
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QGroupBox, QLabel, QLineEdit, QPushButton,
    QRadioButton, QWidget,
)

from pyfracpaq.resources import ui_specification

PANELS = ('uibgTabMaps', 'uibgTabLengths', 'uibgTabAngles',
          'uibgTabFluid', 'uibgTabWavelets', 'uibgTabGraphs')
NAVIGATION = ('pbMapsTab', 'pbLengthsTab', 'pbAnglesTab',
              'pbFluidTab', 'pbWaveletsTab', 'pbGraphsTab')
HOUGH = ('edit_houghpeaks', 'edit_houghthreshold', 'edit_fillgap', 'edit_minlength')
STRESSES = ('edit_sigma1', 'edit_sigma2', 'edit_thetasigma1',
            'edit_C0', 'edit_Pf', 'edit_mu')
STABILITY = ('checkbox_sliptendency', 'checkbox_dilationtendency',
             'checkbox_fracsuscep', 'checkbox_CSF')
INTEGER_FIELDS = {'edit_houghpeaks', 'edit_numscancircles', 'edit_numblocksmap',
                  'edit_numscancirclesgraph', 'edit_DegString'}


class AspectImage(QLabel):
    def __init__(self, pixmap: QPixmap) -> None:
        super().__init__()
        self.original = pixmap
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def resizeEvent(self, event) -> None:
        self.setPixmap(self.original.scaled(
            self.size(), Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        ))
        super().resizeEvent(event)


def reference_text(value: str | list) -> str:
    return '\n'.join(value) if isinstance(value, list) else str(value)


class Controls:
    def __init__(self) -> None:
        self.reference = ui_specification()
        self.specs = {o['tag']: o for o in self.reference['objects']}
        self.widgets: dict[str, QWidget] = {}
        self.censor_available = True

    def __getitem__(self, name: str) -> QWidget:
        return self.widgets[name]

    def add(self, name: str, widget: QWidget) -> QWidget:
        widget.setObjectName(name)
        self.widgets[name] = widget
        return widget

    def make(self, name: str, parent: QWidget | None = None) -> QWidget:
        spec = self.specs[name]
        text = reference_text(spec.get('String', spec.get('Title', '')))
        style = spec.get('Style')
        if spec['type'] in ('uipanel', 'uitools.uibuttongroup'):
            widget = QGroupBox(text.replace('&', '&&'), parent)
            widget.setProperty('referenceBorder', spec.get('BorderType', 'beveledin'))
        elif style == 'text':
            widget = QLabel(text, parent)
            widget.setTextFormat(Qt.TextFormat.PlainText)
            widget.setWordWrap(True)
            alignment = {'left': Qt.AlignmentFlag.AlignLeft,
                         'center': Qt.AlignmentFlag.AlignHCenter,
                         'right': Qt.AlignmentFlag.AlignRight}
            widget.setAlignment(alignment[spec.get('HorizontalAlignment', 'center')]
                                | Qt.AlignmentFlag.AlignVCenter)
        elif style == 'edit':
            widget = QLineEdit(text, parent)
            alignment = {'left': Qt.AlignmentFlag.AlignLeft,
                         'center': Qt.AlignmentFlag.AlignHCenter,
                         'right': Qt.AlignmentFlag.AlignRight}
            widget.setAlignment(alignment[spec.get('HorizontalAlignment', 'left')])
            if name in INTEGER_FIELDS:
                widget.setValidator(QIntValidator(0, 2_147_483_647, widget))
            elif name not in ('edit_filename', 'edit_FilenameTag', 'edit_aString', 'edit_LString'):
                validator = QDoubleValidator(-1e308, 1e308, 15, widget)
                validator.setLocale(QLocale.c())
                validator.setNotation(QDoubleValidator.Notation.ScientificNotation)
                widget.setValidator(validator)
        elif style in ('checkbox', 'radiobutton'):
            cls = QCheckBox if style == 'checkbox' else QRadioButton
            widget = cls(text, parent)
            widget.setChecked(bool(spec.get('Value', 0)))
        elif style == 'popupmenu':
            widget = QComboBox(parent)
            widget.addItems(spec['String'])
            value = self.reference['opening_values'].get(name, spec.get('Value', 1))
            widget.setCurrentIndex(int(value) - 1)
        elif style == 'pushbutton':
            widget = QPushButton(text, parent)
        else:
            raise ValueError(f'Unsupported reference control: {name}')
        widget.setToolTip(spec.get('TooltipString', ''))
        return self.add(name, widget)

    def values(self) -> dict[str, bool | str]:
        values = {}
        for name, widget in self.widgets.items():
            if isinstance(widget, (QCheckBox, QRadioButton)):
                values[name] = widget.isChecked()
            elif isinstance(widget, QLineEdit):
                values[name] = widget.text()
            elif isinstance(widget, QComboBox):
                values[name] = widget.currentText()
        return values

    def dependencies(self) -> None:
        def checked(name: str) -> bool:
            return self[name].isChecked()

        def enable(names: tuple[str, ...], enabled: bool) -> None:
            for name in names:
                self[name].setEnabled(enabled)
                label = name.replace('edit_', 'label_').replace('popupmenu_', 'text_')
                if label in self.widgets:
                    self[label].setEnabled(enabled)

        enable(HOUGH, checked('radiobutton_image'))
        enable(('checkbox_shownodes',), checked('checkbox_tracemap'))
        enable(('checkbox_showcircles', 'edit_numscancircles'),
               checked('checkbox_intensitymap') or checked('checkbox_densitymap'))
        enable(STRESSES, any(checked(name) for name in STABILITY))
        enable(('popupmenu_histolengthbins',), checked('checkbox_histolength'))
        enable(('popupmenu_histoanglebins',), checked('checkbox_histoangle'))
        enable(('checkbox_mle',), checked('checkbox_logloglength'))
        enable(('checkbox_censor',), self.censor_available)
        enable(('edit_lc', 'edit_uc'),
               checked('checkbox_logloglength') and checked('checkbox_mle'))
        rose = checked('checkbox_rose')
        enable(('popupmenu_rosebins', 'checkbox_roselengthweighted',
                'checkbox_showrosemean', 'checkbox_rosecolour'), rose)
        enable(('edit_numblocksmap', 'edit_numpixelsItoY'), checked('checkbox_triangle'))
        permeability = checked('checkbox_permellipse')
        enable(('edit_lambda', 'radiobutton_fixedaperture', 'radiobutton_scaledaperture'),
               permeability)
        fixed = checked('radiobutton_fixedaperture')
        enable(('edit_fixedaperture',), permeability and fixed)
        enable(('edit_aperturefactor', 'edit_apertureexponent'), permeability and not fixed)
        enable(('edit_aString', 'edit_LString', 'edit_DegString',
                'radiobutton_Morlet', 'radiobutton_Mexican'), checked('checkbox_wavelet'))
        self['label_DegString'].setEnabled(checked('checkbox_wavelet'))
        enable(('edit_numscancirclesgraph',),
               checked('checkbox_intensitygraphalong') or checked('checkbox_densitygraphalong'))


def reference_font() -> QFont:
    return QFont('Helvetica', 9)
