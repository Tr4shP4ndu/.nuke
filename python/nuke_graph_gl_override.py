# Copyright (C) CC-BY 4.0 2024 Alex Telford
# http://minimaleffort.tech
# This work is licensed under the Creative Commons Attribution 4.0 International License.
# To view a copy of this license, visit http://creativecommons.org/licenses/by/4.0/ or send a letter to Creative Commons,
# PO Box 1866, Mountain View, CA 94042, USA.
# Distributed without any warranty or liability, use at your own risk

# This script is something I made in a few hours, it is untested and is unsuitable for production use.
# Please do not judge me on this code...
# While I do not have the intention to develop this further, if you choose to, here are some notes.

# TODO:
# Pull the logic out of the UI, it's too intertangled
# the QGLWidget should not have a hard reference, it's still owned by Nuke
# Fix selecting both editor nodes and nuke nodes, currently finicky
# Allow deleting of nodes/connections
# Currently only one plug per node is supported, no reason not to support groups of plugs
# Plugs and connections are janky AF, this needs to be optimized away from the UI code
# QSettings should be in one place
# Add more brush types (circle, line, etc) Currently it's just a brush
# Add more node types, such as images, docs, etc
# There is a memory leak due to object ownership in Qt, probably sidebar

# Also thanks to Erwan for his insights into mapping the nuke scene transforms
# https://erwanleroy.com/nuke-node-graph-utilities-using-qt-pyside2/

from PySide2 import QtGui, QtWidgets, QtCore, QtSvg, QtOpenGL, QtTest
import nuke
from enum import IntFlag, auto
from typing import List

# This is just here so I can re-run this script while making changes
try:
    graph.setParent(None)
    graph.close()
except:
    pass

# https://fonts.google.com/icons?selected=Material%20Symbols%20Outlined%3Abrush%3AFILL%400%3Bwght%40400%3BGRAD%400%3Bopsz%4024
BRUSH_ICON = "E:/projects/icons/brush.svg"
# https://fonts.google.com/icons?selected=Material%20Symbols%20Outlined%3Aadd_box%3AFILL%400%3Bwght%40400%3BGRAD%400%3Bopsz%4024
ADD_ICON = "E:/projects/icons/add_square.svg"


class KnobTypes(IntFlag):
    """Collection of knob types for doing connection checking
    """
    NoType = auto()
    Unsupported = auto()
    String = auto()
    File = auto()
    Int = auto()
    Enumeration = auto()
    Bool = auto()
    Boolean = Bool
    Double = auto()
    Float = auto()
    Array = auto()
    # Write_File = auto()
    # MultiInt = auto()
    # Bitmask = auto()
    # MultiFloat = auto()
    # ChannelSet = auto()
    # ChannelMask = auto()
    # Input_ChannelSet = auto()
    # Input_ChannelMask = auto()
    # Channel = auto()
    # Input_Channel = auto()
    # XY = auto()
    # XYZ = auto()
    # XYWH = auto()
    # BBox = auto()
    # Format = auto()
    # Color = auto()
    # AColor = auto()
    # Transform2d = auto()
    # MultiLine_String = auto()
    # Axis = auto()
    # UV = auto()
    # Box3 = auto()
    # Too many... do this later
    StringTypes = String|File
    IntTypes = Int|Array|Bool
    FloatTypes = Float|Double
    NumericTypes = IntTypes|FloatTypes|Bool
    EnumTypes = Enumeration

    @classmethod
    def from_knob(cls, knob:nuke.Knob)->"KnobTypes":
        """Determines the knob type from the knob
        Returns Unsupported if that type is not currently supported

        Args:
            knob (nuke.Knob): Input knob

        Returns:
            KnobTypes
        """
        name = knob.Class()
        if name.endswith("_Knob"):
            name = name[:-5]
        if hasattr(cls, name):
            return getattr(cls, name)
        return cls.Unsupported


def get_knob_options(knob:nuke.Knob)->List[str]:
    """ Gets a list of enum options from a knob if supported
    
    Args:
        knob (nuke.Knob)
    
    Returns:
        List[str]
    """
    if KnobTypes.from_knob(knob) & KnobTypes.EnumTypes:
        return knob.values()
    return []


def get_knob_range(knob:nuke.Knob):
    """ Gets the min/max range from a knob if supported
    
    Args:
        knob (nuke.Knob)
    
    Returns:
        List[int|float]
    """
    if KnobTypes.from_knob(knob) & KnobTypes.NumericTypes:
        return [knob.minimum(), knob.maximum()]
    return [0, 0]


