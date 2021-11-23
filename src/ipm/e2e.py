"""Functions to perform interactions with graphical user interfaces on
behalf of regular users.

This library offers a functional api to perform programmatically common
interactions with the graphical interface. In order to do its job,
this library uses the at-spi api, so the corresponding service must be
available and the applications must implement the api.

If you rather like it, think of this library as an abstraction of the
at-spi api. This abstraction is intended to ease the use of the api.

Examples
--------

Implementation of Gherkin steps::

    # GIVEN I started the application
    process, app = e2e.run("./contador.py")
    ## ok ?
    if app is None:
        process and process.kill()
        assert False, f"There is no aplication {path} in the desktop"
    do, shows = e2e.perform_on(app)

    # WHEN I click the button 'Contar'
    do('click', role= 'push button', name= 'Contar')

    # THEN I see the text "Has pulsado 1 vez"
    assert shows(role= "label", text= "Has pulsado 1 vez")

    ## Before leaving, clean up your mess
    process and process.kill()


"""

from __future__ import annotations

from collections.abc import ByteString
from pathlib import Path
import random
import re
import subprocess
import sys
import textwrap
import time
from typing import Any, AnyStr, Callable, Iterable, Iterator, NamedTuple, Optional, Protocol, TypeVar, Union

import gi
gi.require_version('Atspi', '2.0')
from gi.repository import Atspi

__all__ = [
    'do',
    'expect',
    'expect_all',
    'expect_any',
    'expect_first',
    'expect_one',
    'objects_in',
    'run',
    
    'obj_get_attr',
    'obj_children',
    'tree_walk',
    'is_error',
    'fail_on_error',
    'Either',
    'MatchArgs',
]


class NotFoundError(Exception): pass


T = TypeVar('T')
Either = Union[Exception, T]
"""The classic Either type, i.e. a value of type T or an error.

*N.B.:* The typing and implementation of the functions using this type
is quite relaxed (unorthodox).

"""


def is_error(x: Either[Any]) -> bool:
    """Checks whether any python object represents an error.
    
    This function is intended to be used with values of type ``Either``.

    Parameters
    ----------
    x : Either[T]
        The object to check

    Returns
    -------
    bool
        whether it's an error

    """
    return isinstance(x, Exception)


def fail_on_error(x: Either[Any]) -> Any:
    """Raises an exception on error.

    Raiese an exception when the python object represents an error,
    otherwise returns the object itself.

    Parameters
    ----------
    x : Either[T]
        The object to check

    Returns
    -------
    T
        The python object when it is not an error

    Raises
    ------
    Exception
        The exception that corresponds to the error

    """
    
    if is_error(x):
        raise x
    return x

    
def _pprint(obj: Atspi.Object) -> str:
    role = obj.get_role_name()
    name = obj.get_name() or ""
    return f"{role}('{name}')"


def _get_action_idx(obj: Atspi.Object, name: str) -> Optional[int]:
    for i in range(obj.get_n_actions()):
        if obj.get_action_name(i) == name:
            return i
    return None


def _get_actions_names(obj: Atspi.Object) -> list[str]:
    return [ obj.get_action_name(i) for i in range(obj.get_n_actions()) ]


def obj_get_attr(obj: Atspi.Object, name:str) -> Either[str]:
    """Returns the value of an at-spi object's attribute.

    Some attributes are not actual attributes in at-spi, and must be
    retrieved using an at-spi function like `get_text()`. This
    function can chooice the right way to access attributes.

    Parameters
    ----------
    obj : Atspi.Object
        The object from which to retrieve the value of the attriute
    name : str
        The name of the attribute

    Returns
    -------
    str
        The value of the attribute
    AttributeError
        When the object has no such attribute
    """
    
    if name == 'role':
        return obj.get_role_name()
    elif name == 'name':
        return obj.get_name() or ""
    elif name == 'text':
        return obj.get_text(0, -1)
    elif hasattr(obj, name):
        return getattr(obj, name)
    elif hasattr(obj, f"get_{name}"):
        return getattr(obj, f"get_{name}")()
    else:
        return AttributeError(f"{_pprint(obj)} has no attribute {name}")
    

