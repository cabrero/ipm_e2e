# API

Se trata de que el api se parezca lo más posible a cómo escribimos las
cosas en el diseño de la interface.
Ya sea pseudo-lenguaje natural o whatever
// TODO: mirar lo del userjourney, y otras opciones para especificar el
// comportamiento en el diseño

EL lenguaje es OO y faltan muchas construcciones típicas de un lenguaje
funcional.
Al final es mejor que el api tenga aspectos OO. Pero siempre de tal forma
que sea trasladable a un lenguaje funcional.
P.e. que el method chaining se puede reconvertir en un pipe operator

```
tables = objects_in(app, ...)

do('click').on_all(objects_in(tables, ...))

expect(objects_in(tables, ...)).to_show(...)

do, verify = perform_below(app)
do('click').on(...)
verify.on(...).that_shows(...)


objs = perform_below(app, ...)
objs = perform_below(objs(...), ...)
objs = perform_below([...], ...)

# objs :: ... -> list[AtspiObject]

do('click').on_all(objs(...))
do('click').on_first(objs(...))

do('click').on(objs(...))    // TODO: conseguir un nombre que refleje mejor que la secuencia de objs tiene que tener un único elemento

verify(objs(...)).that_shows(...)
verify_any(objs(...)).that_shows(...)
verify_first(objs(...)).that_shows(...)

verify_that_shows(...).on_all(objs(...))
verify_that_shows(...).on_any(objs(...))

on_all(objs(...)).verify_that_shows(...)


expect(objs(...)).to_show(...)

```

```
expect(objs(...), to_show(...))

expect
|> objs(...)
|> to_show(...)


app
|> on(...)
|> do('click')

app
|> on(...)
|> verify(that_shows(...))

do('click', on(app, ...))
verify(on(app, ...), that_shows(...))


do('click')
|> on(...)

verify
|> on(...)
|> that_shows(...)

// OR

verify
|> that_shows(...)
|> on(...)

verify_that_shows(...)
|> on_all(objs(...))

objs(...)
|> on_all
|> verify_that_shows(...)
```