def set_knob_value(knob:nuke.Knob, value)->bool:
    """Sets the knob value based on it's type

    Args:
        knob (nuke.Knob): Knob to set
        value (varied): value to set

    Returns:
        bool: success
    """
    knob_type = KnobTypes.from_knob(knob)
    if knob_type == KnobTypes.Unsupported:
        return False

    if knob_type & KnobTypes.StringTypes:
        knob.setValue(str(value))
    
    elif knob_type & KnobTypes.Enumeration:
        options = get_knob_options(knob)
        if not options:
            return False
        if isinstance(value, str):
            if value in options:
                knob.setValue(value)
            else:
                return False
        
        else:
            # in case using slider, this is not ideal...
            value = int(float(value))
            if value < 0 or value >= len(options):
                return False
            knob.setValue(options[value])
        return True
    
    elif knob_type & KnobTypes.Bool:
        knob.setValue(bool(round(float(value))))
    
    elif knob_type & KnobTypes.IntTypes:
        knob.setValue(int(round(value)))
    
    elif knob_type & KnobTypes.FloatTypes:
        knob.setValue(float(value))
    
    else:
        return False
    return True

def hex_to_qcolor(hex_color:int)->QtGui.QColor:
    """Converts the color from nuke to a QColor

    Args:
        hex_color (int): Nuke color

    Returns:
        QtGui.QColor: Color
    """
    red = (hex_color >> 24) & 0xFF
    green = (hex_color >> 16) & 0xFF
    blue = (hex_color >> 8) & 0xFF
    alpha = hex_color & 0xFF
    return QtGui.QColor(red, green, blue, alpha)


def node_rect(node:nuke.Node)->QtCore.QPointF:
    """Returns the scene rect of a node

    Args:
        node (nuke.Node): node

    Returns:
        QtCore.QPointF: visual rect
    """
    # I believe screenWidth should be multiplied by nuke.zoom?
    return QtCore.QRectF(node.xpos(), node.ypos(), node.screenWidth(), node.screenHeight())


def node_at(pos:QtCore.QPointF)->nuke.Node|None:
    """Gets a node at the given position

    Args:
        pos (QtCore.QPointF): position

    Returns:
        nuke.Node|None: node or None
    """
    for node in nuke.allNodes():
        if node_rect(node).contains(pos):
            return node
    return None


class Button(QtWidgets.QPushButton):
    """A Simple button with rounded edges and an optional icon

    Args:
        path(str): path to svg icon, optional
        color(str|QColor): Color of icon, optional
    """
    def __init__(self, path:str|None=None, color:str|QtGui.QColor="#555555"):
        super(Button, self).__init__()
        self._path_render:QtSvg.QSvgRenderer = QtSvg.QSvgRenderer(path) if path else None
        self.color = QtGui.QColor(color or "#555555")
        self.setFixedSize(QtCore.QSize(24, 24))
    
    def paintEvent(self, event:QtGui.QPaintEvent):
        painter = QtGui.QPainter(self)
        painter.setPen(QtGui.QColor("#000000"))
        
        painter.setBrush(self.color)
        painter.drawRoundedRect(event.rect().adjusted(1, 1, -1, -1), 8, 8)
        
        if self._path_render:
            self._path_render.render(painter, event.rect().adjusted(4, 4, -4, -4))
            
            

class SideBar(QtWidgets.QWidget):
    """A Simple sidebar

    Args:
        parent(QWidget): optional parent
    
    Properties:
        color(QColor)
        width(int)
        on_top(bool)
    """
    def __init__(self, parent:QtWidgets.QWidget=None):
        super(SideBar, self).__init__(parent)
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        brush = Button(BRUSH_ICON)
        layout.addWidget(brush)
        self._color_button = Button(color="#FF0000")
        self.setAutoFillBackground(True)
        layout.addWidget(self._color_button)
        self._slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self._slider.setRange(1, 20)
        layout.addWidget(self._slider)
        self._on_top_cb = QtWidgets.QCheckBox("Over")
        layout.addWidget(self._on_top_cb)
        layout.addStretch(1)
        self._color_button.clicked.connect(self._choose_color)
    
    def paintEvent(self, event:QtGui.QPaintEvent):
        painter = QtGui.QPainter(self)
        hex_color = nuke.toNode('preferences').knob("DAGBackColor").value()
        color = hex_to_qcolor(hex_color)
        painter.setPen(QtCore.Qt.black)
        painter.setBrush(color)
        painter.drawRect(event.rect())
    
    @QtCore.Slot()
    def _choose_color(self):
        color = QtWidgets.QColorDialog.getColor(self.color, None, "Select a Color")
        if not color.isValid():
            return
        self.color = color
    
    @QtCore.Slot(QtGui.QColor)
    def set_color(self, color:QtGui.QColor):
        self._color_button.color = color
        self._color_button.update()
    
    def get_color(self)->QtGui.QColor:
        return self._color_button.color
    
    color = QtCore.Property(QtGui.QColor, get_color, set_color, stored=False)
    
    @QtCore.Slot(int)
    def set_width(self, width:int):
        self._slider.setValue(width)
    
    def get_width(self)->int:
        return self._slider.value()
    
    width = QtCore.Property(int, get_width, set_width, stored=False)
    
    @QtCore.Slot(bool)
    def set_on_top(self, on_top:bool):
        self._on_top_cb.setChecked(bool(on_top))
    
    def get_on_top(self)->bool:
        return self._on_top_cb.isChecked()
    
    on_top = QtCore.Property(bool, get_on_top, set_on_top, stored=False)
        