# Cuando buscamos todos los valores son strings aunque el tipo del
# atributo sea un Enum.
# Podríamos intentar usar el valor, p.e.:
# ```python
# from e2e import role
# do('click', role= role.BUTTON, name= _('Count'))
# ```
#
# Eso nos obligaría a cargar las definiciones de los Enums al cargar
# el módulo, o hacerlo _on-the-fly_ con una cache.
#
# Ahora mismo, cuando una búsqueda falla. Revisamos los valores de los
# attributos que en realidad son de tipo Enum para ver si no está en
# la lista y poder dar un mensaje de error más útil.
#
# TODO: decidir si implementar la primera opción.
# TODO: añadir más casos a la función
def _help_not_found(kwargs) -> str:
    msg = ""
    role = kwargs.get('role', None)
    if role and role.upper() not in Atspi.Role.__dict__:
        msg = f"{msg}\n{role} is not a role name"
    return msg


MatchPattern = Union[AnyStr,
                     re.Pattern,
                     Callable[[Atspi.Object],bool],
                     Callable[[Any],bool]]

#MatchAargs = dict[str, MatchPattern]
from typing import Dict
MatchArgs = Dict[str, MatchPattern]
"""A dict containing a list of patterns an at-spi object should match.

An object matches the list of patterns if and only if it matches all
the patterns in the list. 

Each pair ``name: value`` is interpreted as follows:

    **name = 'when':** Predicate on the object.

        The value is a function ``Atspi.Object -> bool``. This
        function returns whether or not the at-spi objects matches
        this pattern.

    **name = 'nth':** Position of the object.

        The value must be the position of the at-spi object among its
        siblings. As usual the positions start at 0, and negative
        indexes are refered to the end of the list.

    **name = 'path':** TODO

    **name = '...':** Otherwise, one of the object's atrributes.

        The name is interpreted as the name of one object's attribute,
        and the value is interpreted as follows:

            **value = str | bytes:** String or bytes.

                The value must equal to the value of the object's
                attribute.

            **value = re.Pattern:** A regular expression.

                The object's attribute value must match the given re.

            **value = function(Any -> bool):** A predicate on the attribute's value.

                The function must return True when called with the
                object's attribute value as argument.

"""

# TODO: Parámetro `path` el valor puede incluir patrones. Hay que ver
# qué lenguaje usamos. Tiene que machear con el path desde el root
# hasta el widget.  ¿ Nos interesa incluir otros atributos además de
# la posición dentro de los siblings ?
def _match(obj: Atspi.Object, path: TreePath, name: str, value: Any) -> bool:
    if name == 'path':
        TODO
        
    elif name == 'nth':
        nth_of = path[-1]
        idx = value if value >= 0 else nth_of.n + value
        return idx == nth_of.i
    
    elif name == 'when':
        return value(obj, path)
    
    # From now on, the name is the name of an object's attribute
    elif type(value) == str or isinstance(value, ByteString):
        return obj_get_attr(obj, name) == value
    
    elif type(value) == re.Pattern:
        attr_value = obj_get_attr(obj, name)
        if is_error(attr_value):
            return False
        return value.fullmatch(attr_value) is not None
    
    elif callable(value):
        return value(obj_get_attr(obj, name))
    
    # It looks like an error
    else:
        TODO


def _find_all_descendants(root: Atspi.Object, kwargs: MatchArgs) -> Iterable[Atspi.Object]:
    if len(kwargs) == 0:
        descendants = (obj for _path, obj in tree_walk(root))
    else:
        descendants = (obj for path, obj in tree_walk(root)
                       if all(_match(obj, path, name, value) for name, value in kwargs.items()))
    return descendants

    
def obj_children(obj: Atspi.Object) -> list[Atspi.Object]:
    """Obtains the list of children of an at-spi object.

    Parameters
    ----------
    obj : Atspi.Object
        The object whose children will be queried.

    Returns
    -------
    list[Atspi.Object]
        The list of object's children.
    """
    
    return [ obj.get_child_at_index(i) for i in range(obj.get_child_count()) ]


class NthOf(NamedTuple):
    i : int
    n : int

    def is_last(self) -> bool:
        return self.i == self.n - 1
    
    def __str__(self) -> str:
        return f"{self.i}/{self.n}"


TreePath = tuple[NthOf, ...]


ROOT_TREE_PATH = (NthOf(0, 1),)


