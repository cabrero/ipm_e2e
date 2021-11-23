#!/usr/bin/env python3
from __future__ import annotations

import re

from ipm import e2e


from pathlib import Path
import random
import subprocess
import time
from typing import Any, Iterator, NamedTuple, Optional, Union

#-------------------------------------------------------------------------------
# Primer test
#-------------------------------------------------------------------------------

# GIVEN he lanzado la aplicación

with e2e.run("./contador.py") as sut:
    # si todo fue bien
    # THEN veo el texto "Has pulsado 0 veces"
    e2e.expect_any(e2e.objects_in(sut.app, role= "label")).to_show(text="Has pulsado 0 veces")

# el context manager deja todo como estaba


#-------------------------------------------------------------------------------
# Primer test (sin el context manager)
#-------------------------------------------------------------------------------


# GIVEN he lanzado la aplicación

sut = e2e.run("./contador.py")
## Compruebo que todo fue bien
if sut.app is None:
    sut.process and sut.process.kill()
    assert False, f"La aplicación {sut.path} no aparece en el escritorio"

try:    
    # THEN veo el texto "Has pulsado 0 veces"

    e2e.expect_any(e2e.objects_in(sut.app, role= "label")).to_show(text="Has pulsado 0 veces")

finally:
    # TERMINO EL TEST DEJANDO TODO COMO ESTABA
    sut.process and sut.process.kill()

    
#-------------------------------------------------------------------------------
# Segundo test
#-------------------------------------------------------------------------------

# GIVEN he lanzado la aplicación
with e2e.run("./contador.py") as sut:
    # WHEN pulso el botón 'Contar'
    e2e.do('click').on(e2e.objects_in(sut.app, role= 'push button', name= 'Contar'))

    # THEN veo el texto "Has pulsado 1 vez"
    e2e.expect_any(e2e.objects_in(sut.app, role= "label")).to_show(text="Has pulsado 1 vez")


#-------------------------------------------------------------------------------
# Tercer test
#-------------------------------------------------------------------------------

# GIVEN he lanzado la aplicación
with e2e.run("./contador.py") as sut:
    # WHEN pulso el botón 'Contar' cuatro veces
    buttons = e2e.objects_in(sut.app, role= 'push button', name= 'Contar')
    e2e.do('click').on(buttons)
    e2e.do('click').on(buttons)
    e2e.do('click').on(buttons)
    e2e.do('click').on(buttons)

    # THEN veo el texto "Has pulsado 4 veces"
    e2e.expect_all(
        e2e.objects_in(sut.app, role= "label", text= re.compile('^Has pulsado.*'))
    ).to_show(
        text="Has pulsado 4 veces"
    )