class Primitive(object):
    """Stores the path and it's options
    """
    path:QtGui.QPainterPath|None = None
    color:QtGui.QColor|None = None
    width:int = 1



class Plug(QtWidgets.QGraphicsItem):
    """This is the plug object, it's too intertangled with the scene but works for a demo

    Args:
        parent (QGraphicsItem): parent item
    """
    def __init__(self, parent:QtWidgets.QGraphicsItem=None):
        super().__init__(parent)
        self._size = 10
        self.type = KnobTypes.Unsupported
    
    def boundingRect(self)->QtCore.QRectF:
        return QtCore.QRectF(0, 0, self._size, self._size)
    
    def paint(self, painter:QtGui.QPainter, option:QtWidgets.QStyleOptionGraphicsItem, widget:QtWidgets.QWidget):
        painter.setPen(QtCore.Qt.black)
        painter.setBrush(QtGui.QColor("#CCCCCC"))
        painter.drawEllipse(self.boundingRect())
    
    def mousePressEvent(self, event:QtWidgets.QGraphicsSceneMouseEvent):
        if self.scene():
            self.scene().beginConnectionDrag(self)
        event.accept()
    
    def connect(self, knob:nuke.Knob):
        """ Connect to a plug and return the connection struct
        
        Args:
            knob(nuke.Knob)
        
        Returns:
            Connection
        """
        connection = Connection(self, knob)
        self.parentItem().init_from(knob)  # Objects should not know about their parents...
        return connection
        
        

class InputBase(QtWidgets.QGraphicsItem):
    """ Base class for input items
    
    Args:
        title(str)
        color(QColor)
        parent(QGraphicsItem)
    """
    default_name = "Input"  # This is the default display name for the node
    menu_label = "Unknown"  # This is what shows in the sidebar menu

    def __init__(self, title:str=None, color:QtGui.QColor=None, parent:QtWidgets.QGraphicsItem=None):
        super().__init__(parent)
        self.setFlags(self.ItemIsMovable|self.ItemIsSelectable)
        self._color = QtGui.QColor(color or "#CCCCCC")
        self._margin = 2
        self._title_item = QtWidgets.QGraphicsTextItem(title or self.default_name, parent=self)
        self._title_item.setPos(self._margin, self._margin)
        self._title_item.setDefaultTextColor(QtCore.Qt.black)
        widget = QtWidgets.QGraphicsProxyWidget(self)
        palette = QtGui.QPalette()
        palette.setBrush(QtGui.QPalette.Background, QtCore.Qt.transparent)
        widget.setPalette(palette)
        widget.setAutoFillBackground(False)
        self._editor = self._create_widget()
        self._editor.setEnabled(False)
        widget.setWidget(self._editor)
        widget.setPos(self._margin, self._title_item.boundingRect().bottom()+5)
        self._widget_item = widget
        
        self._dot = Plug(self)
        self._dot.type = self.type()
        bounds = self.boundingRect()
        self._dot.setPos(bounds.right()-5, bounds.bottom()-15)
    
    def init_from(self, knob:nuke.Knob):
        """Initializes from a knob on it's first connection

        Args:
            knob (nuke.Knob): knob to initialize from
        """
        if self._title_item.toPlainText() == self.default_name and knob.label():
            self._title_item.setPlainText(knob.label())
        
        if not self._editor.isEnabled():
            self._init_from_knob(self._editor, knob)
            self._editor.setEnabled(True)
    
    def _init_from_knob(self, editor:QtWidgets.QWidget, knob:nuke.Knob):
        """ Override this to initialize from a knob
        
        Args:
            editor(QWidget): The internal editor widget
            knob(nuke.Knob): knob to initialize from
        """
        return
    
    def type(self)->KnobTypes:
        """The supported knob types for a connection
        This should really be on the plug, not the node...

        Returns:
            KnobTypes: types
        """
        return KnobTypes.NoType
    
    def title(self)->str:
        """Title text

        Returns:
            str: title
        """
        return self._title_item.toPlainText()
    
    def set_title(self, title:str):
        """Set the title

        Args:
            title (str): title
        """
        self._title_item.setPlainText(title)
    
    def boundingRect(self)->QtCore.QRectF:
        bounds = self.mapRectFromItem(self._widget_item, self._widget_item.boundingRect())
        bounds = bounds.united(self.mapRectFromItem(self._title_item, self._title_item.boundingRect()))
        return QtCore.QRectF(
            QtCore.QPoint(0, 0),
            QtCore.QPoint(bounds.right() + self._margin,
                          bounds.bottom() + self._margin)
        )
    
    def _create_widget(self)->QtWidgets.QWidget:
        """Reimplement to create the editor widget
        """
        raise NotImplementedError()
    
    def _set_value(self, editor:QtWidgets.QWidget, value):
        """Reimplement to set the editor value
        """
        raise NotImplementedError()
    
    def _value(self, editor:QtWidgets.QWidget):
        """Reimplement to get the editor value
        """
        raise NotImplementedError()
    
    def _update_scene(self):
        """Notifies the scene that the value of this widget has been changed
        """
        if self.scene():
            self.scene().value_changed(self._dot, self.value())
    
    def value(self):
        """Current value

        Returns:
            varied: value
        """
        return self._value(self._editor)
    
    @QtCore.Slot("QVariant")
    def set_value(self, value):
        """Sets the value

        Args:
            value (varied): value
        """
        self._set_value(self._editor, value)
    
    def paint(self, painter:QtGui.QPainter, option:QtWidgets.QStyleOptionGraphicsItem, widget:QtWidgets.QWidget):
        painter.setBrush(self._color)
        pen = QtGui.QPen(QtGui.QColor(0, 0, 0))
        pen.setWidth(0.2)
        painter.setPen(pen)
        painter.drawRect(option.rect)
        if self.isSelected():
            pen.setColor("#0ac871")
            painter.setPen(pen)
            painter.setBrush(QtGui.QColor("#FCBA63"))
            painter.drawRect(option.rect.adjusted(2, 2, -2, -2))
        
        painter.setPen(QtCore.Qt.NoPen)
        gradient = QtGui.QLinearGradient(option.rect.topLeft(), option.rect.bottomLeft())
        gradient.setColorAt(0.0, QtCore.Qt.transparent)
        gradient.setColorAt(1.0, QtGui.QColor(0, 0, 0, 100))
        painter.fillRect(option.rect, gradient)
        
        
