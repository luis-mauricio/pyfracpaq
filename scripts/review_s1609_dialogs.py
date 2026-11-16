"""Point 1 only: exercise native input/dialog UI without exporting analyses."""

import argparse
import time
from pathlib import Path

from PySide6.QtWidgets import QApplication,QLabel
from shiboken6 import isValid

from pyfracpaq import __version__
from pyfracpaq.app import configure_application
from pyfracpaq.gui import MainWindow
from pyfracpaq.gui.wavelet_dialog import WaveletDialog
from reference_common import ROOT,sha256,write_json


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir',type=Path,required=True)
    parser.add_argument('--input',type=Path,required=True)
    parser.add_argument('--manual-picker',action='store_true')
    parser.add_argument('--keep-open',action='store_true')
    args=parser.parse_args()
    if not args.manual_picker:
        parser.error('Use --manual-picker and interact with the real macOS picker; Qt timers do not drive its native modal loop.')
    out=args.output_dir.resolve();out.mkdir(parents=True,exist_ok=True)
    app=QApplication([]);app.setQuitOnLastWindowClosed(False);configure_application(app)
    assert app.platformName()=='cocoa','This script is the native macOS review.'
    window=MainWindow();window.show();app.processEvents();checks=[];captures=[]

    def capture(widget,name):
        app.processEvents();path=out/(name+'.png');assert widget.grab().save(str(path))
        captures.append({'name':name,'path':path.name,'sha256':sha256(path),
                         'logical_size':[widget.width(),widget.height()]})

    def wait_until(predicate):
        start=time.monotonic()
        while not predicate():
            app.processEvents();time.sleep(.01)
            assert time.monotonic()-start<10,'GUI event did not complete.'
        app.processEvents()

    capture(window,'startup-full-width')
    available=window.screen().availableGeometry()
    assert window.frameGeometry().width()==available.width()
    checks.append({'check':'startup width includes native frame','passed':True,
                   'available':list(available.getRect()),'frame':list(window.frameGeometry().getRect())})
    picker_actions=[]
    def browse(select):
        print('Browse: '+('select' if select else 'cancel'),flush=True)
        window.browse()
        picker_actions.append({'action':'select' if select else 'cancel',
                               'method':'Direct interaction with native macOS open-panel; Computer Use in this recorded review'})
    original_input=window.controls['edit_filename'].text()
    browse(False);assert window.controls['edit_filename'].text()==original_input
    browse(True);assert Path(window.controls['edit_filename'].text()).resolve()==args.input.resolve()
    checks.append({'check':'native file chooser cancel/select; accented path and uppercase TXT',
                   'passed':True,'actions':picker_actions,'input_sha256':sha256(args.input.resolve())})
    capture(window,'native-file-selected')

    window.controls['edit_filename'].setText(str(out/'missing-input.txt'))
    window.preview();wait_until(lambda:not window.busy)
    assert window.last_error and window.messages
    message=window.messages[-1];assert message.isVisible();capture(message,'main-input-error')
    assert message.textFormat().name=='PlainText'
    message.accept();app.processEvents();app.processEvents()
    checks.append({'check':'input error visible, plain text and field focus restored','passed':True,
                   'focus_target':window.focusWidget().objectName() if window.focusWidget() else None})
    assert window.focusWidget() is window.controls['edit_filename']

    window.controls['edit_filename'].setText(str(args.input.resolve()))
    window.preview();wait_until(lambda:not window.busy)
    assert window.last_error is None and window.dataset.n_traces==445
    assert window.controls['pushbutton_run'].isEnabled()
    capture(window,'valid-input-recovered')
    checks.append({'check':'valid Preview recovers after error; Run re-enabled',
                   'passed':True,'counts':[window.dataset.n_traces,window.dataset.n_segments,window.dataset.n_nodes]})
    window.controls['edit_scaling'].setText('2');app.processEvents()
    assert window.dataset is None and not window.controls['pushbutton_run'].isEnabled()
    capture(window,'preview-invalidated')
    checks.append({'check':'editing input invalidates Preview and disables Run','passed':True})

    raster=ROOT/'tests/reference/sprint14/native/morlet/FracPaQ2D_wavelet_traces.png'
    dialog=WaveletDialog(raster,directory=out,parent=window);dialog.show();app.processEvents()
    fit=[]
    for size in ((520,320),(400,260),(650,400)):
        dialog.resize(*size);app.processEvents();capture(dialog,f'wavelet-{size[0]}')
        violations=[]
        for name,widget in dialog.widgets.items():
            if isinstance(widget,QLabel) and widget.text():
                fm=widget.fontMetrics()
                if fm.height()>widget.height() or fm.horizontalAdvance(widget.text())>widget.width():
                    violations.append({'control':name,'size':[widget.width(),widget.height()],
                                       'required':[fm.horizontalAdvance(widget.text()),fm.height()]})
        fit.append({'requested_size':list(size),'actual_size':[dialog.width(),dialog.height()],
                    'text_fit_violations':violations})
    dialog.resize(520,320);dialog.widgets['edit_aString'].setText('0')
    dialog.widgets['pb_Run'].click();app.processEvents()
    assert dialog.thread is None and dialog.messages
    warning=dialog.messages[-1];assert warning.isVisible();capture(warning,'wavelet-input-error');warning.accept()
    dialog.widgets['pb_Cancel'].click();app.processEvents();assert not dialog.isVisible()
    checks.append({'check':'Wavelet dialog default/enlarged/compact layout, input error and Cancel',
                   'passed':not any(r['text_fit_violations'] for r in fit),'layouts':fit})
    if args.keep_open:
        capture(window,'ready-for-exit')
        print('Ready for native Exit check.',flush=True)
        window.destroyed.connect(app.quit)
        app.exec()
        assert not isValid(window)
    else:
        window.controls['pushbutton_exit'].click();app.processEvents()
        assert not isValid(window) or not window.isVisible()
    checks.append({'check':'Exit closes the main window','passed':True})
    write_json(out/'manifest.json',{'version':__version__,'platform':app.platformName(),
        'scope':'S16-09 point 1 only: real Cocoa widgets and native file chooser driven through Qt APIs; no scientific Run, product export or release build.',
        'checks':checks,'captures':captures,'passed':all(c['passed'] for c in checks)})
    print('Native dialog checks:',len(checks),'; passed:',all(c['passed'] for c in checks),flush=True)


if __name__=='__main__':main()
