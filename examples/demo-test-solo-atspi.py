#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import random
import subprocess
import time
from typing import Any, Iterator, NamedTuple, Optional, Union

import gi
gi.require_version('Atspi', '2.0')
from gi.repository import Atspi


def tree_walk(obj: Atspi.Object) -> Iterator[Atspi.Object]:
    yield obj
    for i in range(obj.get_child_count()):
        yield from tree_walk(obj.get_child_at_index(i))


#-------------------------------------------------------------------------------
# Primer test
#-------------------------------------------------------------------------------

# GIVEN he lanzado la aplicación

## Ejecuto la aplicación en un proceso del S.O.
path = "./contador.py"
name = f"{path}-test-{str(random.randint(0, 100000000))}"
process = subprocess.Popen([path, '--name', name])
assert process is not None, f"No pude ejecuar la aplicación {path}"

## Espero hasta que la aplicación aparezca en el escritorio
## Pasado un timeout abandono la espera
desktop = Atspi.get_desktop(0)
start = time.time()
timeout = 5
app = None
while app is None and (time.time() - start) < timeout:
    gen = filter(lambda child: child and child.get_name() == name,
                 (desktop.get_child_at_index(i) for i in range(desktop.get_child_count())))
    app = next(gen, None)
    if app is None:
        time.sleep(0.6)

## Compruebo que todo fue bien
if app is None:
    process and process.kill()
    assert False, f"La aplicación {path} no aparece en el escritorio"

    
# THEN veo el texto "Has pulsado 0 veces"

## Busco el label
for obj in tree_walk(app):
    if (obj.get_role_name() == 'label' and
        obj.get_text(0, -1).startswith("Has pulsado")):
        break
else:
    assert False, "No pude encontrar la etiqueta 'Has pulsado ...'"

## Compruebo el contenido
assert obj.get_text(0, -1) == "Has pulsado 0 veces"


# TERMINO EL TEST DEJANDO TODO COMO ESTABA
process and process.kill()

#-------------------------------------------------------------------------------
# Segundo test
#-------------------------------------------------------------------------------

# GIVEN he lanzado la aplicación

## Ejecuto la aplicación en un proceso del S.O.
path = "./contador.py"
name = f"{path}-test-{str(random.randint(0, 100000000))}"
process = subprocess.Popen([path, '--name', name])
assert process is not None, f"No pude ejecuar la aplicación {path}"

## Espero hasta que la aplicación aparezca en el escritorio
## Pasado un timeout abandono la espera
desktop = Atspi.get_desktop(0)
start = time.time()
timeout = 5
app = None
while app is None and (time.time() - start) < timeout:
    gen = filter(lambda child: child and child.get_name() == name,
                 (desktop.get_child_at_index(i) for i in range(desktop.get_child_count())))
    app = next(gen, None)
    if app is None:
        time.sleep(0.6)

## Compruebo que todo fue bien
if app is None:
    process and process.kill()
    assert False, f"La aplicación {path} no aparece en el escritorio"

    
# WHEN pulso el botón 'Contar'

## Busco el botón
for obj in tree_walk(app):
    if (obj.get_role_name() == 'push button' and
        obj.get_name() == 'Contar'):
        break
else:
    assert False, "No pude encontrar el botón 'Contar'"

## Busco al acción 'click' en el botón
for idx in range(obj.get_n_actions()):
    if obj.get_action_name(idx) == 'click':
        break
else:
    assert False, "El botón 'Contar' no tiene una acción 'click'"    

## Lanzo la acción
obj.do_action(idx)


# THEN veo el texto "Has pulsado 1 vez"

## Busco el label
for obj in tree_walk(app):
    if (obj.get_role_name() == 'label' and
        obj.get_text(0, -1).startswith("Has pulsado")):
        break
else:
    assert False, "No pude encontrar la etiqueta 'Has pulsado ...'"

## Compruebo el contenido
assert obj.get_text(0, -1) == "Has pulsado 1 vez"


# TERMINO EL TEST DEJANDO TODO COMO ESTABA
process and process.kill()


#-------------------------------------------------------------------------------
# Tercer test
#-------------------------------------------------------------------------------

# GIVEN he lanzado la aplicación

## Ejecuto la aplicación en un proceso del S.O.
path = "./contador.py"
name = f"{path}-test-{str(random.randint(0, 100000000))}"
process = subprocess.Popen([path, '--name', name])
assert process is not None, f"No pude ejecuar la aplicación {path}"

## Espero hasta que la aplicación aparezca en el escritorio
## Pasado un timeout abandono la espera
desktop = Atspi.get_desktop(0)
start = time.time()
timeout = 5
app = None
while app is None and (time.time() - start) < timeout:
    gen = filter(lambda child: child and child.get_name() == name,
                 (desktop.get_child_at_index(i) for i in range(desktop.get_child_count())))
    app = next(gen, None)
    if app is None:
        time.sleep(0.6)

## Compruebo que todo fue bien
if app is None:
    process and process.kill()
    assert False, f"La aplicación {path} no aparece en el escritorio"

    
# WHEN pulso el botón 'Contar' cuatro veces

## Busco el botón
for obj in tree_walk(app):
    if (obj.get_role_name() == 'push button' and
        obj.get_name() == 'Contar'):
        break
else:
    assert False, "No pude encontrar el botón 'Contar'"

## Busco al acción 'click' en el botón
for idx in range(obj.get_n_actions()):
    if obj.get_action_name(idx) == 'click':
        break
else:
    assert False, "El botón 'Contar' no tiene una acción 'click'"    

## Lanzo la acción cuatro veces
obj.do_action(idx)
obj.do_action(idx)
obj.do_action(idx)
obj.do_action(idx)


# THEN veo el texto "Has pulsado 4 veces"

## Busco el label
for obj in tree_walk(app):
    if (obj.get_role_name() == 'label' and
        obj.get_text(0, -1).startswith("Has pulsado")):
        break
else:
    assert False, "No pude encontrar la etiqueta 'Has pulsado ...'"

## Compruebo el contenido
assert obj.get_text(0, -1) == "Has pulsado 4 veces"


# TERMINO EL TEST DEJANDO TODO COMO ESTABA
process and process.kill()



    