class SliderInput(InputBase):
    """Node with a slider
    
    Args:
        title(str)
        min(int|float)
        max(int|float)
        color(QColor)
        parent(QGraphicsItem)
    """
    default_name = "Slider"
    menu_label = "Slider"
    def __init__(self, title:str=None, min:int|float=0, max:int|float=100, color:QtGui.QColor=None, parent:QtWidgets.QGraphicsItem=None):
        self._min = min
        self._max = max
        super().__init__(title, color, parent)
    
    def type(self)->KnobTypes:
        # Ignore bools
        return KnobTypes.Int|KnobTypes.Array|KnobTypes.Float|KnobTypes.Double
    
    def _init_from_knob(self, editor:QtWidgets.QWidget, knob:nuke.Knob):
        self.set_range(*get_knob_range(knob))
        self.set_value(knob.value())
        return
    
    def _create_widget(self)->QtWidgets.QWidget:
        slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        slider.setRange(0, 1000)
        slider.setFixedWidth(100)
        slider.valueChanged.connect(self._update_scene)
        return slider
    
    def set_range(self, min:float, max:float):
        """Sets the range of the slider

        Args:
            min (float): min value
            max (float): max value
        """
        value = self.value()
        self._min = min
        self._max = max
        self.set_value(value)
    
    def _set_value(self, editor:QtWidgets.QWidget, value:float):
        mapped = (value-self._min)/float(self._max-self._min) * 1000
        editor.setValue(int(round(mapped)))
    
    def _value(self, editor:QtWidgets.QWidget)->float:
        value = editor.value()
        mapped = float(value)/1000 * (self._max-self._min) + self._min
        return mapped
        
class StringInput(InputBase):
    """Node with a slider
    
    Args:
        title(str)
        color(QColor)
        parent(QGraphicsItem)
    """
    default_name = "String"
    menu_label = "Text Field"
    def __init__(self, title:str=None, color:QtGui.QColor=None, parent:QtWidgets.QGraphicsItem=None):
        super().__init__(title, color, parent)
    
    def type(self)->KnobTypes:
        return KnobTypes.StringTypes
    
    def _init_from_knob(self, editor:QtWidgets.QWidget, knob:nuke.Knob):
        self.set_value(knob.value())
        return
    
    def _create_widget(self)->QtWidgets.QWidget:
        editor = QtWidgets.QLineEdit()
        editor.setFixedWidth(100)
        editor.setPlaceholderText("text")
        editor.textChanged.connect(self._update_scene)
        return editor
    
    def _set_value(self, editor:QtWidgets.QWidget, value:str):
        editor.setText(value)
    
    def _value(self, editor:QtWidgets.QWidget)->str:
        return editor.text()
        
class IntInput(InputBase):
    """Node with a slider
    
    Args:
        title(str)
        min(int)
        max(int)
        color(QColor)
        parent(QGraphicsItem)
    """
    default_name = "Int"
    menu_label = "Int Field"
    def __init__(self, title:str=None, min:int=0, max:int=100, color:QtGui.QColor=None, parent:QtWidgets.QGraphicsItem=None):
        self._min = min
        self._max = max
        super().__init__(title, color, parent)
    
    def type(self)->KnobTypes:
        return KnobTypes.IntTypes
    
    def _create_widget(self)->QtWidgets.QWidget:
        editor = QtWidgets.QLineEdit("0")
        editor.setFixedWidth(100)
        validator = QtGui.QIntValidator(editor)
        validator.setRange(self._min, self._max)
        editor.setValidator(validator)
        editor.textChanged.connect(self._update_scene)
        return editor
    
    def _init_from_knob(self, editor:QtWidgets.QWidget, knob:nuke.Knob):
        self.set_range(*get_knob_range(knob))
        self.set_value(knob.value())
        return
    
    def set_range(self, min:int, max:int):
        """Sets the range of the editor

        Args:
            min (int): min value
            max (int): max value
        """
        self._editor.validator().setRange(min, max)
    
    def _set_value(self, editor:QtWidgets.QWidget, value:int):
        editor.setText(str(int(round(float(value)))))
    
    def _value(self, editor:QtWidgets.QWidget)->int:
        if not editor.text():
            return 0
        return int(round(float(editor.text())))
        
