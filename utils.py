#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim: set ts=4 sw=4 et sts=4 ai:

def assert_eq(a, b):
    if isinstance(a, ctypes.Array):
        assert_eq(a._type_, b._type_)
        assert_eq(a._length_, b._length_)
        assert_eq(a[:], b[:])
        return

    assert a == b, "%s (%r) != %s (%r)" % (a, a, b, b)

def return_fill_buffer(b, value):
    return (b._type_ * b._length_)(*([value] * b._length_))

def print_struct(s, indent=''):
    for field_name, field_type in s._fields_:
        field_detail = getattr(s.__class__, field_name)
        field_value = getattr(s, field_name)
        print(indent, field_name, end=': ', sep='')
        if isinstance(field_value, ctypes.Structure):
            print()
            print_struct(field_value, indent=indent+'    ')
        elif isinstance(field_value, ctypes.Array):
            print(field_value._length_, field_value[:])
        elif isinstance(field_value, bytes):
            print(repr(field_value))
        else:
            print(hex(field_value))

