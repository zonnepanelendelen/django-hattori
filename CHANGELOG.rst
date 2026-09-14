==========
Change log
==========

0.1.0 (2018-05-10)
------------------

* Initial release.


0.1.1 (2018-06-11)
------------------

* ModuleNotFoundError is a new exception in Python 3.6, whereas earlier versions use ImportError.


0.1.2 (2018-07-27)
------------------

* Add progress bar that indicates the progress of the anonymization operation.


0.2.0 (2018-10-28)
------------------

* Added tests
* Small code refactors


0.3.0 (2026-09-14)
------------------

* Non-callable replacers (strings, ``None``, dicts, Django expressions) are written with a single ``UPDATE`` per model.
* Callable replacers stream rows with ``iterator()`` and write plain ``UPDATE ... WHERE pk = %s`` statements through ``executemany`` instead of ``bulk_update`` (whose ``CASE WHEN`` is quadratic in the batch size).
* The primary key is captured before replacers run, so a primary key column can itself be replaced.
* ``get_allowed_value`` no longer fails when a replacer returns ``None`` for a field with ``max_length``.
* Dropped the ``six`` dependency.