class FloatInput(InputBase):
    """Node with a slider
    
    Args:
        title(str)
        min(float)
        max(float)
        color(QColor)
        parent(QGraphicsItem)
    """
    default_name = "Float"
    menu_label = "Float Field"
    def __init__(self, title:str=None, min:float=0, max:float=100, color:QtGui.QColor=None, parent:QtWidgets.QGraphicsItem=None):
        self._min = min
        self._max = max
        super().__init__(title, color, parent)
    
    def type(self)->KnobTypes:
        return KnobTypes.FloatTypes
    
    def _init_from_knob(self, editor:QtWidgets.QWidget, knob:nuke.Knob):
        self.set_range(*get_knob_range(knob))
        self.set_value(knob.value())
        return
    
    def _create_widget(self)->QtWidgets.QWidget:
        editor = QtWidgets.QLineEdit("0.0")
        editor.setFixedWidth(100)
        validator = QtGui.QDoubleValidator(self._min, self._max, 3, editor)
        validator.setNotation(QtGui.QDoubleValidator.StandardNotation)
        editor.setValidator(validator)
        editor.textChanged.connect(self._update_scene)
        return editor
    
    def set_range(self, min:float, max:float):
        """Sets the range of the editor

        Args:
            min (float): min value
            max (float): max value
        """
        self._editor.validator().setRange(min, max)
    
    def _set_value(self, editor:QtWidgets.QWidget, value:float):
        editor.setText(str(float(value)))
    
    def _value(self, editor:QtWidgets.QWidget)->float:
        if not editor.text():
            return 0.0
        return float(editor.text())
        
class BoolInput(InputBase):
    """Node with a slider
    
    Args:
        title(str)
        color(QColor)
        parent(QGraphicsItem)
    """
    default_name = "Bool"
    menu_label = "Checkbox"
    def __init__(self, title:str=None, color:QtGui.QColor=None, parent:QtWidgets.QGraphicsItem=None):
        super().__init__(title, color, parent)
    
    def type(self)->KnobTypes:
        return KnobTypes.Bool
    
    def _init_from_knob(self, editor:QtWidgets.QWidget, knob:nuke.Knob):
        self.set_value(knob.value())
        return
    
    def _create_widget(self)->QtWidgets.QWidget:
        editor = QtWidgets.QCheckBox()
        editor.toggled.connect(self._update_scene)
        return editor
    
    def _set_value(self, editor:QtWidgets.QWidget, value:bool):
        editor.setText(bool(value))
    
    def _value(self, editor:QtWidgets.QWidget)->bool:
        return editor.isChecked()
        
class EnumInput(InputBase):
    """Node with a slider
    
    Args:
        title(str)
        options(List[str])
        color(QColor)
        parent(QGraphicsItem)
    """
    default_name = "Option"
    menu_label = "Options"
    def __init__(self, title:str=None, options:List[str]=None, color:QtGui.QColor=None, parent:QtWidgets.QGraphicsItem=None):
        self._options = options or []
        super().__init__(title, color, parent)
    
    def type(self)->KnobTypes:
        return KnobTypes.EnumTypes
    
    def _init_from_knob(self, editor:QtWidgets.QWidget, knob:nuke.Knob):
        self._set_options(get_knob_options(knob))
        self.set_value(knob.value())
        return
    
    def _create_widget(self)->QtWidgets.QWidget:
        editor = QtWidgets.QComboBox()
        editor.addItems(self._options)
        editor.currentTextChanged.connect(self._update_scene)
        return editor

    def _set_options(self, options:List[str]):
        """Sets the options for this combobox

        Args:
            options (List[str])
        """
        current_value = self.value()
        blocked = self._editor.blockSignals(True)
        self._editor.clear()
        self._editor.addItems(options)
        if current_value in options:
            self._editor.setCurrentIndex(options.index(current_value))
        self._editor.blockSignals(blocked)
        
    def _set_value(self, editor:QtWidgets.QWidget, value:str|int):
        if isinstance(value, str):
            if value in self._options:
                self._editor.setCurrentIndex(self._options.index(value))
        else:
            # assume float/int
            value = int(float(value))
            if value < 0 or value >= self._options:
                return
            self._editor.setCurrentIndex(value)
    
    def _value(self, editor:QtWidgets.QWidget)->str:
        return editor.currentText()

