"""
tkintertools
============
The tkindertools module is an auxiliary module of the tkinder module.
Minimum Requirement: Python3.10.

Provides:
1. Transparent, rounded and customized widgets
2. Automatic control of picture size and widget size
3. Scalable png pictures and playable gif pictures
4. Regular mobile widgets and canvas interfaces
5. Gradient colors and contrast colors
6. Text with controllable length and alignment
7. Convenient, inheritable singleton pattern class

Base Information
----------------
* Author: Xiaokang2022<2951256653@qq.com>
* Version: 2.5.6-pre
* Update: 2022/12/11

Contents
--------
* Container Widget: `Tk`, `Toplevel`, `Canvas`
* Virtual Canvas Widget: `CanvasLabel`, `CanvasButton`, `CanvasEntry`, `CanvasText`, `ProcessBar`
* Tool Class: `PhotoImage`, `Singleton`
* Tool Function: `move_widget`, `correct_text`, `change_color`

More
----
* GitCode: https://gitcode.net/weixin_62651706/tkintertools
* GitHub(Mirror): https://github.com/392126563/tkintertools
* Gitee(Mirror): https://gitee.com/xiaokang-2022/tkintertools
* Tutorials: https://xiaokang2022.blog.csdn.net/article/details/127374661
"""

import sys
import tkinter
from math import sqrt
from typing import Generator, Iterable, Literal, Self, Type

__author__ = 'Xiaokang2022'
__version__ = '2.5.6-pre'
__all__ = (
    'Tk',
    'Toplevel',
    'Canvas',
    'CanvasLabel',
    'CanvasButton',
    'CanvasEntry',
    'CanvasText',
    'ProcessBar',
    'PhotoImage',
    'Singleton',
    'move_widget',
    'correct_text',
    'change_color',
)

if sys.version_info < (3, 10):
    # 版本检测，低版本缺失部分语法（如类型提示中的 | 语法）
    raise RuntimeError('\033[36mPython version is too low!\033[0m\a')


COLOR_BUTTON_FILL = '#E1E1E1', '#E5F1FB', '#CCE4F7', '#F0F0F0'      # 默认的按钮内部颜色
COLOR_BUTTON_OUTLINE = '#C0C0C0', '#288CDB', '#4884B4', '#D5D5D5'   # 默认的按钮外框颜色
COLOR_TEXT_FILL = '#FFFFFF', '#FFFFFF', '#FFFFFF', '#F0F0F0'        # 默认的文本内部颜色
COLOR_TEXT_OUTLINE = '#C0C0C0', '#414141', '#288CDB', '#D5D5D5'     # 默认的文本外框颜色
COLOR_TEXT = '#000000', '#000000', '#000000', '#A3A3A3'             # 默认的文本颜色
COLOR_NONE = '', '', '', ''                                         # 透明颜色
COLOR_BAR = '#E1E1E1', '#06b025'                                    # 默认的进度条颜色

BORDERWIDTH = 1     # 默认控件外框宽度
CURSOR = '│'        # 文本光标
FONT = '楷体', 15   # 默认字体
LIMIT = -1          # 默认文本长度
NULL = ''           # 空字符
RADIUS = 0          # 默认控件圆角半径


class Tk(tkinter.Tk):
    """ 创建窗口，并处理部分`Canvas`类绑定的关联事件及缩放操作 """

    def __init__(
        self: Self,
        title: str | None = None,
        geometry: str | None = None,
        minisize: tuple[int, int] | None = None,
        alpha: float | None = None,
        shutdown=None,  # type: function | None
        **kw
    ) -> None:
        """
        `title`: 窗口标题
        `geometry`: 窗口大小及位置（格式：'宽度x高度+左上角横坐标+左上角纵坐标' 或者 '宽度x高度'）
        `minisize`: 窗口的最小缩放大小（默认为参数 geometry 的宽度与高度）
        `alpha`: 窗口透明度，范围为 0~1，0 为完全透明
        `shutdown`: 关闭窗口之前执行的函数（会覆盖原关闭操作）
        `**kw`: 与 tkinter.Tk 类的参数相同
        """
        if type(self) == Tk:  # 此行代码是为了方便后面的 Toplevel 类继承
            tkinter.Tk.__init__(self, **kw)

        self.width, self.height = [100, 1], [100, 1]  # [初始值, 当前值]

        self._canvas: list[Canvas] = []  # 子画布列表
        self._toplevel: list[Toplevel] = []  # 子窗口列表

        if minisize:
            self.minsize(*minisize)
        elif geometry:
            self.minsize(*map(int, geometry.split('+')[0].split('x')))

        self.title(title if title else None)
        self.geometry(geometry if geometry else None)
        self.attributes('-alpha', alpha if alpha else None)
        self.protocol('WM_DELETE_WINDOW', shutdown if shutdown else None)

        self.bind('<Configure>', lambda _: self.__zoom())  # 开启窗口缩放检测
        self.bind('<Any-Key>', self.__input)  # 绑定键盘输入字符（代码顺序不可错）
        self.bind('<Control-v>', lambda _: self.__paste())  # 绑定粘贴快捷键

    def __zoom(self: Self) -> None:
        """ 缩放检测 """
        width, height = map(int, self.geometry().split('+')[0].split('x'))
        # NOTE: 此处必须用 geometry 方法，直接用 Event 会有画面异常的 bug

        if (width, height) == (self.width[1], self.height[1]):  # 没有大小的改变
            return

        for canvas in self._canvas:
            if not canvas.expand:  # 不缩放的画布
                continue

            canvas.zoom(width/self.width[1], height/self.height[1])

        # 更新窗口当前的宽高值
        self.width[1], self.height[1] = width, height

    def __input(self: Self, event: tkinter.Event) -> None:
        """ 键盘输入字符事件 """
        for canvas in self._canvas:
            if not canvas.lock:
                continue

            for widget in canvas._widget[::-1]:
                if not isinstance(widget, _TextWidget):
                    continue
                if not widget.live:
                    continue
                if widget.input(event):
                    return

    def __paste(self: Self) -> None:
        """ 快捷键粘贴事件 """
        for canvas in self._canvas:
            if not canvas.lock:
                continue

            for widget in canvas._widget[::-1]:
                if not isinstance(widget, _TextWidget):
                    continue
                if not widget.live:
                    continue
                if widget.paste():
                    return

    @property
    def canvas(self: Self) -> tuple:
        """ `Tk`类的`Canvas`元组 """

    @canvas.getter
    def canvas(self: Self) -> tuple:
        return tuple(self._canvas)

    @property
    def toplevel(self: Self) -> tuple:
        """ `Tk`类的`Toplevel`元组 """

    @toplevel.getter
    def toplevel(self: Self) -> tuple:
        return tuple(self._toplevel)

    def wm_geometry(self: Self, newGeometry: str | None = None) -> str | None:
        # 重写: 添加修改初始宽高值的功能
        if newGeometry:
            self.width[0], self.height[0] = map(
                int, newGeometry.split('+')[0].split('x'))
            self.width[1], self.height[1] = self.width[0], self.height[0]
        return tkinter.Tk.wm_geometry(self, newGeometry)

    geometry = wm_geometry