def tree_walk(root: Atspi.Object, path: TreePath= ROOT_TREE_PATH) -> Iterator[tuple[TreePath, Atspi.Object]]:
    """Creates a tree traversal.

    This function performs an inorder tree traversal, starting at the
    given _root_ (at-spi object). Foreach visited node, it yields the
    path from the root to the node, and the node itself.

    The path includes the position and the number of siblings of each
    node.

    Parameters
    ----------
    root : Atspi.Object
        The root node where to start the traversal.

    path : TreePath, optional
        A prefix for the paths yielded.

    Yields
    ------
    (TreePath, Atspi.Object)
        A tuple containing the path to the node and the node itself

    """
    
    yield path, root
    children = obj_children(root)
    n_children = len(children)
    for i, child in enumerate(children):
        yield from tree_walk(child, path= path + (NthOf(i,n_children),))


def objects_in(root_s: Union[Atspi.Object, Iterable[Atspi.Object]],
                  **kwargs: MatchArgs) -> Iterable[Atspi.Object]:
    """Returns an iterable for all the objects that matches the given
    conditions.

    It searches below `root/s` the objects that matches the arguments
    given in `kwargs`. As might be expected, below object means in the
    subtree which root is this object.

    Parameters
    ----------
    root_s: Union[Atspi.Object, Iterable[Atspi.Object]]
        The root/s of the subtree/s where the search is performed.

    **kwargs
        See :py:data:`MatchArgs`

    Returns
    -------
    Iterable[Atspi.Object]
        An iterable of the objects that matches the conditions.

    """

    if isinstance(root_s, Atspi.Object):
        root_s = [root_s]

    result = []
    if len(kwargs) == 0:
        for root in root_s:
            result.extend(obj for _path, obj in tree_walk(root))
    else:
        for root in root_s:
            result.extend(_find_all_descendants(root, kwargs))
    return result
        

_MARK = object()


class Action:
    def __init__(self, action_name: str):
        self.action_name = action_name

    def on_all(self, objs: Iterable[Atspi.Object]) -> None:
        for obj in objs:
            self._do_action(obj)

    def on_first(self, objs: Iterable[Atspi.Object]) -> None:
        obj = next(objs)
        self._do_action(obj)

    def on(self, objs: Iterable[Atspi.Object]) -> None:
        objs_iter = iter(objs)
        obj = next(objs_iter)
        if next(objs_iter, _MARK) is not _MARK:
            raise AssertionError(f"when doing '{self.action_name}' on object"
                                 f", found more than one object: {objs}")
        self._do_action(obj)

    def __str__(self) -> str:
        return f"do('self.action_name')"
    
    def _do_action(self, obj: Atspi.Object) -> None:
        idx = _get_action_idx(obj, self.action_name)
        if idx is None:
            names = _get_actions_names(obj)
            raise NotFoundError(f"widget {_pprint(obj)} has no action named '{self.action_name}', got: {','.join(names)}")
        obj.do_action(idx)


do = Action


class Expectation:
    def __init__(self, objects: Iterable[Atspi.Object], which_one: str):
        self.objects = objects
        self.which_one = which_one

    def to_show(self, text: AnyStr) -> None:
        predicate = lambda obj: obj_get_attr(obj, 'text') == text
        if not self._check(predicate):
            texts = [ f"  {_pprint(obj)} shows \"{obj_get_attr(obj, 'text')}\"" for obj in self.objects ]
            raise AssertionError(f"expect {self.which_one} to show \"{text}\", but:\n" +
                                 "\n".join(texts))

    def _check(self, predicate: Callable[[Atspi.Object],bool]) -> bool:
        if self.which_one == 'all':
            return all(predicate(obj) for obj in self.objects)
        elif self.which_one == 'any':
            return any(predicate(obj) for obj in self.objects)
        elif self.which_one == 'first':
            obj = next(self.objects, _MARK)
            return obj is not _MARK and predicate(obj)
        elif self.which_one == 'one':
            checks = [ obj for obj in self.objects if predicate(obj) ]
            return len(checks) == 1
        else:
            raise RuntimeError(f"unknown which_one= {self.which_one}")

    def __str__(self) -> str:
        # // TODO: Si Iterable[Atspi.Object] es un generador, aquí ya
        # lo hemos agotado y no lo podemos volver a recorrer
        objects_str = ",".join(_pprint(obj) for obj in self.objects)
        return f"expect_{self.which_one}({objects_str})"


def expect(objects: Iterable[Atspi.Object]) -> Expectation:
    return Expectation(objects, 'all')


def expect_all(objects: Iterable[Atspi.Object]) -> Expectation:
    return Expectation(objects, 'all')


def expect_any(objects: Iterable[Atspi.Object]) -> Expectation:
    return Expectation(objects, 'any')