class Connection(object):
    """A struct to hold the connection data

    Args:
        plug(Plug)
        knob(nuke.Knob)
    """
    def __init__(self, plug:Plug, knob:nuke.Knob):
        self.plug = plug
        self.knob = knob
    
    @property
    def node(self):
        return self.knob.node()


class Scene(QtWidgets.QGraphicsScene):
    """ A Simple scene to hold the nodes and track any in-progress connections
    """
    def __init__(self):
        super().__init__()
        self._glwidget = None
        self.setSceneRect(QtCore.QRect(QtCore.QPoint(-10000, -10000), QtCore.QPoint(10000, 10000)))
        self.active_plug = None
        self.connections = []
    
    def value_changed(self, plug:Plug, value):
        for connection in self.connections:
            if connection.plug == plug:
                set_knob_value(connection.knob, value)
    
    def beginConnectionDrag(self, plug:Plug):
        self.active_plug = plug
    
    def mouseReleaseEvent(self, event:QtWidgets.QGraphicsSceneMouseEvent):
        if self.active_plug:
            # find node under cursor
            transform = QtGui.QTransform()
            zoom = nuke.zoom()
            offset = self._glwidget.geometry().center()/zoom - QtCore.QPoint(*nuke.center())
            transform.scale(zoom, zoom)
            transform.translate(offset.x(), offset.y())
            pos = transform.inverted()[0].map(self._glwidget.mapFromGlobal(QtGui.QCursor.pos()))
            node = node_at(pos)
            if node:
                # Create connection
                menu = QtWidgets.QMenu()
                menu.setAttribute(QtCore.Qt.WA_DeleteOnClose)
                
                names = []
                for knob in node.allKnobs():
                    if not knob.visible():
                        continue
                    knob_type = KnobTypes.from_knob(knob)
                    if knob_type & self.active_plug.type:
                        names.append(knob.name())
                
                for name in sorted(names):
                    menu.addAction(name)
                
                action = menu.exec_(QtGui.QCursor.pos())
                if action:
                    self.connections.append(self.active_plug.connect(node.knob(action.text())))
        self.active_plug = None
        super().mouseReleaseEvent(event)
    

