# Copyright (C) 2024 Alex Telford
# http://minimaleffort.tech
# This work is licensed under the Creative Commons Attribution 4.0 International License.
# To view a copy of this license, visit http://creativecommons.org/licenses/by/4.0/ or send a letter to Creative Commons,
# PO Box 1866, Mountain View, CA 94042, USA.
# Distributed without any warranty or liability, use at your own risk

# This script allows you to click a widget to get information about it's internals in Qt.
# There is so much more you can do with the metaobject system in Qt, but hopefully this gets you started


from PySide2 import QtWidgets, QtGui, QtCore, QtOpenGL
from typing import List
import collections
# This is not perfect, but suits for example purposes, you can go deeper into introspection for better results.
BASE_CLASSES = [s for s in dir(QtCore)+dir(QtWidgets)+dir(QtOpenGL) if s[0] == "Q"]


class ClickHandler(QtCore.QObject):
    """
    A simple event listener to listen for a click to grab the widget under the cursor
    """
    def __init__(self, parent:QtCore.QObject=None):
        super().__init__(parent)
        # Generally this is not advised, but works for this debug script
        if parent:
            parent.installEventFilter(self)
            QtWidgets.QApplication.setOverrideCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
    
    def eventFilter(self, obj:QtCore.QObject, event:QtCore.QEvent)->bool:
        try:
            if event.type() == QtCore.QEvent.KeyPress and event.key() & (QtCore.Qt.Key_Enter|QtCore.Qt.Key_Escape|QtCore.Qt.Key_Return):
                # User is escapping, clean it up
                obj.removeEventFilter(self)
                QtWidgets.QApplication.restoreOverrideCursor()
                self.setParent(None)
                self.deleteLater()
            
            if event.type() == QtCore.QEvent.MouseButtonPress:
                QtWidgets.QApplication.restoreOverrideCursor()
                obj.removeEventFilter(self)
                widget = QtWidgets.QApplication.widgetAt(QtGui.QCursor.pos())
                print("="*20)
                _debug_qobject_hierarchy(widget)
                print("="*20)
                _debug_qobject_internals(widget)
                print("="*20)
                self.setParent(None)
                self.deleteLater()
                return True
        except:
            # Prevents an infinite loop if you change some code
            obj.removeEventFilter(self)
            QtWidgets.QApplication.restoreOverrideCursor()
            self.setParent(None)
            self.deleteLater()
            raise
            
        return False


def _get_inheritance(meta_object:QtCore.QMetaObject)->List[QtCore.QMetaObject]:
    """ Gets the inheritance stack until it gets to Qt (inclusive)
    
    Args:
        meta_object(QtCore.QMetaObject)
    
    Returns:
        Inheritance stack
    """
    meta_objects:List[QtCore.QMetaObject] = [meta_object]
    while meta_object:
        meta_object = meta_object.superClass()
        meta_objects.append(meta_object)
        if meta_object.className() in BASE_CLASSES:
            break
    return meta_objects


def _debug_qobject_hierarchy(qobject:QtCore.QObject):
    """ Prints the debug stack of a private object
    
    Args:
        qobject(QtCore.QObject)
    """
    hierarchy = collections.deque()
    obj = qobject
    while obj:
        hierarchy.appendleft(obj)
        obj = obj.parent()
    
    print("Hierarchy")
    print("-"*20)
    indent = 0
    for obj in hierarchy:
        # https://doc.qt.io/qt-5/qmetaobject.html
        meta_object:QtCore.QMetaObject = obj.metaObject()
        object_name = obj.objectName()  # This is the exposed name
        class_name = meta_object.className()  # Class name whether from C++ or Python, can also use staticMetaObject on a class pointer
        
        # Here we find how this custom class inherits from Qt
        inheritance = _get_inheritance(meta_object)
        classes = [mo.className() for mo in inheritance]
        print(f"{'  '*indent}{class_name}{f' ({object_name})' if object_name else ''} {' << '.join(classes)}")
        indent += 1


