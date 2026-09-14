# -*- encoding: utf-8 -*-

from hattori.base import BaseAnonymizer, faker
from tests.models import Person


class PersonAnonymizer(BaseAnonymizer):
    model = Person
    attributes = [
        # ('card_number', faker.credit_card_number),
        ('first_name', lambda instance, field: faker.first_name()),
        ('last_name', lambda instance, field: faker.last_name()),
        ('description', 'fix string'),
        # ('phone', faker.phone_number),
        # ('email', faker.email),
        # ('city', faker.city),
        # ('comment', faker.text),
        # ('description', 'fix string'),
        # ('code', faker.pystr),
    ]