class Graph(QtWidgets.QGraphicsView):
    """Node graph overlay

    Args:
        glwidget(QGLWidget): The node graph to attach to
        parent(QWidget): parent widget
    """
    def __init__(self, glwidget:QtOpenGL.QGLWidget, parent:QtWidgets.QWidget=None):
        self._drawing = False
        scene = Scene()
        scene._glwidget = glwidget
        super().__init__(scene=scene, parent=parent)
        self._settings = QtCore.QSettings("minimaleffort.tech", "NukeDrawing", parent=self)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self._glwidget = glwidget
        self._pressed = False
        self.setTransformationAnchor(QtWidgets.QGraphicsView.NoAnchor)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.setViewportUpdateMode(QtWidgets.QGraphicsView.FullViewportUpdate)
        self.setCacheMode(QtWidgets.QGraphicsView.CacheNone)
        self.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, True)
        if parent:
            self.setGeometry(parent.geometry())
            # Todo: resize with parent\
        self.scene().invalidate(self.scene().sceneRect())
        self._update_transform()
        
        self._sidebar = SideBar(self)
        self._sidebar.hide()
        self._sidebar.color = self._settings.value("color", QtGui.QColor("#FF0000"))
        self._sidebar.width = self._settings.value("width", 2)
        self._sidebar.on_top = self._settings.value("on_top") or False
        
        self._note_toggle = QtWidgets.QCheckBox("Show Notes", self)
        self._note_toggle.setChecked(True)
        self._note_toggle.setAutoFillBackground(True)
        self._note_toggle.clicked.connect(self._draw)
        self._note_toggle.move(0, self.geometry().bottom() - self._note_toggle.height() + 10)
        
        # Painting
        self._last_pos = QtCore.QPointF()
        self._undos = []
        self._top_paths = []
        self._base_paths = []
        self._active_path = None
        
    def _update_transform(self):
        """Syncs the view transform against nuke
        """
        transform = QtGui.QTransform()
        zoom = nuke.zoom()
        center = self._glwidget.geometry().center()
        offset = center - QtCore.QPoint(*nuke.center())
        transform.translate(center.x(), center.y())
        transform.scale(zoom, zoom)
        transform.translate(-center.x(), -center.y())
        transform.translate(offset.x(), offset.y())
        self.setTransform(transform)
        
    def drawBackground(self, painter:QtGui.QPainter, rect:QtCore.QRectF):
        hex_color = nuke.toNode('preferences').knob("DAGBackColor").value()
        color = hex_to_qcolor(hex_color)
        painter.setPen(QtCore.Qt.NoPen)
        painter.setBrush(color)
        painter.drawRect(rect)
        painter.setPen(QtCore.Qt.black)
        
        # Draw any notes
        if self._note_toggle.isChecked():
            painter.save()
            painter.setBrush(QtCore.Qt.NoBrush)
            for primitive in self._base_paths:
                pen = QtGui.QPen(primitive.color)
                pen.setWidth(primitive.width)
                painter.setPen(pen)
                painter.drawPath(primitive.path)
                # print (primitive.path.boundingRect())
            painter.restore()
        
        transform = QtGui.QTransform()
        zoom = nuke.zoom()
        offset = self._glwidget.geometry().center()/zoom - QtCore.QPoint(*nuke.center())
        transform.scale(zoom, zoom)
        transform.translate(offset.x(), offset.y())
        for connection in self.scene().connections:
            start = connection.plug.mapToScene(5, 5)
            pos = transform.inverted()[0].map(node_rect(connection.node).center())
            node_pos = self.mapFromScene(pos)
            end = node_pos
            painter.drawLine(start, end)
            
        # # Draw anything that needs to go between background and nuke nodes here
        # image:QtGui.QImage = self._glwidget.grabFrameBuffer(False)
        image:QtGui.QImage = self._glwidget.grabFrameBuffer(True)
        painter.drawImage(rect, image)
        # TODO: draw connection labels
        
    def drawForeground(self, painter:QtGui.QPainter, rect:QtCore.QRectF):
        # Draw any notes
        if self._note_toggle.isChecked():
            painter.save()
            painter.setBrush(QtCore.Qt.NoBrush)
            for primitive in self._top_paths:
                pen = QtGui.QPen(primitive.color)
                pen.setWidth(primitive.width)
                painter.setPen(pen)
                painter.drawPath(primitive.path)
            painter.restore()
        
        # Pending connections
        if self.scene().active_plug:
            start = self.scene().active_plug.mapToScene(5, 5)
            pen = QtGui.QPen(QtGui.QColor("dodgerblue"))
            pen.setWidth(2)
            painter.setPen(pen)
            painter.drawLine(start, self.mapToScene(self.mapFromGlobal(QtGui.QCursor.pos())))
        
    def _send_mouse_event(self, event:QtGui.QMouseEvent):
        """Sends a mouse event to the invisible nuke glwidget

        Args:
            event (QtGui.QMouseEvent): event
        """
        w = self._glwidget
        relpos = event.pos()
        me = QtGui.QMouseEvent(event.type(), relpos, event.windowPos(), event.globalPos(),
                               event.button(), event.buttons(), event.modifiers(), event.source())
        while(w):
            if not w.hasMouseTracking() and me.type() == QtCore.QEvent.MouseMove and me.buttons() == 0:
                pass  # todo
            else:
                w.event(event)
            if me.isAccepted():
                w.update()
                break
            if w.isWindow() or w.testAttribute(QtCore.Qt.WA_NoMousePropagation):
                break
            
            relpos += w.pos()
            w = w.parentWidget()
    
    def _draw(self):
        """Trigger a scene redraw, this must happen after the current event loop to reduce jitter
        """
        self._glwidget.update()
        QtCore.QTimer.singleShot(20, lambda:
            self.scene().invalidate(self.scene().sceneRect()))

    def mouseDoubleClickEvent(self, event:QtGui.QMouseEvent):
        item = self.itemAt(event.pos())
        if item and (isinstance(item, InputBase) or isinstance(item.parentItem(), InputBase)):
            if not isinstance(item, InputBase):
                item = item.parentItem()
            name, ok = QtWidgets.QInputDialog.getText(self, "Rename Node", "Name:", QtWidgets.QLineEdit.Normal, item.title())
            if ok:
                item.set_title(name)
                return
        self._send_mouse_event(event)
        super().mouseDoubleClickEvent(event)
        self._draw()

    def mousePressEvent(self, event:QtGui.QMouseEvent):
        if self._drawing and event.button() == QtCore.Qt.LeftButton:
            self._last_pos = self.mapToScene(event.pos())
            self._active_path = Primitive()
            self._active_path.path = QtGui.QPainterPath(self._last_pos)
            self._active_path.color = self._sidebar.color
            self._active_path.width = self._sidebar.width
            if self._sidebar.on_top:
                self._top_paths.append(self._active_path)
            else:
                self._base_paths.append(self._active_path)
            self._undos = []
            self._draw()
            return
        super().mousePressEvent(event)
        if self.items(event.pos()):
            self._pressed = True
        else:
            self._pressed = False
            self._send_mouse_event(event)
            self._draw()
    
    def mouseMoveEvent(self, event:QtGui.QMouseEvent):
        if self._drawing and self._active_path:
            self._last_pos = self.mapToScene(event.pos())
            self._active_path.path.lineTo(self._last_pos)
            self._draw()
            return
        self._send_mouse_event(event)
        super().mouseMoveEvent(event)
        self._draw()
        self._update_transform()
    
    def event(self, event:QtCore.QEvent)->bool:
        # TODO: This is not ideal...
        if event.type() == QtCore.QEvent.ShortcutOverride and event.key() == QtCore.Qt.Key_Tab:
            QtCore.QTimer.singleShot(20, lambda: QtTest.QTest.keyClick(self._glwidget, QtCore.Qt.Key_Tab))
        return super().event(event)
    
    def keyPressEvent(self, event:QtGui.QKeyEvent):
        if self._drawing:
            # TODO: Clean this up
            if event.matches(QtGui.QKeySequence.Undo) and self._paths:
                return
            elif event.matches(QtGui.QKeySequence.Redo) and self._undos:
                return
            elif event.key() in (QtCore.Qt.Key_Escape, QtCore.Qt.Key_Enter, QtCore.Qt.Key_Return):
                return
            
        if self.scene().focusItem():
            super().keyPressEvent(event)
            return
        w = self._glwidget
        ke = QtGui.QKeyEvent(event.type(), event.key(), event.modifiers(), event.text(), event.isAutoRepeat(), event.count())
        while(w):
            w.event(ke)
            if ke.isAccepted():
                w.update()
                break
            w = w.parentWidget()
        if not ke.isAccepted():
            super().keyPressEvent(event)
        self._draw()
    
    def focusNextPrevChild(self, next:bool)->bool:
        return False
    
    def keyReleaseEvent(self, event:QtGui.QKeyEvent):
        if self._drawing:
            if event.matches(QtGui.QKeySequence.Undo) and self._paths:
                if self._sidebar.on_top:
                    self._undos.append(self._top_paths.pop())
                else:
                    self._undos.append(self._base_paths.pop())
                self._draw()
                event.accept()
                return
            elif event.matches(QtGui.QKeySequence.Redo) and self._undos:
                if self._sidebar.on_top:
                    self._top_paths.append(self._undos.pop())
                else:
                    self._base_paths.append(self._undos.pop())
                self._draw()
                event.accept()
                return
            elif event.key() in (QtCore.Qt.Key_Enter, QtCore.Qt.Key_Return,QtCore.Qt.Key_Escape):
                self.toggle_draw()
                self._settings.setValue("color", self._sidebar.color)
                self._settings.setValue("width", self._sidebar.width)
                self._settings.setValue("on_top", self._sidebar.on_top)
                event.accept()
                self._draw()
                return
            
        if self.scene().focusItem():
            super().keyReleaseEvent(event)
            return
        w = self._glwidget
        ke = QtGui.QKeyEvent(event.type(), event.key(), event.modifiers(), event.text(), event.isAutoRepeat(), event.count())
        while(w):
            w.event(ke)
            if ke.isAccepted():
                w.update()
                break
            w = w.parentWidget()
        if not ke.isAccepted():
            super().keyReleaseEvent(event)
        self._draw()
    
    def mouseReleaseEvent(self, event:QtGui.QMouseEvent):
        self._active_path = None
        if not self._pressed and not (self._drawing and event.button() == QtCore.Qt.LeftButton):
            self._send_mouse_event(event)
        self._pressed = False
        super().mouseReleaseEvent(event)
        self._draw()
    
    def wheelEvent(self, event:QtGui.QWheelEvent):
        w = self._glwidget
        relpos = event.pos()
        me = QtGui.QWheelEvent(event.pos(), event.globalPos(), event.pixelDelta(), event.angleDelta(),
                               event.buttons(), event.modifiers(), event.phase(), event.inverted(),
                               event.source())
        while(w):
            w.event(event)
            if me.isAccepted():
                w.update()
                break
            if w.isWindow() or w.testAttribute(QtCore.Qt.WA_NoMousePropagation):
                break
            
            relpos += w.pos()
            w = w.parentWidget()
        self._glwidget.update()
        event.accept()
        self._update_transform()
        self._draw()
        
    def toggle_draw(self):
        """Toggle drawing mode
        """
        self._drawing = not self._drawing
        if self._drawing:
            self._sidebar.show()
        else:
            self._sidebar.hide()
    
    def add_menu(self):
        """Show the add menu
        """
        menu = QtWidgets.QMenu()
        menu.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        for cls in InputBase.__subclassess__():
            action = menu.addAction(cls.menu_label)
        
        action = menu.exec_(QtGui.QCursor.pos())
        if not action:
            return
        
        for cls in InputBase.__subclassess__():
            if action.text() == cls.menu_label:
                node = cls()
                break
        else:
            # TODO: Error message
            return
        
        self.scene().addItem(node)
        node.setPos(QtCore.QPointF(*nuke.center()))
        
        
# This just finds the current node graph, this could also be adapted to add to multiple node graphs
# To initialize on each graph on start you would need some listeners
nuke_graph = None
for win in QtWidgets.QApplication.topLevelWidgets():
    for child in win.findChildren(QtOpenGL.QGLWidget):
        p = child.parent()
        if p.metaObject().className() == "Foundry::UI::LinkedView" and p.objectName().startswith("DAG."):
            nuke_graph = child
            break
    else:
        continue
    break

graph = Graph(nuke_graph, parent=nuke_graph.parent())
graph.show()

toolbar = nuke.toolbar('Nodes', create=False)
toolbar.addCommand("draw", graph.toggle_draw, icon=BRUSH_ICON)
toolbar.addCommand("add", graph.add_menu, icon=ADD_ICON)