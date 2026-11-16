# Controles e grupos do FIG

Todos os objetos com Tag estão relacionados abaixo. Propriedades completas, callbacks, hierarquia e posições: [JSON principal](../../tests/reference/gui/guiFracPaQ2D.json). Associação a IDs é rastreabilidade de referência, não cobertura Qt implementada. Propriedades ausentes no arquivo dependem dos defaults MATLAB; confirmar em captura real.

| Tag / objectName futuro | Tipo | Grupo pai | IDs relacionados |
| --- | --- | --- | --- |
| `figure_main` | figure | `None` | UI-01 |
| `axes_icon` | axes | `figure_main` | UI-02 |
| `axes_tracemap` | axes | `figure_main` | UI-07, UI-17, IN-10 |
| `axes_logo` | axes | `figure_main` | UI-02 |
| `text19` | text | `figure_main` | UI-02 |
| `uipanel1` | uipanel | `figure_main` | UI-01 |
| `text3` | text | `uipanel1` | UI-01 |
| `uibuttongroup1` | uitools.uibuttongroup | `uipanel1` | UI-01 |
| `radiobutton_node` | radiobutton | `uibuttongroup1` | UI-05, IN-01 |
| `radiobutton_image` | radiobutton | `uibuttongroup1` | UI-05, IN-12 |
| `uibuttongroup5` | uitools.uibuttongroup | `uipanel1` | UI-01 |
| `label_houghpeaks` | text | `uibuttongroup5` | IN-15 |
| `label_houghthreshold` | text | `uibuttongroup5` | IN-15 |
| `label_fillgap` | text | `uibuttongroup5` | IN-15 |
| `label_minlength` | text | `uibuttongroup5` | IN-15 |
| `edit_houghpeaks` | edit | `uibuttongroup5` | IN-15 |
| `edit_houghthreshold` | edit | `uibuttongroup5` | IN-15 |
| `edit_fillgap` | edit | `uibuttongroup5` | IN-15 |
| `edit_minlength` | edit | `uibuttongroup5` | IN-15 |
| `edit_filename` | edit | `uipanel1` | UI-03, IN-01, IN-11 |
| `pushbutton_browse` | pushbutton | `uipanel1` | UI-04 |
| `text13` | text | `uipanel1` | UI-01 |
| `edit_scaling` | edit | `uipanel1` | IN-04 |
| `pushbutton_flipy` | pushbutton | `uipanel1` | UI-09, ANG-08, WAV-12 |
| `pushbutton_flipx` | pushbutton | `uipanel1` | UI-09, ANG-08, WAV-12 |
| `pushbutton_preview` | pushbutton | `uipanel1` | UI-06, IN-02, IN-03, IN-05, IN-06, IN-07, IN-08, IN-09, IN-13, IN-14, IN-16, IN-17, IN-18 |
| `uibuttongroup7` | uitools.uibuttongroup | `figure_main` | UI-01 |
| `label_stats` | text | `uibuttongroup7` | UI-08 |
| `text_message` | text | `figure_main` | UI-14, UI-15, UI-18 |
| `uibgTabMaps` | uitools.uibuttongroup | `figure_main` | UI-19 |
| `checkbox_tracemap` | checkbox | `uibgTabMaps` | MAP-01, MAP-03 |
| `checkbox_shownodes` | checkbox | `uibgTabMaps` | MAP-02 |
| `uipanel5` | uipanel | `uibgTabMaps` | UI-19 |
| `checkbox_sliptendency` | checkbox | `uipanel5` | MAP-11, MAP-16, MAP-17 |
| `checkbox_dilationtendency` | checkbox | `uipanel5` | MAP-12 |
| `edit_sigma1` | edit | `uipanel5` | MAP-15 |
| `label_sigma1` | text | `uipanel5` | MAP-15 |
| `label_sigma2` | text | `uipanel5` | MAP-15 |
| `edit_sigma2` | edit | `uipanel5` | MAP-15 |
| `label_thetasigma1` | text | `uipanel5` | MAP-15 |
| `edit_thetasigma1` | edit | `uipanel5` | MAP-15 |
| `checkbox_fracsuscep` | checkbox | `uipanel5` | MAP-13 |
| `checkbox_CSF` | checkbox | `uipanel5` | MAP-14 |
| `label_C0` | text | `uipanel5` | MAP-15 |
| `edit_C0` | edit | `uipanel5` | MAP-15 |
| `edit_Pf` | edit | `uipanel5` | MAP-15 |
| `label_mu` | text | `uipanel5` | MAP-15 |
| `label_Pf` | text | `uipanel5` | MAP-15 |
| `edit_mu` | edit | `uipanel5` | MAP-15 |
| `uipanel6` | uipanel | `uibgTabMaps` | UI-19 |
| `checkbox_tracemaplength` | checkbox | `uipanel6` | MAP-04 |
| `checkbox_segmentmaplength` | checkbox | `uipanel6` | MAP-05 |
| `checkbox_segmentmapstrike` | checkbox | `uipanel6` | MAP-06 |
| `uipanel4` | uipanel | `uibgTabMaps` | UI-19 |
| `checkbox_intensitymap` | checkbox | `uipanel4` | MAP-07, MAP-10, MAP-18 |
| `checkbox_densitymap` | checkbox | `uipanel4` | MAP-08, MAP-18 |
| `checkbox_showcircles` | checkbox | `uipanel4` | MAP-09 |
| `label_numscancircles` | text | `uipanel4` | MAP-09 |
| `edit_numscancircles` | edit | `uipanel4` | MAP-09 |
| `uibgTabAngles` | uitools.uibuttongroup | `figure_main` | UI-01 |
| `checkbox_histoangle` | checkbox | `uibgTabAngles` | ANG-01 |
| `popupmenu_histoanglebins` | popupmenu | `uibgTabAngles` | ANG-01 |
| `checkbox_rose` | checkbox | `uibgTabAngles` | ANG-02, ANG-09 |
| `checkbox_roselengthweighted` | checkbox | `uibgTabAngles` | ANG-04 |
| `checkbox_showrosemean` | checkbox | `uibgTabAngles` | ANG-05 |
| `checkbox_rosecolour` | checkbox | `uibgTabAngles` | ANG-06 |
| `popupmenu_rosebins` | popupmenu | `uibgTabAngles` | ANG-03 |
| `edit_degfromnorth` | edit | `uibgTabAngles` | ANG-07 |
| `label_degfromnorth` | text | `uibgTabAngles` | ANG-07 |
| `text_histoanglebins` | text | `uibgTabAngles` | ANG-01 |
| `text_rosebins` | text | `uibgTabAngles` | UI-01 |
| `uibgTabLengths` | uitools.uibuttongroup | `figure_main` | UI-01 |
| `checkbox_censor` | checkbox | `uibgTabLengths` | LEN-05 |
| `checkbox_histolength` | checkbox | `uibgTabLengths` | LEN-01, LEN-02, LEN-16 |
| `popupmenu_histolengthbins` | popupmenu | `uibgTabLengths` | LEN-02 |
| `checkbox_logloglength` | checkbox | `uibgTabLengths` | LEN-03, LEN-04 |
| `checkbox_mle` | checkbox | `uibgTabLengths` | LEN-07, LEN-08, LEN-09, LEN-11, LEN-12 |
| `edit_lc` | edit | `uibgTabLengths` | LEN-10 |
| `edit_uc` | edit | `uibgTabLengths` | LEN-10 |
| `checkbox_seglenvariogram` | checkbox | `uibgTabLengths` | LEN-15 |
| `label_uc` | text | `uibgTabLengths` | LEN-10 |
| `checkbox_crossplot` | checkbox | `uibgTabLengths` | LEN-06 |
| `checkbox_blocksize` | checkbox | `uibgTabLengths` | LEN-13, LEN-14 |
| `text_histolengthbins` | text | `uibgTabLengths` | LEN-02 |
| `label_lc` | text | `uibgTabLengths` | LEN-10 |
| `uibgTabFluid` | uitools.uibuttongroup | `figure_main` | UI-01 |
| `uibuttongroup_apertures` | uitools.uibuttongroup | `uibgTabFluid` | UI-01 |
| `label_apertureexponent` | text | `uibuttongroup_apertures` | FLO-11 |
| `radiobutton_fixedaperture` | radiobutton | `uibuttongroup_apertures` | FLO-10 |
| `edit_fixedaperture` | edit | `uibuttongroup_apertures` | FLO-10 |
| `radiobutton_scaledaperture` | radiobutton | `uibuttongroup_apertures` | FLO-11 |
| `edit_aperturefactor` | edit | `uibuttongroup_apertures` | FLO-11 |
| `edit_apertureexponent` | edit | `uibuttongroup_apertures` | FLO-11 |
| `label_aperturefactor` | text | `uibuttongroup_apertures` | FLO-11 |
| `label_fixedaperture` | text | `uibuttongroup_apertures` | FLO-10 |
| `checkbox_triangle` | checkbox | `uibgTabFluid` | FLO-01, FLO-03, FLO-04, FLO-05, FLO-07 |
| `edit_numblocksmap` | edit | `uibgTabFluid` | FLO-06 |
| `checkbox_permellipse` | checkbox | `uibgTabFluid` | FLO-09, FLO-13 |
| `edit_lambda` | edit | `uibgTabFluid` | FLO-12 |
| `label_lambda` | text | `uibgTabFluid` | FLO-12 |
| `uibuttongroup12` | uitools.uibuttongroup | `uibgTabFluid` | UI-01 |
| `checkbox_cracktensor` | checkbox | `uibuttongroup12` | FLO-08 |
| `label_numblocksmap` | text | `uibgTabFluid` | FLO-06 |
| `label_numpixelsItoY` | text | `uibgTabFluid` | FLO-02 |
| `edit_numpixelsItoY` | edit | `uibgTabFluid` | FLO-02 |
| `uibgTabButtons` | uitools.uibuttongroup | `figure_main` | UI-01 |
| `pbMapsTab` | pushbutton | `uibgTabButtons` | UI-10 |
| `pbLengthsTab` | pushbutton | `uibgTabButtons` | UI-10 |
| `pbAnglesTab` | pushbutton | `uibgTabButtons` | UI-10 |
| `pbFluidTab` | pushbutton | `uibgTabButtons` | UI-10 |
| `pbWaveletsTab` | pushbutton | `uibgTabButtons` | UI-10 |
| `pbGraphsTab` | pushbutton | `uibgTabButtons` | UI-10 |
| `pushbutton_run` | pushbutton | `figure_main` | UI-11, UI-12, GRA-13 |
| `pushbutton_exit` | pushbutton | `figure_main` | UI-13 |
| `text4` | text | `figure_main` | UI-02 |
| `uibgTabWavelets` | uitools.uibuttongroup | `figure_main` | UI-01 |
| `checkbox_wavelet` | checkbox | `uibgTabWavelets` | WAV-01, WAV-06, WAV-07, WAV-08, WAV-09, WAV-10, WAV-11 |
| `edit_aString` | edit | `uibgTabWavelets` | WAV-03 |
| `label_aString` | text | `uibgTabWavelets` | WAV-03 |
| `label_DegString` | text | `uibgTabWavelets` | WAV-05 |
| `uipanel7` | uipanel | `uibgTabWavelets` | UI-01 |
| `radiobutton_Morlet` | radiobutton | `uipanel7` | WAV-02 |
| `radiobutton_Mexican` | radiobutton | `uipanel7` | WAV-02 |
| `label_LString` | text | `uibgTabWavelets` | WAV-04 |
| `edit_LString` | edit | `uibgTabWavelets` | WAV-04 |
| `edit_DegString` | edit | `uibgTabWavelets` | WAV-05 |
| `uibgTabGraphs` | uitools.uibuttongroup | `figure_main` | UI-01 |
| `uibuttongroup20` | uitools.uibuttongroup | `uibgTabGraphs` | UI-01 |
| `checkbox_tracelengthgraphfrom` | checkbox | `uibuttongroup20` | GRA-10 |
| `checkbox_segmentlengthgraphfrom` | checkbox | `uibuttongroup20` | GRA-11 |
| `checkbox_segmentanglegraphfrom` | checkbox | `uibuttongroup20` | GRA-12 |
| `uibuttongroup19` | uitools.uibuttongroup | `uibgTabGraphs` | UI-01 |
| `checkbox_tracelengthgraphalong` | checkbox | `uibuttongroup19` | GRA-03 |
| `checkbox_segmentlengthgraphalong` | checkbox | `uibuttongroup19` | GRA-04 |
| `checkbox_segmentstrikegraphalong` | checkbox | `uibuttongroup19` | GRA-05 |
| `checkbox_intensitygraphalong` | checkbox | `uibuttongroup19` | GRA-06 |
| `checkbox_densitygraphalong` | checkbox | `uibuttongroup19` | GRA-07 |
| `label_numscancirclesgraph` | text | `uibuttongroup19` | GRA-08 |
| `edit_numscancirclesgraph` | edit | `uibuttongroup19` | GRA-08 |
| `pushbutton_selectgraphendpoints` | pushbutton | `uibgTabGraphs` | GRA-01, GRA-02, GRA-09 |
| `text55` | text | `figure_main` | UI-01 |
| `edit_FilenameTag` | edit | `figure_main` | UI-16 |
