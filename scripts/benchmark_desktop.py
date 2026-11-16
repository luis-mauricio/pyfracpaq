"""Measure actual Qt heartbeat through real-data compute/export and Exit."""

import argparse
import os
from pathlib import Path
import resource
import time

os.environ.setdefault('MPLCONFIGDIR','/tmp/pyfracpaq-matplotlib')
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QWidget
from shiboken6 import isValid

from pyfracpaq.app import configure_application
from pyfracpaq.gui import MainWindow
from reference_common import ROOT, REFERENCE, sha256, write_json


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--exit-during-export',action='store_true')
    args=parser.parse_args()
    folder=REFERENCE/'sprint16/benchmarks'/('exit' if args.exit_during_export else 'gui')
    folder.mkdir(parents=True,exist_ok=True);os.chdir(folder)
    source=REFERENCE/'sprint16/benchmarks/map1_prepared.txt'
    app=QApplication([]);configure_application(app)
    other=QWidget();other.show();window=MainWindow();window.show()
    beats=[];exports=[];messages=[];state={'phase':'preview'};start=time.perf_counter()
    status=window._status
    def observed_status(message):
        messages.append({'seconds':time.perf_counter()-start,'message':message});status(message)
    window._status=observed_status
    original=window.present_figure
    def present(output,context):
        begin=time.perf_counter();result=original(output,context)
        exports.append({'basename':output.basename,'seconds':time.perf_counter()-begin})
        if args.exit_during_export:QTimer.singleShot(0,window.close)
        return result
    window.present_figure=present
    heartbeat=QTimer();heartbeat.setInterval(20)
    heartbeat.timeout.connect(lambda:beats.append(time.perf_counter()-start));heartbeat.start()
    def completed(kind):
        if state['phase']=='preview':
            assert window.last_error is None
            selected=('MAP-01','MAP-04','MAP-05','MAP-06','LEN-02','ANG-01','ANG-02')
            for spec in window.registry.specs:window.controls[spec.checkbox].setChecked(spec.id in selected)
            state['phase']='run';QTimer.singleShot(0,window.run_selected)
        else:
            assert window.last_error is None
            state['seconds']=time.perf_counter()-start
            state['other_visible']=other.isVisible()
            if not args.exit_during_export:window.close()
            QTimer.singleShot(100,app.quit)
    window.job_completed.connect(completed)
    window.controls['edit_filename'].setText(str(source));QTimer.singleShot(0,window.preview)
    QTimer.singleShot(60000,app.quit);app.exec()
    assert state['phase']=='run' and 'seconds' in state, state
    gaps=[b-a for a,b in zip([0.]+beats,beats)]
    write_json(folder/'validation.json',{'source':str(source.relative_to(ROOT)),'source_sha256':sha256(source),
       'qt_platform':app.platformName(),'heartbeat_interval_seconds':.02,'heartbeat_samples':len(beats),
       'maximum_heartbeat_gap_seconds':max(gaps,default=0),'elapsed_seconds':state['seconds'],
       'exports':exports,'messages':messages,'peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
       'exit_during_export':args.exit_during_export,'main_window_deleted':not isValid(window),
       'unrelated_window_preserved':state['other_visible'],
       'scope':'Actual prepared real input, production worker/render/export, no mocks. macOS RSS bytes; Qt offscreen. '
               'Each PNG still blocks for its measured duration; event loop resumes between outputs.'})


if __name__=='__main__':main()