class Toplevel(tkinter.Toplevel, Tk):
    """ 用法类似于`tkinter.Toplevel`类，同时增加了`Tk`的功能 """

    def __init__(
        self: Self,
        master: Tk,
        title: str | None = None,
        geometry: str | None = None,
        minisize: tuple[int, int] | None = None,
        alpha: float | None = None,
        shutdown=None,  # type: function | None
        **kw
    ) -> None:
        """
        `master`: 父窗口
        `title`: 窗口标题
        `geometry`: 窗口大小及位置（格式：'宽度x高度+左上角横坐标+左上角纵坐标' 或者 '宽度x高度'）
        `minisize`: 窗口的最小缩放大小（默认为参数 geometry 的宽度与高度）
        `alpha`: 窗口透明度，范围为 0~1，0 为完全透明
        `shutdown`: 关闭窗口之前执行的函数（会覆盖关闭操作）
        `**kw`: 与 tkinter.Toplevel 类的参数相同
        """
        tkinter.Toplevel.__init__(self, master=master, **kw)
        Tk.__init__(self, title=title, geometry=geometry,
                    minisize=minisize, alpha=alpha, shutdown=shutdown, **kw)

        # 将实例本身添加到父控件的子窗口列表中
        master._toplevel.append(self)

    def destroy(self: Self) -> None:
        # 重写: 添加了删除Tk对实例连系的功能
        self.master._toplevel.remove(self)
        return tkinter.Toplevel.destroy(self)


class Canvas(tkinter.Canvas):
    """ 用于承载虚拟的画布控件，并处理部分绑定事件 """

    def __init__(
        self: Self,
        master: Tk,
        width: int,
        height: int,
        lock: bool = True,
        expand: bool = True,
        **kw
    ) -> None:
        """
        `master`: 父控件
        `width`: 画布宽度
        `height`: 画布高度
        `lock`: 画布内控件的功能锁（False 时功能暂时失效）
        `expand`: 画布内控件是否能缩放
        `**kw`: 与 tkinter.Canvas 类的参数相同
        """
        self.width, self.height = [width]*2, [height]*2  # [初始值, 当前值]
        self.lock, self.expand = lock, expand

        self.rate_x, self.rate_y = 1., 1.  # 放缩比率

        self._widget: list[_BaseWidget] = []  # 子控件列表（与事件绑定有关）

        # 子 item 字典（与缩放功能有关）
        self._font_dict = {}  # type: dict[tkinter._CanvasItemId, float]
        self._width_dict = {}  # type: dict[tkinter._CanvasItemId, float]
        self._image_dict = {}  # type: dict[tkinter._CanvasItemId, list]

        tkinter.Canvas.__init__(self, master, width=width,
                                height=height, highlightthickness=0, **kw)

        # 将实例添加到 Tk 的画布列表中
        master._canvas.append(self)

        self.bind('<Motion>', self.__touch)  # 绑定鼠标触碰控件
        self.bind('<Button-1>', self.__press)  # 绑定鼠标左键按下
        self.bind('<B1-Motion>', self.__press)  # 绑定鼠标左键按下移动
        self.bind('<MouseWheel>', self.__mousewheel)  # 绑定鼠标滚轮滚动
        self.bind('<ButtonRelease-1>', self.__release)  # 绑定鼠标左键松开

    def zoom(self: Self, rate_x: float | None = None, rate_y: float | None = None) -> None:
        """
        缩放画布及其内部的所有元素
        `rate_x`: 横向缩放比率，默认值表示自动更新缩放（根据窗口缩放程度）
        `rate_y`: 纵向缩放比率，默认值同上
        """
        if not self.lock:
            return

        if not rate_x:
            rate_x = self.master.width[1]/self.master.width[0]/self.rate_x
        if not rate_y:
            rate_y = self.master.height[1]/self.master.height[0]/self.rate_y

        # 更新画布的位置及大小数据
        self.width[1] *= rate_x
        self.height[1] *= rate_y
        temp_x, self.rate_x = self.rate_x, self.width[1] / self.width[0]
        temp_y, self.rate_y = self.rate_y, self.height[1] / self.height[0]

        # 更新画布的位置及大小
        place_info = self.place_info()
        tkinter.Canvas.place(
            self,
            width=self.width[1],
            height=self.height[1],
            x=float(place_info['x'])*rate_x,
            y=float(place_info['y'])*rate_y)

        # 更新子画布控件的子虚拟画布控件位置数据
        for widget in self._widget:
            widget.x1 *= rate_x
            widget.x2 *= rate_x
            widget.y1 *= rate_y
            widget.y2 *= rate_y

        for item in self.find_all():  # item 位置缩放
            self.coords(item, [c*rate_y if i & 1 else c*rate_x for i,
                               c in enumerate(self.coords(item))])

        for item in self._font_dict:  # 字体大小缩放
            self._font_dict[item] *= sqrt(rate_x*rate_y)
            if font := self.itemcget(item, 'font').split():  # BUG: 不加 if 有时会有 bug
                font[1] = int(self._font_dict[item])
                self.itemconfigure(item, font=font)

        for item in self._width_dict:  # 宽度粗细缩放
            self._width_dict[item] *= sqrt(rate_x*rate_y)
            self.itemconfigure(item, width=self._width_dict[item])

        for item in self._image_dict:  # 图像大小缩放（采用相对的绝对缩放）
            if self._image_dict[item][0] and self._image_dict[item][0].file.split('.')[-1] == 'png':
                self._image_dict[item][1] = self._image_dict[item][0].zoom(
                    temp_x*rate_x, temp_y*rate_y, 1.2)
                self.itemconfigure(item, image=self._image_dict[item][1])

    def __touch(self: Self, event: tkinter.Event) -> None:
        """ 鼠标触碰控件事件 """
        if not self.lock:
            return

        for widget in self._widget[::-1]:
            if not widget.live:
                continue

            if widget.touch(event):
                if isinstance(widget, CanvasButton):
                    self.configure(cursor='hand2')
                elif isinstance(widget, _TextWidget):
                    self.configure(cursor='xterm')
                else:
                    self.configure(cursor='arrow')
                return

        self.configure(cursor='arrow')

    def __press(self: Self, event: tkinter.Event) -> None:
        """ 鼠标左键按下事件 """
        if not self.lock:
            return

        for widget in self._widget:
            if not isinstance(widget, CanvasButton | _TextWidget):
                continue
            if not widget.live:
                continue
            widget.press(event)
            # NOTE: 左键按下事件无需使用 return 加速，按下空白区域也是有作用的

    def __release(self: Self, event: tkinter.Event) -> None:
        """ 鼠标左键松开事件 """
        if not self.lock:
            return

        for widget in self._widget[::-1]:
            if not isinstance(widget, CanvasButton):
                continue
            if not widget.live:
                continue
            widget.touch(event)
            if widget.execute(event):
                return

    def __mousewheel(self: Self, event: tkinter.Event) -> None:
        """ 鼠标滚轮滚动事件 """
        if not self.lock:
            return

        for widget in self._widget[::-1]:
            if not isinstance(widget, CanvasText):
                continue
            if not widget.live:
                continue
            if widget.scroll(event):
                return

    @property
    def widget(self: Self) -> tuple:
        """ `Canvas`类的子控件元组 """

    @widget.getter
    def widget(self: Self) -> tuple:
        return tuple(self._widget)

    def set_lock(self: Self, boolean: bool) -> None:
        """
        设置画布锁，并自动执行一些功能
        `boolean`: 画布锁将要更新的值
        """
        self.lock = boolean
        if boolean and self.expand:
            self.zoom()

    def create_text(self: Self, *args, **kw):
        # 重写：添加对 text 类型的 _CanvasItemId 的字体大小的控制
        font = kw.get('font')
        if not font:
            kw['font'] = ('楷体', 10)  # 默认字体
        elif type(font) == str:
            kw['font'] = (font, 10)
        item = tkinter.Canvas.create_text(self, *args, **kw)
        self._font_dict[item] = kw['font'][1]
        return item

    def create_image(self: Self, *args, **kw):
        # 重写：添加对 image 类型的 _CanvasItemId 的图像大小的控制
        item = tkinter.Canvas.create_image(self, *args, **kw)
        self._image_dict[item] = [kw.get('image'), None]
        return item

    def create_rectangle(self: Self, *args, **kw):
        # 重写：添加对 rectangle 类型的 _CanvasItemId 的线条宽度的控制
        item = tkinter.Canvas.create_rectangle(self, *args, **kw)
        self._width_dict[item] = float(self.itemcget(item, 'width'))
        return item

    def create_line(self: Self, *args, **kw):
        # 重写：添加对 line 类型的 _CanvasItemId 的线条宽度的控制
        item = tkinter.Canvas.create_line(self, *args, **kw)
        self._width_dict[item] = float(self.itemcget(item, 'width'))
        return item

    def create_oval(self: Self, *args, **kw):
        # 重写：添加对 oval 类型的 _CanvasItemId 的线条宽度的控制
        item = tkinter.Canvas.create_oval(self, *args, **kw)
        self._width_dict[item] = float(self.itemcget(item, 'width'))
        return item

    def create_arc(self: Self, *args, **kw):
        # 重写：添加对 arc 类型的 _CanvasItemId 的线条宽度的控制
        item = tkinter.Canvas.create_arc(self, *args, **kw)
        self._width_dict[item] = float(self.itemcget(item, 'width'))
        return item

    def create_polygon(self: Self, *args, **kw):
        # 重写：添加对 polygon 类型的 _CanvasItemId 的线条宽度的控制
        item = tkinter.Canvas.create_polygon(self, *args, **kw)
        self._width_dict[item] = float(self.itemcget(item, 'width'))
        return item

    def itemconfigure(
        self: Self,
        tagOrId,  # type: str | tkinter._CanvasItemId
        **kw
    ) -> dict[str, tuple[str, str, str, str, str]] | None:
        # 重写：创建空image的_CanvasItemId时漏去对图像大小的控制
        if type(kw.get('image')) == PhotoImage:
            self._image_dict[tagOrId] = [kw.get('image'), None]
        return tkinter.Canvas.itemconfigure(self, tagOrId, **kw)

    def place(self: Self, *args, **kw) -> None:
        # 重写：增加一些特定功能
        self.width[0] = kw.get('wdith', self.width[0])
        self.height[0] = kw.get('height', self.height[0])
        return tkinter.Canvas.place(self, *args, **kw)

    def destroy(self: Self) -> None:
        # 重写：兼容
        for widget in self.widget:
            widget.destroy()
        self.master._canvas.remove(self)
        return tkinter.Canvas.destroy(self)


