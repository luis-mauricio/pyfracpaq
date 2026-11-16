"""Small MATLAB-style TeX layout for the port's labels, using free fonts.

Native SVG probes use Arial runs, Computer Modern symbols, scripts at 80%
of the base size and a half-line script offset. Mathtext's LaTeX defaults use
smaller scripts and different baselines. Unsupported expressions retain the
ordinary Matplotlib renderer. No MathWorks font file is redistributed.
"""

from contextlib import contextmanager
from functools import lru_cache
from math import ceil,cos,sin,radians
import re

from matplotlib import font_manager
from matplotlib._mathtext_data import latex_to_bakoma
from matplotlib.backends.backend_agg import get_hinting_flag
from matplotlib.textpath import TextPath
from matplotlib.transforms import Affine2D

FONT_SCALE=1.0015
SUBSCRIPT_DROP=.475
ORIGIN_X_POINTS=-.36
ORIGIN_Y_POINTS=.6
ARIAL_OUTLINE_STROKE=.04


@lru_cache(maxsize=1024)
def literal_path(char,properties):
    return TextPath((0,0),char,prop=properties)

def runs(text,properties):
    """Return (literal, font, baseline shift in points), or None on fallback."""
    result=[];source=text.replace('$','');position=0
    properties=properties.copy()
    bold=properties.get_weight() in ('bold','heavy','black','demibold','semibold')
    if bold:properties.set_size(properties.get_size_in_points()*FONT_SCALE)
    base_size=properties.get_size_in_points()

    def parse(font,shift=0,closing=False):
        nonlocal position
        plain=[]
        def flush():
            if plain:result.append((''.join(plain),font.copy(),shift));plain.clear()
        while position<len(source):
            token=source[position];position+=1
            if token=='}':
                if not closing:raise ValueError('Unexpected closing brace')
                flush();return
            if token=='{':
                flush();parse(font.copy(),shift,True);continue
            if token in '_^':
                flush();script=font.copy();script.set_size(font.get_size_in_points()*.8)
                offset=(ceil(base_size*.45) if token=='^' else
                        -base_size*SUBSCRIPT_DROP if bold else -ceil(base_size*.45))
                if position>=len(source):raise ValueError('Missing script')
                if source[position]=='{':position+=1;parse(script,shift+offset,True)
                else:
                    char=source[position];position+=1;result.append((char,script,shift+offset))
                continue
            if token=='\\':
                flush();match=re.match(r'[A-Za-z]+',source[position:])
                if match is None:
                    if position<len(source) and source[position] in ',; ':
                        position+=1;result.append((' ',font.copy(),shift));continue
                    raise ValueError('Unsupported TeX escape')
                command=match[0];position+=len(command)
                if command in ('log','sin','cos','tan','exp'):
                    result.append((command,font.copy(),shift));continue
                if command in ('mathdefault','mathrm','mathregular','mathit','mathbf'):
                    if position>=len(source) or source[position]!='{':raise ValueError('Missing group')
                    position+=1;group=font.copy()
                    if command=='mathit':group.set_style('italic')
                    elif command=='mathbf':group.set_weight('bold')
                    else:group.set_style('normal')
                    parse(group,shift,True);continue
                if command in ('it','rm','bf'):
                    font=font.copy()
                    if command=='bf':font.set_weight('bold')
                    else:font.set_style('italic' if command=='it' else 'normal')
                    continue
                symbol=latex_to_bakoma.get('\\'+command)
                if symbol is None:raise ValueError('Unsupported TeX command')
                family,code=symbol;symbol_font=font.copy()
                symbol_font.set_file(font_manager.findfont(family))
                result.append((chr(code),symbol_font,shift));continue
            plain.append(token)
        if closing:raise ValueError('Unclosed group')
        flush()
    try:parse(properties.copy())
    except ValueError:return None
    return result


def layout(text,properties,renderer,measure):
    return _layout(text,properties,renderer,measure)


def _layout(text,properties,renderer,measure):
    pieces=runs(text,properties)
    if pieces is None:return None
    unit=renderer.dpi/72;x=0;top=0;bottom=0;placed=[]
    for literal,font,shift in pieces:
        width,height,descent=measure(literal,font,False)
        if synthetic_bold(font):height+=font.get_size_in_points()*.04*unit
        y=shift*unit
        placed.append((literal,font,x,y))
        top=max(top,y+height-descent);bottom=min(bottom,y-descent)
        x+=width
    return placed,(x,top-bottom,-bottom)


