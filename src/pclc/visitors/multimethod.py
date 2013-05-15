#
# Copyright Capita Translation and Interpreting 2013
#
# This file is part of Pipeline Creation Language (PCL).
# 
# Pipeline Creation Language (PCL) is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# Pipeline Creation Language (PCL) is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with Pipeline Creation Language (PCL).  If not, see <http://www.gnu.org/licenses/>.
#
#
# Multi-method decorator
#
registry = {}
class_registry = {}

def __make_key(klass, types):
    keys = [klass]
    keys.extend(types)
    return tuple(keys)

#
# Decorate methods with this, whose arguments are the types
#
def multimethod(*types):
    def decorator(method):
        global class_registry
        class_registry[types] = method
        def wrapper(target_obj, *args, **kwargs):
            global registry
            target_method = None
            for klass in target_obj.__class__.__mro__:
                keys = __make_key(klass, [arg.__class__ for arg in args])
                if registry.has_key(keys):
                    target_method = registry[keys]
                    return target_method(target_obj, *args, **kwargs)
            if not target_method:
                raise LookupError("Method not registered on class %s for type %s" % \
                                  (type(target_obj), [arg.__class__ for arg in args]))
        return wrapper
    return decorator

#
# Decorate the class whose methods are decorated with the multi-method decorator
#
def multimethodclass(klass):
    global class_registry
    registrations = {__make_key(klass, types) : class_registry[types] for types in class_registry}
    registry.update(registrations)
    class_registry = {}
    return klass