class _BaseWidget:
    """ 内部类: 虚拟画布控件基类 """

    def __init__(
        self: Self,
        canvas: Canvas,
        x: float,
        y: float,
        width: float,
        height: float,
        radius: int,
        text: str,
        justify: str,
        borderwidth: float,
        font: tuple[str, int, str],
        color_text: tuple[str, str, str],
        color_fill: tuple[str, str, str],
        color_outline: tuple[str, str, str]
    ) -> None:
        """
        ### 标准参数
        `canvas`: 父画布容器控件
        `x`: 控件左上角的横坐标
        `y`: 控件左上角的纵坐标
        `width`: 控件的宽度
        `height`: 控件的高度
        `radius`: 控件圆角化半径
        `text`: 控件显示的文本，对于文本控件而言，可以为一个元组：(默认文本, 鼠标触碰文本)
        `justify`: 文本的对齐方式
        `borderwidth`: 外框的宽度
        `font`: 控件的字体设定 (字体, 大小, 样式)
        `color_text`: 控件文本的颜色
        `color_fill`: 控件内部的颜色
        `color_outline`: 控件外框的颜色
        ---
        ### 特定参数
        `command`: 按钮控件的关联函数
        `show`: 文本控件的显示文本
        `limit`: 文本控件的输入字数限制，为负数时表示没有字数限制
        `space`: 文本控件能否输入空格的标识
        `read`: 文本控件的只读模式
        `cursor`: 输入提示符的字符，默认为一竖线
        ---
        ### 详细说明
        字体的值为一个包含两个或三个值的元组，共两种形式
        形式一: `(字体名称, 字体大小)`
        形式二: `(字体名称, 字体大小, 字体样式)`

        颜色为一个包含三个或四个 RGB 颜色字符串的元组，共两种形式
        不使用禁用功能时: `(正常颜色, 触碰颜色, 交互颜色)`
        需使用禁用功能时: `(正常颜色, 触碰颜色, 交互颜色, 禁用颜色)`
        """
        self.master = canvas
        self.value = text
        self.justify = justify
        self.font = font
        self.color_text = list(color_text)
        self.color_fill = list(color_fill)
        self.color_outline = list(color_outline)

        # 控件左上角坐标
        self.x1, self.y1 = x, y
        # 控件左下角坐标
        self.x2, self.y2 = x+width, y+height
        # 控件的宽高值
        self.width, self.height = width, height
        # 边角圆弧半径
        self.radius = radius
        # 控件活跃标志
        self.live = True
        # 控件的状态
        self._state = 'normal'

        # 将实例添加到父画布控件
        canvas._widget.append(self)

        if radius:
            if 2 * radius > width:
                radius = width // 2
                self.radius = radius
            if 2 * radius > height:
                radius = height // 2
                self.radius = radius

            d = 2*radius  # 圆角直径
            _x, _y, _w, _h = x+radius, y+radius, width-d, height-d

            # 虚拟控件内部填充颜色
            kw = {'outline': NULL, 'fill': color_fill[0]}
            self.inside = [
                canvas.create_rectangle(
                    x, _y, x+width, y+height-radius, **kw),
                canvas.create_rectangle(
                    _x, y, x+width-radius, y+height, **kw),
                canvas.create_arc(
                    x, y, x+d, y+d, start=90, extent=100, **kw),
                canvas.create_arc(
                    x+_w, y, x+width, y+d, start=0, extent=100, **kw),
                canvas.create_arc(
                    x, y+_h, x+d, y+height, start=180, extent=100, **kw),
                canvas.create_arc(
                    x+_w, y+_h, x+width, y+height, start=270, extent=100, **kw)]

            # 虚拟控件外框
            kw = {'extent': 100, 'style': 'arc', 'outline': color_outline[0]}
            self.outside = [
                canvas.create_line(
                    _x, y, x+width-radius, y, fill=color_outline[0]),
                canvas.create_line(
                    _x, y+height, x+width-radius, y+height, fill=color_outline[0]),
                canvas.create_line(
                    x, _y, x, y+height-radius, fill=color_outline[0]),
                canvas.create_line(
                    x+width, _y, x+width, y+height-radius+1, fill=color_outline[0]),
                canvas.create_arc(
                    x, y, x+d, y+d, start=90, **kw),
                canvas.create_arc(
                    x+_w, y, x+width, y+d, start=0, **kw),
                canvas.create_arc(
                    x, y+_h, x+d, y+height, start=180, **kw),
                canvas.create_arc(
                    x+_w, y+_h, x+width, y+height, start=270, **kw)]
        else:
            # 虚拟控件的外框
            self.rect = canvas.create_rectangle(
                x, y, x+width, y+height,
                width=borderwidth,
                outline=color_outline[0],
                fill=color_fill[0])

        # 虚拟控件显示的文字
        self.text = canvas.create_text(
            x + (radius+2 if justify == 'left' else width-radius-3
                 if justify == 'right' else width / 2),
            y + height / 2,
            text=text,
            font=font,
            justify=justify,
            anchor='w' if justify == 'left' else 'e' if justify == 'right' else 'center',
            fill=color_text[0])

    def state(self: Self, mode: Literal['normal', 'touch', 'press', 'disabled'] | None = None) -> None:
        """
        mode 参数为 None 时仅更新控件，否则改变虚拟控件的外观
        `normal`: 正常状态
        `touch`: 鼠标触碰时的状态
        `press`: 鼠标按下时的状态
        `disabled`: 禁用状态
        """
        if mode:
            self._state = mode

        if self._state == 'normal':
            mode = 0
        elif self._state == 'touch':
            mode = 1
        elif self._state == 'press':
            mode = 2
        else:
            mode = 3

        self.master.itemconfigure(self.text, fill=self.color_text[mode])
        if isinstance(self, CanvasText):
            self.master.itemconfigure(self._text, fill=self.color_text[mode])

        if self.radius:
            # 修改色块
            for item in self.inside:
                self.master.itemconfigure(item, fill=self.color_fill[mode])

            # 修改线条
            for item in self.outside[:4]:
                self.master.itemconfigure(item, fill=self.color_outline[mode])
            for item in self.outside[4:]:
                self.master.itemconfigure(
                    item, outline=self.color_outline[mode])
        else:
            self.master.itemconfigure(
                self.rect, outline=self.color_outline[mode])
            if isinstance(self, ProcessBar):
                self.master.itemconfigure(self.bottom, fill=self.color_fill[0])
                self.master.itemconfigure(self.bar, fill=self.color_fill[1])
            else:
                self.master.itemconfigure(
                    self.rect, fill=self.color_fill[mode])

    def move(self: Self, dx: float, dy: float) -> None:
        """
        移动控件的位置
        `dx`: 横向移动长度（单位：像素）
        `dy`: 纵向移动长度
        """
        self.x1 += dx
        self.x2 += dx
        self.y1 += dy
        self.y2 += dy

        if self.radius:
            for item in self.inside+self.outside:
                self.master.move(item, dx, dy)
        else:
            self.master.move(self.rect, dx, dy)

        self.master.move(self.text, dx, dy)

        if isinstance(self, _TextWidget):
            self.master.move(self.cursor, dx, dy)
        if isinstance(self, CanvasText):
            self.master.move(self._text, dx, dy)
        if isinstance(self, ProcessBar):
            self.master.move(self.bar, dx, dy)

    def configure(self: Self, *args, **kw) -> str | tuple | None:
        """
        修改或查询原有参数的值，可供修改或查询的参数有
        1. 所有控件: `color_text`、`color_fill`、`color_outline`
        2. 非文本控件: `text`
        """
        if args:
            if args[0] == 'text':
                return self.value
            else:
                return getattr(self, args[0])

        if value := kw.get('text', None):
            self.value = value
        if text := kw.get('color_text', None):
            self.color_text = text
        if fill := kw.get('color_fill', None):
            self.color_fill = fill
        if outline := kw.get('color_outline', None):
            self.color_outline = outline

        if isinstance(self, CanvasLabel | CanvasButton | ProcessBar) and value:
            self.master.itemconfigure(self.text, text=value)

    def destroy(self: Self) -> None:
        """ 摧毁控件释放内存 """
        self.live = False
        self.master._widget.remove(self)

        if self.radius:
            for item in self.inside+self.outside:
                self.master.delete(item)
        else:
            self.master.delete(self.rect)

        if isinstance(self, _TextWidget):
            self.master.delete(self.cursor)
        if isinstance(self, CanvasText):
            self.master.delete(self._text)
        if isinstance(self, ProcessBar):
            self.master.delete(self.bar)

        self.master.delete(self.text)

    def set_live(self: Self, boolean: bool | None = None) -> bool | None:
        """ 设定或查询live值 """
        if boolean == None:
            return self.live
        else:
            self.live = boolean
            if boolean:
                self.state('normal')
            else:
                self.state('disabled')
                # TODO: 滚动条的状态设定