def _debug_qobject_internals(qobject:QtCore.QObject, indent:int=0):
    """ Prints out custom properties, signals, slots, etc
    
    Args:
        qobject(QtCore.QObject)
        indent(int)
    """
    meta_object:QtCore.QMetaObject = qobject.metaObject()
    object_name = qobject.objectName()  # This is the exposed name
    class_name = meta_object.className()  # Class name whether from C++ or Python, can also use staticMetaObject on a class pointer
    
    inheritance = _get_inheritance(meta_object)
    classes = [mo.className() for mo in inheritance]
    # Class type, name and inheritance
    print(f"{'  '*indent}{class_name}{f' ({object_name})' if object_name else ''} {' << '.join(classes)}")
    
    # Class Info
    print(f"{'  '*indent}Class Info:")
    base = inheritance[-2] # Ignoring Qt, get the most base level class
    indent += 1
    method_offset = base.methodOffset()
    method_count = meta_object.methodCount()
    for i in range(base.classInfoOffset(), meta_object.classInfoCount()):
        class_info:QtCore.QMetaClassInfo = meta_object.classInfo(i)
        name:str = class_info.name()
        value:str = class_info.value()
        print(f"{'  '*indent}{name} = {value}")
    indent -= 1
        
    # Properties
    print(f"{'  '*indent}Dynamic Properties:")
    indent += 1
    for name in qobject.dynamicPropertyNames():
        if name == "_PySideInvalidatePtr":
            continue
        try:
            value = qobject.property(name)
        except:
            value = "<unreadable>"
        print(f"{'  '*indent}{name} = {value}")
    indent -= 1
    print(f"{'  '*indent}Properties:")
    property_offset = base.propertyOffset()  # This is the index of the first property created by this class
    property_count = meta_object.propertyCount()  # This is the total number of properties on this class
    indent += 1
    for i in range(property_offset, property_count):
        # https://doc.qt.io/qt-5/qmetaproperty.html
        meta_property:QtCore.QMetaProperty = meta_object.property(i)
        name:str = meta_property.name()
        try:
            value = meta_property.read(qobject)  # Note this may error for non-exposed types
        except:
            value = "<unreadable>"
        
        info:str = f"{'  '*indent}{name} = {value}"
        
        if meta_property.notifySignalIndex() != -1:
            # this is the signal that is emitted when this property changes
            signal:QtCore.QMetaMethod = meta_property.notifySignal()
            info += f"  emits: {signal.methodSignature()}"
        
        print(info)
    indent -= 1
    
    # Methods
    # Methods and signals are both stored as methods by Qt
    slots:List[QtCore.QMetaMethod] = []
    signals:List[QtCore.QMetaMethod] = []
    method_offset = base.methodOffset()  # This is the index of the first method created by this class
    method_count = meta_object.methodCount()  # This is the total number of methods/signals on this class
    for i in range(method_offset, method_count):
        # https://doc.qt.io/qt-5/qmetamethod.html
        meta_method:QtCore.QMetaMethod = meta_object.method(i)
        match meta_method.methodType():
            case QtCore.QMetaMethod.Signal:
                signals.append(meta_method)
            case QtCore.QMetaMethod.Slot:
                slots.append(meta_method)
            case QtCore.QMetaMethod.Constructor:
                pass  # Constructor, ignore
            case QtCore.QMetaMethod.Method:
                pass  # Standard method, ignore
            case _:
                pass
    print(f"{'  '*indent}Signals:")
    indent += 1
    for meta_method in signals:
        # https://doc.qt.io/qt-5/qmetamethod.html
        # name:str = meta_method.name()
        signature:str = meta_method.methodSignature()
        # Note you can also extract paramater and return types! check the docs for more info
        print(f"{'  '*indent}{signature}")
        
    indent -= 1
    print(f"{'  '*indent}Slots:")
    indent += 1
    for meta_method in slots:
        signature:str = meta_method.methodSignature()
        print(f"{'  '*indent}{signature}")
    indent -= 1
        

""" Install to Nuke, it's a similar process for Maya, Houdini, etc, but I have nuke open right now so...
"""
import nuke
def _track_click():
    ClickHandler(QtWidgets.QApplication.instance())
        
toolbar = nuke.toolbar('Nodes', create=False)
toolbar.addCommand("Qdbg", _track_click)