def expect_first(objects: Iterable[Atspi.Object]) -> Expectation:
    return Expectation(objects, 'first')


def expect_one(objects: Iterable[Atspi.Object]) -> Expectation:
    return Expectation(objects, 'one')


###########################################################################
def _wait_for_app(name: str, timeout: Optional[float]= None) -> Optional[Atspi.Object]:
    desktop = Atspi.get_desktop(0)
    start = time.time()
    app = None
    timeout = timeout or 5
    while app is None and (time.time() - start) < timeout:
        gen = (child for child in obj_children(desktop)
               if child and child.get_name() == name)
        app = next(gen, None)
        if app is None:
            time.sleep(0.6)
    return app


class SUT(NamedTuple):
    process: subprocess.Popen
    app: Optional[Atspi.Object]
    path: Union[str, pathlib.Path]

    def __enter__(self):
        if self.app is None:
            raise RuntimeError(f"the application {self.path} didn't show up in desktop")
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self.process:
            self.process.kill()


def run(path: Union[str, Path],
        name: Optional[str]= None,
        timeout: Optional[float]= None) -> AbstractContextManager[SUT]:
    """Runs the command in a new os process. Waits for application to
    appear in desktop.

    Starts a new os process and runs the given command in it. The
    command should start an application that implements the at-spi and
    provides a user interface.

    After running the command, the function will wait until the
    corresponding application appears in the desktop and it is
    accessible through the at-spi.

    Finally it will return the Popen object that controls the process
    and the at-spi object that controls the accessible application.

    When, after a given timeout, it cannot find the application, it
    will stop waiting and return None instead of the at-spi object.

    Parameters
    ----------
    path : str | pathlib.Path
       The file path of the command

    name : str, optional
       The application's name that will be shown in the desktop.
       When no name is given, the function will forge one.

    Returns
    -------
    AbstractContextManager[SUT]
       A named tuple that can be used as a context manager.
       Popen object that is in charge of running the command in a new process.
       The Atspi object that represents the application in the desktop, or None
       if it couldn't find the application after a given timeout.


    :param path: str | pathlib.Path The file path of the command

    """
    
    name = name or f"{path}-test-{str(random.randint(0, 100000000))}"
    process = subprocess.Popen([path, '--name', name])
    app = _wait_for_app(name, timeout)
    return SUT(process= process, app= app, path= path)


def dump_desktop() -> None:
    """Prints the list of applications in desktop.

    *NB:* This function is not usefull for writing test. It maybe be
    useful for debuging purposes.

    """

    desktop = Atspi.get_desktop(0)
    for app in obj_children(desktop):
        print(app.get_name())


def _draw_branches(path: TreePath) -> str:
    return f"{draw_1}{draw_2}"


def dump_app(name: str) -> None:
    """Prints the tree of at-spi objects of an application.

    *NB:* This function is not usefull for writing test. It maybe be
    useful for debuging purposes.

    Parameters
    ----------
    name : str
        The name of the application.

    """
    
    desktop = Atspi.get_desktop(0)
    app = next(
        (app for app in obj_children(desktop) if app and app.get_name() == name),
        _MARK)
    if app == _MARK:
        print(f"App {name} not found in desktop")
        print(f"Try running {__file__} without args to get the list of apps")
        sys.exit(0)
    dump(app)


def dump(app: Atspi.Object) -> None:    
    for path, node in tree_walk(app):
        interfaces = node.get_interfaces()
        try:
            idx = interfaces.index('Action')
            n = node.get_n_actions()
            actions = [node.get_action_name(i) for i in range(n)]
            interfaces[idx] = f"Action({','.join(actions)})"
        except ValueError:
            pass
        role_name = node.get_role_name()
        name = node.get_name() or ""
        draw_1 = "".join("  " if nth_of.is_last() else "│ " for nth_of in path[:-1])
        draw_2 = "└ " if path[-1].is_last() else "├ "
        print(f"{draw_1}{draw_2}{role_name}('{name}') {interfaces}")


def main() -> None:
    """As a script calls dump functions.

    Usage:
   
    .. program:: atspi-dump
 
    Without args, dumps the list of applications running in the desktop

    .. option:: <name>

       Dumps the tree of at-spi objects of the application {name}
    """
    import sys
    
    if len(sys.argv) == 1:
        dump_desktop()
    else:
        dump_app(sys.argv[1])

    
if __name__ ==  '__main__':
    main()