class CanvasLabel(_BaseWidget):
    """ 创建一个虚拟的标签控件，用于显示少量文本 """

    def __init__(
        self: Self,
        canvas: Canvas,
        x: int,
        y: int,
        width: int,
        height: int,
        radius: int = RADIUS,
        text: str = NULL,
        borderwidth: int = BORDERWIDTH,
        justify: str = tkinter.CENTER,
        font: tuple[str, int, str] = FONT,
        color_text: tuple[str, str, str] = COLOR_TEXT,
        color_fill: tuple[str, str, str] = COLOR_BUTTON_FILL,
        color_outline: tuple[str, str, str] = COLOR_BUTTON_OUTLINE
    ) -> None:
        _BaseWidget.__init__(self, canvas, x, y, width, height, radius, text, justify,
                             borderwidth, font, color_text, color_fill, color_outline)

    def touch(self: Self, event: tkinter.Event) -> bool:
        """ 触碰状态检测 """
        condition = self.x1 <= event.x <= self.x2 and self.y1 <= event.y <= self.y2
        self.state('touch' if condition else 'normal')
        return condition


class CanvasButton(_BaseWidget):
    """ 创建一个虚拟的按钮，并执行关联函数 """

    def __init__(
        self: Self,
        canvas: Canvas,
        x: int,
        y: int,
        width: int,
        height: int,
        radius: int = RADIUS,
        text: str = NULL,
        borderwidth: int = BORDERWIDTH,
        justify: str = tkinter.CENTER,
        font: tuple[str, int, str] = FONT,
        command=None,  # type: function | None
        color_text: tuple[str, str, str] = COLOR_TEXT,
        color_fill: tuple[str, str, str] = COLOR_BUTTON_FILL,
        color_outline: tuple[str, str, str] = COLOR_BUTTON_OUTLINE
    ) -> None:
        _BaseWidget.__init__(self, canvas, x, y, width, height, radius, text, justify,
                             borderwidth, font, color_text, color_fill, color_outline)
        self.command = command

    def execute(self: Self, event: tkinter.Event) -> bool:
        """ 执行关联函数 """
        condition = self.x1 <= event.x <= self.x2 and self.y1 <= event.y <= self.y2
        if condition and self.command:
            self.command()
        return condition

    def press(self: Self, event: tkinter.Event) -> None:
        """ 交互状态检测 """
        if self.x1 <= event.x <= self.x2 and self.y1 <= event.y <= self.y2:
            self.state('press')
        else:
            self.state('normal')

    def touch(self: Self, event: tkinter.Event) -> bool:
        """ 触碰状态检测 """
        condition = self.x1 <= event.x <= self.x2 and self.y1 <= event.y <= self.y2
        self.state('touch' if condition else 'normal')
        return condition


