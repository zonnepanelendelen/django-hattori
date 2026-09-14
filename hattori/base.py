# -*- coding: utf-8 -*-

import logging

from django.conf import settings
from django.db import connections, transaction
from faker import Faker
from tqdm import tqdm

from hattori.constants import DEFAULT_CHUNK_SIZE

logger = logging.getLogger(__name__)

try:
    faker = Faker(settings.LANGUAGE_CODE)
except AttributeError:
    faker = Faker()


class BaseAnonymizer:
    """
    Replaces the values of ``attributes`` on every row of ``get_query_set()``.

    ``attributes`` is a list of ``(field_name, replacer)`` pairs. A replacer is either

    - a callable ``replacer(model_instance, field_name)`` evaluated per row, or
    - anything else (a string, ``None``, a dict for a JSONField, a Django expression),
      written as-is with one ``UPDATE`` for the whole queryset.

    Constant replacers are applied first, in a single ``UPDATE``. Callable replacers are
    then evaluated in list order on rows streamed from the database and written as plain
    ``UPDATE ... WHERE pk = %s`` statements through ``executemany``. Both steps run in one
    transaction.

    Because constants are written before the callable pass, a callable that reads a field
    listed as a constant sees the replaced value, and a ``get_query_set()`` that filters on
    a constant-replaced field is re-evaluated against the replaced values.
    """

    model = None
    attributes = None

    def __init__(self):
        if not self.model or not self.attributes:
            logger.info('ERROR: Your anonymizer is missing the model or attributes definition!')
            exit(1)

    def get_query_set(self):
        """
        You can override this in your Anonymizer.
        :return: QuerySet
        """
        return self.model.objects.all()

    def run(self, batch_size=DEFAULT_CHUNK_SIZE):
        batch_size = batch_size or DEFAULT_CHUNK_SIZE
        constants = {field_name: value for field_name, value in self.attributes if not callable(value)}
        callables = [(field_name, value) for field_name, value in self.attributes if callable(value)]
        queryset = self.get_query_set()
        with transaction.atomic(using=queryset.db):
            count_instances = queryset.update(**constants) if constants else 0
            if callables:
                count_instances = self._run_callables(queryset, callables, batch_size)
        return len(self.attributes), count_instances, count_instances * len(self.attributes)

    def _run_callables(self, queryset, callables, batch_size):
        connection = connections[queryset.db]
        quote = connection.ops.quote_name
        meta = queryset.model._meta
        fields = [meta.get_field(field_name) for field_name, _ in callables]
        set_clause = ', '.join('{} = %s'.format(quote(field.column)) for field in fields)
        sql = 'UPDATE {} SET {} WHERE {} = %s'.format(quote(meta.db_table), set_clause, quote(meta.pk.column))

        count_instances = 0
        batch = []
        progress_bar = tqdm(desc='Processing', total=queryset.count())
        with connection.cursor() as cursor:
            for model_instance in queryset.iterator(chunk_size=batch_size):
                # captured before the replacers run: the pk column itself may be a replaced field
                pk = model_instance.pk
                for field_name, replacer in callables:
                    setattr(model_instance, field_name, self.get_allowed_value(replacer, model_instance, field_name))
                batch.append(
                    tuple(field.get_db_prep_save(getattr(model_instance, field.name), connection) for field in fields)
                    + (pk,)
                )
                count_instances += 1
                progress_bar.update(1)
                if len(batch) >= batch_size:
                    cursor.executemany(sql, batch)
                    batch = []
            if batch:
                cursor.executemany(sql, batch)
        progress_bar.close()
        return count_instances

    @staticmethod
    def get_allowed_value(replacer, model_instance, field_name):
        retval = replacer(model_instance, field_name)
        max_length = model_instance._meta.get_field(field_name).max_length
        if max_length and retval is not None:
            retval = retval[:max_length]
        return retval