def synthetic_bold(font):
    return (font.get_file() is not None and 'cmmi10' in font.get_file()
            and font.get_weight() in ('bold','heavy','black','demibold','semibold'))


@contextmanager
def native_mathtext(renderer):
    if type(renderer).__name__!='RendererAgg':
        yield;return
    measure=renderer.get_text_width_height_descent;draw=renderer.draw_mathtext
    draw_text=renderer.draw_text;advances={};painting_math=False
    def unkerned(text,properties,ismath=False):
        if ismath:return measure(text,properties,ismath)
        _,height,descent=measure(text,properties,False)
        width=0.
        for char in text:
            key=(char,str(properties),get_hinting_flag())
            if key not in advances:advances[key]=measure(char,properties,False)[0]
            width+=advances[key]
        return width,height,descent
    def metrics(text,properties,ismath):
        if ismath is True:
            item=layout(text,properties,renderer,unkerned)
            if item is not None:return item[1]
        return unkerned(text,properties,ismath)
    def plain(gc,x,y,text,properties,angle,ismath=False,mtext=None):
        if ismath:return draw_text(gc,x,y,text,properties,angle,ismath,mtext)
        font=renderer._prepare_font(properties)
        items=list(font._layout(text,flags=get_hinting_flag(),features=('-kern','-liga','-clig')))
        size=properties.get_size_in_points()
        if painting_math and ARIAL_OUTLINE_STROKE is not None and not properties.get_file():
            stroke=renderer.new_gc();stroke.copy_properties(gc)
            stroke.set_linewidth(ARIAL_OUTLINE_STROKE);stroke.set_joinstyle('round')
            try:
                for char,item in zip(text,items,strict=True):
                    if char.isspace():continue
                    path=literal_path(char,properties)
                    theta=radians(angle);c=cos(theta);s=sin(theta)
                    transform=(Affine2D().scale(renderer.dpi/72).rotate_deg(angle)
                               .translate(x+item.x*c-item.y*s,renderer.height-y+item.x*s+item.y*c))
                    renderer.draw_path(stroke,path,transform,gc.get_rgb())
            finally:stroke.restore()
            return
        renderer._draw_text_glyphs_and_boxes(gc,x,y,angle,
            ((item.ft_object,size,item.glyph_index,0,1,item.x,item.y) for item in items),[])
    def render(gc,x,y,text,properties,angle):
        return paint_math(gc,x,y,text,properties,angle)
    def paint_math(gc,x,y,text,properties,angle):
        nonlocal painting_math
        item=layout(text,properties,renderer,unkerned)
        if item is None:return draw(gc,x,y,text,properties,angle)
        theta=radians(angle);c=cos(theta);s=sin(theta)
        unit=renderer.dpi/72
        if properties.get_weight() in ('bold','heavy','black','demibold','semibold'):
            x+=unit*(ORIGIN_X_POINTS*c+ORIGIN_Y_POINTS*s)
            y+=unit*(-ORIGIN_X_POINTS*s+ORIGIN_Y_POINTS*c)
        for literal,font,dx,dy in item[0]:
            px=x+dx*c-dy*s;py=y-dx*s-dy*c
            if synthetic_bold(font):
                # Native bold CMMI retains the regular glyph advance and grows
                # its outline right/up by .04 em. Use the free Matplotlib font.
                strength=font.get_size_in_points()*.04
                path=TextPath((0,0),literal,prop=font)
                transform=(Affine2D().translate(strength/2,strength/2)
                           .scale(renderer.dpi/72).rotate_deg(angle)
                           .translate(px,renderer.height-py))
                stroke=renderer.new_gc();stroke.copy_properties(gc)
                stroke.set_linewidth(strength);stroke.set_joinstyle('round')
                try:renderer.draw_path(stroke,path,transform,gc.get_rgb())
                finally:stroke.restore()
            else:
                painting_math=True
                try:renderer.draw_text(gc,px,py,literal,font,angle,ismath=False)
                finally:painting_math=False
    renderer.get_text_width_height_descent=metrics;renderer.draw_mathtext=render;renderer.draw_text=plain
    try:yield
    finally:
        renderer.get_text_width_height_descent=measure;renderer.draw_mathtext=draw;renderer.draw_text=draw_text