class _TextWidget(_BaseWidget):
    """ 内部类 """

    def __init__(
        self: Self,
        canvas: Canvas,
        x: int,
        y: int,
        width: int,
        height: int,
        radius: int,
        text: tuple[str] | str,
        limit: int,
        space: bool,
        justify: str,
        icursor: str,
        borderwidth: int,
        font: tuple[str, int, str],
        color_text: tuple[str, str, str],
        color_fill: tuple[str, str, str],
        color_outline: tuple[str, str, str]
    ) -> None:

        self.limit = limit
        self.space = space
        self.icursor = icursor

        # 表面显示值
        self.value_surface = NULL
        # 光标闪烁间隔
        self._cursor_time = 300
        # 光标闪烁标志
        self._cursor = False

        if type(text) == str:
            self.value_normal, self.value_touch = text, NULL
        else:
            self.value_normal, self.value_touch = text

        _BaseWidget.__init__(self, canvas, x, y, width, height, radius, NULL, justify,
                             borderwidth, font, color_text, color_fill, color_outline)

        # 鼠标光标（位置顺序不可乱动）
        self.cursor = canvas.create_text(0, 0, font=font, fill=color_text[2])

    def touch_on(self: Self) -> None:
        """ 鼠标悬停状态 """
        if self._state != 'press':
            self.state('touch')

            # 判断显示的值是否为第一默认值
            if self.master.itemcget(self.text, 'text') == self.value_normal:
                # 更新为第二默认值
                self.master.itemconfigure(self.text, text=self.value_touch)

    def touch_off(self: Self) -> None:
        """ 鼠标离开状态 """
        if self._state != 'press':
            self.state('normal')

            # 判断显示的值是否为第二默认值
            if self.master.itemcget(self.text, 'text') == self.value_touch:
                # 更新为第一默认值
                self.master.itemconfigure(self.text, text=self.value_normal)

    def press(self: Self, event: tkinter.Event) -> None:
        """ 交互状态检测 """
        if self.x1 <= event.x <= self.x2 and self.y1 <= event.y <= self.y2:
            if self._state != 'press':
                self.press_on()
        else:
            self.press_off()

    def touch(
        self,  # type: CanvasEntry | CanvasText
        event: tkinter.Event
    ) -> bool:
        """ 触碰状态检测 """
        condition = self.x1 <= event.x <= self.x2 and self.y1 <= event.y <= self.y2
        self.touch_on() if condition else self.touch_off()
        return condition

    def cursor_flash(self: Self) -> None:
        """ 鼠标光标闪烁 """
        if self._cursor_time >= 300:
            self._cursor_time, self._cursor = 0, not self._cursor
            if self._cursor:
                self.master.itemconfigure(self.cursor, text=self.icursor)
            else:
                self.master.itemconfigure(self.cursor, text=NULL)

        if self._state == 'press':
            self._cursor_time += 10
            self.master.after(10, self.cursor_flash)
        else:
            self._cursor_time, self._cursor = 300, False  # 恢复默认值
            self.master.itemconfigure(self.cursor, text=NULL)

    def cursor_update(self: Self, text: str = ' ') -> None:
        """ 鼠标光标更新 """
        self._cursor_time, self._cursor = 300, False  # 恢复默认值
        if isinstance(self, CanvasEntry):
            self.master.coords(self.cursor, self.master.bbox(
                self.text)[2], self.y1+self.height * self.master.rate_y / 2)
        elif isinstance(self, CanvasText):
            _pos = self.master.bbox(self._text)
            self.master.coords(self.cursor, _pos[2], _pos[1])
        self.master.itemconfigure(
            self.cursor, text=NULL if not text else self.icursor)

    def paste(self: Self) -> bool:
        """ 快捷键粘贴 """
        condition = self._state == 'press' and not getattr(self, 'show', None)
        if condition:
            self.append(self.master.clipboard_get())
        return condition

    def get(self: Self) -> str:
        """ 获取输入框的值 """
        return self.value

    def set(self: Self, value: str) -> None:
        """ 设置输入框的值 """
        self.value = self.value_surface = ''
        self.append(value)

    def append(self: Self, value: str) -> None:
        """ 添加输入框的值 """
        temp, self._state = self._state, 'press'
        (event := tkinter.Event()).keysym = None
        for char in value:
            event.char = char
            self.input(event)
        self._state = temp
        self.cursor_flash()


class CanvasEntry(_TextWidget):
    """ 创建一个虚拟的输入框控件，可输入单行少量字符，并获取这些字符 """

    def __init__(
        self: Self,
        canvas: Canvas,
        x: int,
        y: int,
        width: int,
        height: int,
        radius: int = RADIUS,
        text: tuple[str] | str = NULL,
        show: str | None = None,
        limit: int = LIMIT,
        space: bool = False,
        cursor: str = CURSOR,
        borderwidth: int = BORDERWIDTH,
        justify: str = tkinter.LEFT,
        font: tuple[str, int, str] = FONT,
        color_text: tuple[str, str, str] = COLOR_TEXT,
        color_fill: tuple[str, str, str] = COLOR_TEXT_FILL,
        color_outline: tuple[str, str, str] = COLOR_TEXT_OUTLINE
    ) -> None:
        _TextWidget.__init__(self, canvas, x, y, width, height, radius, text, limit, space, justify,
                             cursor, borderwidth, font, color_text, color_fill, color_outline)
        self.master.itemconfigure(self.text, text=self.value_normal)
        self.show = show

    def press_on(self: Self) -> None:
        """ 控件获得焦点 """
        self.state('press')
        self.master.itemconfigure(self.text, text=self.value_surface)
        self.cursor_update(NULL)
        self.cursor_flash()

    def press_off(self: Self) -> None:
        """ 控件失去焦点 """
        self.state('normal')

        if self.value == NULL:
            self.master.itemconfigure(self.text, text=self.value_normal)
        else:
            self.master.itemconfigure(self.text, text=self.value_surface)

    def input(self: Self, event: tkinter.Event) -> None:
        """ 文本输入 """
        if self._state == 'press':
            if event.keysym == 'BackSpace':
                # 按下退格键
                self.value = self.value[:-1]
            elif len(self.value) == self.limit:
                # 达到字数限制
                return True
            elif len(event.char):
                if not event.char.isprintable() or (event.char == ' ' and not self.space):
                    return True
                else:
                    # 按下普通按键
                    self.value += event.char
            else:
                return True

            # 更新表面显示值
            self.value_surface = len(
                self.value) * self.show if self.show else self.value

            # 更新显示
            self.master.itemconfigure(self.text, text=self.value_surface)
            self.update_text()
            self.cursor_update()
            return True

    def update_text(self: Self):
        """ 更新控件 """
        while True:
            pos = self.master.bbox(self.text)
            if pos[2] > self.x2-self.radius-2 or pos[0] < self.x1+self.radius+1:
                self.value_surface = self.value_surface[1:]
                self.master.itemconfigure(self.text, text=self.value_surface)
            else:
                break

        # BUG: 当窗口扩大再缩小时，可能出现过短情况


class CanvasText(_TextWidget):
    """ 创建一个透明的虚拟文本框，用于输入多行文本和显示多行文本（只读模式）"""

    def __init__(
        self: Self,
        canvas: Canvas,
        x: int,
        y: int,
        width: int,
        height: int,
        radius: int = RADIUS,
        text: tuple[str] | str = NULL,
        limit: int = LIMIT,
        space: bool = True,
        read: bool = False,
        cursor: bool = CURSOR,
        borderwidth: int = BORDERWIDTH,
        justify: str = tkinter.LEFT,
        font: tuple[str, int, str] = FONT,
        color_text: tuple[str, str, str] = COLOR_TEXT,
        color_fill: tuple[str, str, str] = COLOR_TEXT_FILL,
        color_outline: tuple[str, str, str] = COLOR_TEXT_OUTLINE
    ) -> None:
        _TextWidget.__init__(self, canvas, x, y, width, height, radius, text, limit, space, justify,
                             cursor, borderwidth, font, color_text, color_fill, color_outline)

        _x = x + (width-radius-3 if justify == 'right' else width /
                  2 if justify == 'center' else radius+2)
        _anchor = 'n' if justify == 'center' else 'ne' if justify == 'right' else 'nw'

        # 位置确定文本(位置不要乱动)
        self._text = canvas.create_text(_x, y+radius+2,
                                        justify=justify,
                                        anchor=_anchor,
                                        font=font,
                                        fill=color_text[0])

        # TODO: 滚动条待写

        # 只读模式
        self.read = read
        # # 修改多行文本靠左显示
        self.master.coords(self.text, _x, y+radius+2)
        self.master.itemconfigure(
            self.text, text=self.value_normal, anchor=_anchor)
        self.master.itemconfigure(self.cursor, anchor='n')

        # 行位置数
        self.position = [0, 0]

    def press_on(self: Self) -> None:
        """ 控件获得焦点 """
        if not self.read:
            self.state('press')
            *__, _ = [''] + self.value_surface.rsplit('\n', 1)
            self.master.itemconfigure(self.text, text=''.join(__))
            self.master.itemconfigure(self._text, text=_)
            self.cursor_update(NULL)
            self.cursor_flash()

    def press_off(self: Self) -> None:
        """ 控件失去焦点 """
        self.state('normal')

        if self.value == NULL:
            self.master.itemconfigure(self.text, text=self.value_normal)
        else:
            *__, _ = [''] + self.value_surface.rsplit('\n', 1)
            self.master.itemconfigure(self.text, text=''.join(__))
            self.master.itemconfigure(self._text, text=_)

    def input(self: Self, event: tkinter.Event) -> bool:
        """ 文本输入 """
        if self._state == 'press':
            if event.keysym == 'BackSpace':
                # 按下退格键
                self.input_backspace()
            elif len(self.value) == self.limit:
                # 达到字数限制
                return True
            elif event.keysym == 'Tab':
                # 按下Tab键
                self.append(' '*4)
            elif event.keysym == 'Return' or event.char == '\n':
                # 按下回车键
                self.input_return()
            elif event.char.isprintable() and event.char:
                # 按下其他普通的键
                _text = self.master.itemcget(self._text, 'text')
                self.master.itemconfigure(self._text, text=_text+event.char)
                _pos = self.master.bbox(self._text)

                if _pos[2] > self.x2-self.radius-2 or _pos[0] < self.x1+self.radius+1:
                    # 文本溢出啦
                    self.master.itemconfigure(self._text, text=_text)
                    self.input_return()
                    self.master.itemconfigure(self._text, text=event.char)

                self.value += event.char
            else:
                return True

            self.cursor_update()

            # 更新表面显示值
            text = self.master.itemcget(self.text, 'text')
            _text = self.master.itemcget(self._text, 'text')
            self.value_surface = text+'\n'+_text

            return True

    def input_return(self: Self) -> None:
        """ 回车键功能 """
        self.value += '\n'

        # 相关数据获取
        text = self.master.itemcget(self.text, 'text')
        _text = self.master.itemcget(self._text, 'text')
        _pos = self.master.bbox(self._text)

        self.master.itemconfigure(self._text, text='')

        if _pos[3]+_pos[3]-_pos[1] < self.y2-self.radius-2:
            # 还没填满文本框
            self.master.move(self._text, 0, _pos[3] - _pos[1])
            self.master.itemconfigure(
                self.text, text=text+bool(text)*'\n'+_text)
        else:
            # 文本框已经被填满了
            text = text.split('\n', 1)[-1]
            self.master.itemconfigure(self.text, text=text+'\n'+_text)

            self.position[0] += 1
            self.position[1] += 1

    def input_backspace(self: Self) -> None:
        """ 退格键功能 """
        if not self.value:
            # 没有内容，删个毛啊
            return

        _text = self.master.itemcget(self._text, 'text')
        self.value = self.value[:-1]

        if _text:
            # 正常地删除字符
            self.master.itemconfigure(self._text, text=_text[:-1])
        else:
            # 遇到换行符
            _ = self.value.rsplit('\n', 1)[-1]
            self.master.itemconfigure(self._text, text=_)

            if self.value == self.master.itemcget(self.text, 'text'):
                # 内容未超出框的大小
                _pos = self.master.bbox(self._text)
                self.master.move(self._text, 0, _pos[1] - _pos[3])
                __ = self.value.removesuffix(_)[:-('\n' in self.value)]
            else:
                # 内容已经超出框框的大小啦
                text = self.master.itemcget(self.text, 'text')
                __ = self.value.removesuffix(
                    text)[:-1].rsplit('\n', 1)[-1]+'\n'+text.removesuffix(_)[:-1]

                self.position[0] -= 1
                self.position[1] -= 1

            self.master.itemconfigure(self.text, text=__)

    def scroll(self: Self, event: tkinter.Event) -> None:
        """ 文本滚动 """
        # TODO: 滚动条关联的操作待写


class ProcessBar(_BaseWidget):
    """ 虚拟的进度条，可以直观的方式显示任务进度 """

    def __init__(
        self: Self,
        canvas: Canvas,
        x: int,
        y: int,
        width: int,
        height: int,
        borderwidth: int = BORDERWIDTH,
        justify: str = tkinter.CENTER,
        font: tuple[str, int, str] = FONT,
        color_text: tuple[str, str, str] = COLOR_TEXT,
        color_outline: tuple[str, str, str] = COLOR_TEXT_OUTLINE,
        color_bar: tuple[str, str] = COLOR_BAR
    ) -> None:
        self.bottom = canvas.create_rectangle(
            x, y, x+width, y+height, width=borderwidth, fill=color_bar[0])
        self.bar = canvas.create_rectangle(
            x, y, x, y+height, width=borderwidth, outline='', fill=color_bar[1])

        _BaseWidget.__init__(self, canvas, x, y, width, height, 0, '0.00%', justify,
                             borderwidth, font, color_text, COLOR_NONE, color_outline)

        self.color_fill = list(color_bar)

    def touch(self: Self, event: tkinter.Event) -> bool:
        """ 触碰状态检测 """
        condition = self.x1 <= event.x <= self.x2 and self.y1 <= event.y <= self.y2
        self.state('touch' if condition else 'normal')
        return condition

    def load(self: Self, percentage: float) -> None:
        """
        进度条加载，并更新外观
        `percentage`: 进度条的值，范围 0~1
        """
        percentage = 0 if percentage < 0 else 1 if percentage > 1 else percentage
        x2 = self.x1 + self.width * percentage * self.master.rate_x
        self.master.coords(self.bar, self.x1, self.y1, x2, self.y2)
        self.configure(text='%.2f%%' % (percentage * 100))


class PhotoImage(tkinter.PhotoImage):
    """ 生成图片并进行相应的一些处理（支持png和gif格式） """

    def __init__(
        self: Self,
        file: str | bytes | None = None,
        **kw
    ) -> None:
        """
        `file`: 图片文件的路径
        `**kw`: 与 tkinter.PhotoImage 的参数相同
        """
        self.file = file

        if file.rsplit('.', 1)[-1] == 'gif':
            self.frames: list[tkinter.PhotoImage] = []
        elif file.rsplit('.', 1)[-1] == 'png':
            return tkinter.PhotoImage.__init__(self, file=file, **kw)
        else:
            raise

    def parse(self: Self, start: int = 0) -> Generator[int, None, None]:
        """
        解析动图，返回一个生成器
        `start`: 动图解析的起始索引（帧数-1）
        """
        try:
            while True:
                self.frames.append(tkinter.PhotoImage(
                    file=self.file, format='gif -index %d' % start))
                start += 1
                yield start
        except tkinter.TclError:
            return

    def play(
        self: Self,
        canvas: Canvas,
        itemid,  # type: tkinter._CanvasItemId
        interval: int,
        _ind: int = 0
    ) -> None:
        """
        播放动图，canvas.lock为False会暂停
        `canvas`: 播放动画的画布
        `itemid`: 播放动画的 _CanvasItemId（就是 create_text 的返回值）
        `interval`: 每帧动画的间隔时间
        """
        if _ind == len(self.frames):
            _ind = 0
        canvas.itemconfigure(itemid, image=self.frames[_ind])
        args = canvas, itemid, interval, _ind+canvas.lock
        canvas.after(interval, self.play, *args)

    def zoom(self: Self, rate_x: float, rate_y: float, precision: float | None = None) -> tkinter.PhotoImage:
        """
        缩放图片
        `rate_x`: 横向缩放倍率
        `rate_y`: 纵向缩放倍率
        `precision`: 精度到小数点后的位数，越大运算就越慢(默认值代表绝对精确)
        """
        if precision:
            key = round(10**precision)  # TODO: 需要算法以提高精度和速度（浮点数->小的近似分数）
            image = tkinter.PhotoImage.zoom(self, key, key)
            image = image.subsample(round(key / rate_x), round(key / rate_y))
        else:
            width, height = int(self.width()*rate_x), int(self.height()*rate_y)
            image = tkinter.PhotoImage(width=width, height=height)
            for x in range(width):
                for y in range(height):
                    image.put('#%02X%02X%02X' % self.get(
                        int(x/rate_x), int(y/rate_y)), (x, y))

        return image


class Singleton(object):
    """ 单例模式类，用于继承 """

    _instance_ = None

    def __new__(cls: Type[Self], *args, **kw) -> Self:
        if not cls._instance_:
            cls._instance_ = object.__new__(cls)
        return cls._instance_


def move_widget(
    master: Tk | Canvas | tkinter.Misc | tkinter.BaseWidget,
    widget: Canvas | _BaseWidget | tkinter.BaseWidget | int,
    dx: int,
    dy: int,
    times: float,
    mode: Literal['smooth', 'rebound', 'flat'] | tuple,
    _x: int = 0,
    _y: int = 0,
    _ind: int = 0
) -> None:
    """
    ### 控件移动函数
    以特定方式移动由 Place 布局的某个控件或某些控件的集合或图像
    #### 参数说明
    `master`: 控件所在的父控件
    `widget`: 要移动位置的控件
    `dx`: 横向移动的距离（单位：像素）
    `dy`: 纵向移动的距离
    `times`: 移动总时长（单位：秒）
    `mode`: 移动速度模式，为以下三种，或者为 (函数, 起始值, 终止值) 的形式，或者为一个长度等于 20 的，总和为 100 的元组
    1. `smooth`: 速度先慢后快再慢 (Sin, 0, π)
    2. `rebound`: 和 smooth 一样，但是最后会回弹一下 (Cos, 0, 0.6π)
    3. `flat`: 匀速平移
    """
    # 速度变化模式
    if isinstance(mode, tuple) and len(mode) >= 20:  # 记忆值
        v = mode
    elif mode == 'smooth':  # 流畅模式
        v = 0, 1, 3, 4, 5, 6, 7, 8, 8, 8, 8, 8, 8, 7, 6, 5, 4, 3, 1, 0
    elif mode == 'rebound':  # 回弹模式
        v = 11, 11, 10, 10, 10, 9, 9, 8, 7, 6, 6, 5, 4, 3, 1, 0, -1, -2, -3, -4
    elif mode == 'flat':  # 平滑模式
        v = (5,) * 20
    else:  # 函数模式
        f, start, end = mode
        end = (end-start) / 19
        v = tuple(f(start+end*_) for _ in range(20))
        key = 100 / sum(v)
        v = tuple(key*_ for _ in v)

    # 总计实际应该移动的百分比
    proportion = sum(v[:_ind+1]) / 100

    # 计算本次移动量
    x = round(proportion * dx - _x)
    y = round(proportion * dy - _y)

    if isinstance(master, tkinter.Misc) and isinstance(widget, tkinter.BaseWidget):
        # 父控件：tkinter控件
        # 子控件：tkinter控件
        origin_x = int(widget.place_info()['x'])
        origin_y = int(widget.place_info()['y'])
        widget.place(x=origin_x+x, y=origin_y+y)
    elif isinstance(master, Canvas) and isinstance(widget, _BaseWidget):
        # 父控件：Canvas
        # 子控件：_BaseWidget
        widget.move(x, y)
    else:
        # 父控件：Canvas | tkinter.Canvas
        # 子控件：tkinter._CanvasItemId
        master.move(widget, x, y)

    if _ind != 19:
        # 迭代函数
        args = master, widget, dx, dy, times, v, _x+x, _y+y, _ind+1
        master.after(round(times*50), move_widget, *args)


def correct_text(
    length: int,
    string: str,
    position: Literal['left', 'center', 'right'] = 'center'
) -> str:
    """
    ### 文本控制函数
    可将目标字符串改为目标长度并居中对齐，ASCII码字符算1个长度，中文及其他字符算2个
    #### 参数说明
    `length`: 目标长度
    `string`: 要修改的字符串
    `position`: 文本处于该长度范围的位置，可选三个值
    1. `left`: 文本靠左
    2. `center`: 文本居中
    3. `right`: 文本靠右
    """
    length -= sum(1 + (ord(i) > 256) for i in string)  # 计算空格总个数
    if position == 'left':  # 靠左
        return ' '*length+string
    elif position == 'right':  # 靠右
        return string+length*' '
    else:  # 居中
        length, key = divmod(length, 2)
        return ' '*length+string+(length+key)*' '


def change_color(
    color: Iterable[str] | str,
    proportion: float = 1
) -> str:
    """
    ### 颜色处理函数
    按一定比例给出已有RGB颜色字符串的渐变RGB颜色字符串，或颜色的对比色
    #### 参数说明
    `color`: 颜色元组或列表 (初始颜色, 目标颜色)，或者一个颜色字符串
    `proportion`: 渐变比例（浮点数，范围为0~1）
    """
    if isinstance(color, str):
        color = color, None

    # 判断颜色字符串格式（#FFF或者#FFFFFF格式）
    key = 256 if len(color[0]) == 7 else 16

    # 解析初始颜色的RGB
    _ = int(color[0][1:], 16)
    _, B = divmod(_, key)
    R, G = divmod(_, key)

    # 解析目标颜色的RGB
    if color[1]:
        _ = int(color[1][1:], 16)
        _, _B = divmod(_, key)
        _R, _G = divmod(_, key)
    else:
        _R, _G, _B = 255 - R, 255 - G, 255 - B

    # 根据比率计算返回值
    RGB = R + round((_R - R) * proportion)
    RGB *= key
    RGB += G + round((_G - G) * proportion)
    RGB *= key
    RGB += B + round((_B - B) * proportion)

    # 以对应格式返回结果
    return '#%0*X' % (6 if key == 256 else 3, RGB)


def test() -> None:
    """ 测试函数 """
    from random import randint
    from tkinter.messagebox import askyesno

    def shutdown():
        """ 关闭窗口 """
        if askyesno('提示', '是否退出测试程序?'):
            root.destroy()

    def change_bg(ind=0, color=[None, '#F1F1F1']):
        """ 颜色变幻 """
        if not ind:
            color[0], color[1] = color[1], '#%06X' % randint(0, 1 << 24)
        color = change_color(color, ind)
        _color = change_color(color)
        canvas_doc.configure(bg=color)
        canvas_doc.itemconfigure(doc, fill=_color)
        for widget in canvas_main._widget:
            widget.color_fill[0], widget.color_text[0] = color, _color
            widget.state()
        root.after(20, change_bg, 0 if ind >= 1 else ind+0.01)

    def draw(ind=0):
        """ 绘制球体 """
        canvas_graph.create_oval(
            (300-ind/3)*canvas_graph.rate_x, (100-ind/3)*canvas_graph.rate_y,
            (400+ind)*canvas_graph.rate_x, (200+ind)*canvas_graph.rate_y,
            outline=change_color(('#FFFFFF', '#000000'), ind/100),
            width=2.5, fill=NULL if ind else '#FFF')
        if ind < 100:
            root.after(30, draw, ind+1)

    def processbar(ind=0):
        """ 进度条更新 """
        bar.load(ind)
        root.after(1, processbar, ind+0.0001)

    root = Tk('Test', '960x540', alpha=0.9, shutdown=shutdown)
    (canvas_main := Canvas(root, 960, 540)).place(x=0, y=0)
    (canvas_doc := Canvas(root, 960, 540)).place(x=-960, y=0)
    (canvas_graph := Canvas(root, 960, 540)).place(x=960, y=0)

    CanvasButton(
        canvas_main, 10, 500, 120, 30, 0, '模块文档',
        command=lambda: (move_widget(root, canvas_main, 960*canvas_main.rate_x, 0, 0.3, 'rebound'),
                         move_widget(root, canvas_doc, 960*canvas_doc.rate_x, 0, 0.3, 'rebound')))
    CanvasButton(
        canvas_main, 830, 500, 120, 30, 0, '图像测试',
        command=lambda: (move_widget(root, canvas_main, -960*canvas_main.rate_x, 0, 0.3, 'rebound'),
                         move_widget(root, canvas_graph, -960*canvas_graph.rate_x, 0, 0.3, 'rebound')))
    CanvasButton(
        canvas_doc, 830, 500, 120, 30, 0, '返回主页',
        command=lambda: (move_widget(root, canvas_main, -960*canvas_main.rate_x, 0, 0.3, 'rebound'),
                         move_widget(root, canvas_doc, -960*canvas_doc.rate_x, 0, 0.3, 'rebound')))
    CanvasButton(
        canvas_graph, 10, 500, 120, 30, 0, '返回主页',
        command=lambda: (move_widget(root, canvas_main, 960*canvas_main.rate_x, 0, 0.3, 'rebound'),
                         move_widget(root, canvas_graph, 960*canvas_graph.rate_x, 0, 0.3, 'rebound')))

    try:
        image = PhotoImage('tkinter.png')
        canvas_graph.create_image(830, 130, image=image)
    except tkinter.TclError:
        print('\033[31m啊哦！你没有示例图片喏……\033[0m')

    CanvasText(canvas_main, 10, 10, 465, 200, 10,
               ('居中圆角文本框', '竖线光标'), justify='center')
    CanvasText(canvas_main, 485, 10, 465, 200, 0,
               ('靠右方角文本框', '下划线光标'), cursor=' _')
    CanvasEntry(canvas_main, 10, 220, 200, 25, 5,
                ('居中圆角输入框', '点击输入'), justify='center')
    CanvasEntry(canvas_main, 750, 220, 200, 25, 0,
                ('靠右方角输入框', '点击输入'), '•')
    CanvasButton(
        canvas_main, 10, 250, 120, 25, 5, '圆角按钮',
        command=lambda: move_widget(canvas_main, label_1, 0, -120 * canvas_main.rate_y, 0.25, 'rebound'))
    CanvasButton(
        canvas_main, 830, 250, 120, 25, 0, '方角按钮',
        command=lambda: move_widget(canvas_main, label_2, 0, -120 * canvas_main.rate_y, 0.25, 'smooth'))

    bar = ProcessBar(canvas_main, 220, 220, 520, 25)
    load = CanvasButton(canvas_main, 420, 250, 120, 25, 0, '加载进度',
                        command=lambda: (processbar(), load.set_live(False)))

    doc = canvas_doc.create_text(
        15, 270, text=__doc__, font=('楷体', 12), anchor='w')

    label_1 = CanvasLabel(canvas_main, 225, 550, 250,
                          100, 10, '圆角标签\n移动模式:rebound')
    label_2 = CanvasLabel(canvas_main, 485, 550, 250,
                          100, 0, '方角标签\n移动模式:smooth')
    button_1 = CanvasButton(canvas_doc, 830, 10, 120, 30, 0, '颜色变幻',
                            command=lambda: (button_1.set_live(False), change_bg()))
    button_2 = CanvasButton(canvas_graph, 10, 10, 120, 30, 0, '绘制图形',
                            command=lambda: (button_2.set_live(False), draw()))

    root.mainloop()


if __name__ == '__main__':
    test()
