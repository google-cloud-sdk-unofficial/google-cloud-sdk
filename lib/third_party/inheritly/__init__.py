# Copyright 2014 Google Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Various decorators that document and restrict inheritance.

Provides two decorators:

@override
@final

TODO(user): @interface, @supports_multiple_inheritance. @final already
says "we don't support inheritance, not even single inheritance", so I don't
think we need @supports_single_inheritance; letting that be implied by absence
of @final is probably good enough? Actually, I wish @final were the default.
Inheritance should only be supported if author opts in, i.e. class was
specifically _designed_ for inheritance.

Their meaning is analogous to Java namesakes. See docstrings for details.

Enforcement is performed by Meta. You can use the decorators without it, but in
that case, the decorators only serve as documentation.


Decorator Compatibility
=======================

@override and @final must be listed before/applied after any decorators that
do not return the original object. A notable example of such a decorator is
property. E.g. the following won't do what you probably wanted:

  class PetStore(object):

    __metaclass__ = inheritly.Meta

    @property
    @inheritly.final
    def animals(self):
      return ['dead parrot']

This won't blow up. Instead, people who attempt to override animals will be able
to do so, even though you didn't want them to. Instead, @final must come before
@property.

Another example: @final and @override DO in fact return the original object,
so they can be used together.

abc Standard Library Module
---------------------------

This subsumes abc, and is compatible with it. This is achieved by inheritly.Meta
inheriting from abc.ABCMeta. Furthermore, inheritly "re-exports" abc's
abstractmethod and abstractproperty.

inheritly.Meta inheriting from abc.ABCMeta means that a child class can use
the former even if a parent class uses the latter. If you want to use inheritly
in addition to yet another metaclass, you can do the following:

<solution>
class _UnionMeta(inheritly.Meta, whatever.Meta):
  pass

class Widget(object):

  __metaclass__ = _UnionMeta
</solution>

The only catch is that super must be used consistently throughout the
inheritance DAG. Otherwise, not all of the __init__ will get called, which will
result in you being a sad panda. Multiple inheritance FTW?? This isn't unique to
metaclasses: any time you want to use multiple inheritance, all classes involved
must support it by using super. If it doesn't say so on the box, I would assume
that multiple inheritance is not supported.
"""

__author__ = ['danielwong@google.com']

import abc
import inspect
import threading
import types
import warnings

# Some methods can't have @override checks enforced because they
# are special in some way.
# __init__ and __call__ are special because they always technically
# exist by virtue of existing on `object`, which means they look
# like a no-arg functions, so, if we tried to enforce them as such,
# classes wouldn't be able to implement a useful version of them throughout
# the class hierarchy.
_SKIP_ALL_OVERRIDE_CHECKS = set(['__init__', '__new__'])


class Error(UserWarning):
  """Some property (e.g. that a method overrides another) was not met.

  This is a warning (see warnings module in the standard library), but it is
  set to generate an exception by default. As per warnings in general, the
  behavior of a warning can be configured via the warnings module.

  This is raised when offending class is defined, as opposed to when problematic
  parts of the class are used. This is a nice feature, because class definitions
  generally occur when a program is first starting up, instead of after things
  have gotten rolling.
  """


warnings.simplefilter('error', Error)


class NothingToOverride(Error):
  """Method claims to override something, but does not."""


class OverridesWithoutDecorator(Error):
  """Method overrides another without @override decorator.

  This is the dual of NothingToOverride. Taken together, Meta requires that
  @override was applied to M iff M overrides something. Therefore, existence
  of @override can cause an exception (NothingToOverride), as can absence
  of @override (manifests as OverridesWithoutDecorator).
  """


class IncompatibleOverride(Error):
  """Overriding method is not compatible with overridden method.

  class P(object):

    __metaclass__ = inheritly.Meta

    def foo(self, a): pass

  class C(object):

    # Danger, Will Robinson!
    @inheritly.override
    def foo(self): pass

  Suppose you have isinstance(p, P). Then, you should be able to do p.foo(1)
  per Liskov Substitution Principle. p could be a C, in which case, p.foo(1)
  would blow up. This warns of that.
  """


class InheritsFromFinalClass(Error):
  """One of the bases of a class is marked @final."""


class OverridesFinalMethod(Error):
  """A method overrides another method (in a base) that is marked @final."""


class FinalClassMembersAreAmbiguous(Error):
  """You are not allowed to mark classes in other classes as @final.

  This is inheritly ambiguous. Future additions to this library may provide ways
  to mark a class in another class as being one or both of the following:

    1. Does not allow subclasses.
    2. Not a member of the containing class that can be overridden by subclass
       of containing class.

  For now, there is no way to indicate which of these (or both) is intended.
  Suggested work around: document in docstring. This seems like an exceedingly
  rare use case. Therefore, a better solution might never be provided.
  """


class Meta(abc.ABCMeta):
  """Metaclass taht enforces inheritly decorators.

  If a parent does not already use this as its metaclass, a child can do so in
  order to gain enforcement. Generally, it is more convenient to use this in
  the parent, because children then do not need to do it themselves (because
  children inherit metaclasses per the normal metaclass inheritance mechanism).
  """

  def __init__(cls, class_name, bases, dct):
    """Metaclass's initializer for the class being defined.

    Args:
      class_name: The base name of the class being defined.
      bases: A tuple of the base classes of `cls`.
      dct: A dictionary of attributes and values that are intended to
        beceome the class's __dict__ values.

    Raises:
      Error: Generally speaking, a more specific subclass will be raised.
        See docstrings thereof.
    """
    args = class_name, bases, dct
    cls.__enforce_final_classes(bases)
    cls.__enforce_final_methods(*args)
    cls.__enforce_override(*args)

    # Everything checks out. Let normal class initialization proceed.
    super(Meta, cls).__init__(*args)

  def __enforce_override(cls, class_name, bases, dct):
    for name, value in dct.iteritems():
      # See the docs on this constant for why some names are skipped.
      if name in _SKIP_ALL_OVERRIDE_CHECKS:
        continue

      if not _registry.has_override(value):
        # One could argue for a bigger or smaller space of things to be
        # elligible for "does not override" checking. But since the intention of
        # @inheritly.override is to be used as a decorator (as opposed to
        # an attribute like foo = inheritly.override('bar')), seems reasonable
        # that non-callables are not elligible.
        if callable(value):
          cls.__enforce_does_not_override(name, bases)
        continue

      occluded = [base for base in bases if getattr(base, name, None)]
      if not occluded:
        warnings.warn('%s says it overrides something in %s, but not found '
                      'in any base class.' % (name, class_name),
                      NothingToOverride)

      if not isinstance(value, types.FunctionType):
        for base in occluded:
          base_type = type(getattr(base, name))
          types_are_compatible = (isinstance(value, base_type)
                                  # Allow anything to override abstractproperty,
                                  # because abc allows anything to fulfil.
                                  or base_type == abc.abstractproperty)
          if not types_are_compatible:
            warnings.warn('%s in %s is a %s, yet member (with the same name) '
                          'in %s is a %s.'
                          % (name, class_name, type(value).__name__,
                             base.__name__, type(getattr(base, name)).__name__),
                          IncompatibleOverride)
        continue

      for base in occluded:
        preexisting = getattr(base, name)
        # More than just types.MethodType needs to be checked to handle
        # default implementations of methods inherited from the base `object`
        # class. Most of the methods on `object` aren't normal methods
        # because they're implemented in C or as descriptors.
        # Without these additional checks, methods like __call__, __str__,
        # __repr__, and __hash__ can't be overridden.
        if (not isinstance(preexisting, types.MethodType) and
            # object.__call__ matches this condition
            not getattr(preexisting, '__self__', None) and
            # object.{__str__, __repr__, __hash__} match this
            not inspect.ismethoddescriptor(preexisting)):
          warnings.warn('%s in %s is a function, yet member (with the same '
                        'name) in type %r is instead a(n) %s.'
                        % (name, class_name, base.__name__,
                           type(preexisting).__name__),
                        IncompatibleOverride)
        if not can_override(value, preexisting):
          # TODO(user): Provide more details about why override is not
          # valid.
          warnings.warn('%s in %s cannot override method in %s.'
                        % (name, class_name, base.__name__),
                        IncompatibleOverride)
        # Add the base docstring if the override doesn't have one.
        if not value.__doc__ and preexisting.__doc__:
          value.__doc__ = preexisting.__doc__

  # TODO(user): Provide a way to opt out of this behavior so that existing
  # base classes can use Meta without breaking all subclasses (that override).
  # Can this already be done by selectively not turning warnings into
  # exceptions? lol i dunno; I'm not that familiar warnings.
  def __enforce_does_not_override(cls, name, bases):
    """Emits a OverridesWithoutDecorator warning if name is not in bases.

    Args:
      name - (string) Name that bases should not have.
      bases - List of base classes.
    """
    for base in bases:
      if (getattr(base, name, None) and
          # The purpose of this is to allow people to "override" __call__.
          # The reason they would be blocked without this is that `object`
          # has a __call__ method, but it is, effectively, nonfunctional.
          # NOTE: we have to use == instead of "is" because object.__call__
          # is actually a descriptor and returns a new value every access.
          getattr(base, name) != object.__call__):
        warnings.warn('%s in %s overrides a member (with the same name) in %s '
                      'without explicitly saying so using @inheritly.override '
                      'decorator' % (name, cls.__name__, base.__name__),
                      OverridesWithoutDecorator)

  def __enforce_final_classes(cls, bases):
    for base in bases:
      if _registry.has_final(base):
        warnings.warn('%s is final, yet used as a base class.' % base.__name__,
                      InheritsFromFinalClass)

  def __enforce_final_methods(cls, class_name, bases, dct):
    for attr_name, attr_value in dct.iteritems():
      if _registry.has_final(attr_value) and isinstance(attr_value, type):
        # TODO(user): There might come a day when someone actually wants
        # to put @final on an inner class. When that day comes, we might decide
        # that it is worthwhile to provide @finalclass and @finalmethod.
        # However, that seems like an exceedingly rare use case. Also, it's a
        # use case that has never been served anyway, so we might just decide
        # to never support it.
        warnings.warn(
            '%s in %s is a class that is marked as @inheritly.final.'
            % (attr_name, class_name),
            FinalClassMembersAreAmbiguous)

      for base in bases:
        overridden_member = getattr(base, attr_name, None)
        if not overridden_member:
          continue
        if _registry.has_final(overridden_member):
          warnings.warn('%s overrides %s, but that method is marked as @final '
                        'in %s.' %
                        (class_name, attr_name, base.__name__),
                        OverridesFinalMethod)


def override(f):
  """Annotates that a method overrides a method in a super class.

  <example case="happy">
  import inheritly


  class Parent(object):

    # This is needed for enforcement. Without this, @override is purely
    # documentation.
    __metaclass__ = inheritly.Meta

    def override_me(self):
      "Base class docstring."
      print 'Parent'


  class WellFormedChild(Parent):

    @override  # Seems legit. No splosions.
    def override_me(self):
      print 'Child'

  # Prints "Base class docstring."  (@override injects the parent docstring
  # if the override doesn't have one).
  print WellFormedChild.override_me.__doc__
  </example>

  There are a couple of ways application code might mess up:

    1. The decorator is applied to some method in a subclass, but the method
       does not actually override. This is usually due to a misspelling of the
       method name.
    2. The decorator is NOT applied to some method in a subclass, yet it does
       override. This could be an unintentional override. If the override was
       intentional, then it is simply a matter of putting @inheritly.override
       on the method.

  Continuing with previous example, here's what those problems would look like:

  <example>
  # This class statement raises NothingToOveride.
  class FailedChild(Parent):

    @override  # Parent has no method with this name -> Kaboom!
    def misspelling_of_override_me(self):
      print 'Fail!'

  # This class raises OverridesWithoutDecorator.
  class MoarFail(Parent):

    # The problem is that this overrides, but does not say so using decorator.
    def override_me(self):
      pass
  </example>

  Compatibility Checking
  ======================

  If you attempt to override A with B, but B does not support all the calls that
  A supports, a inheritly.IncompatibleOverride warning is generated (and such
  warnings turn into exceptions by default).

  By contrast, inheritly.NothingToOverride warning is generated if the method
  doesn't contrast anything at all.

  As described in the docstring in inheritly.Error, these warnings are turned
  into exceptions by default.

  Args:
    f: The method that is overriding one from a super class.

  Returns:
    The decorated method. Meta handles enforcement.
  """
  # TODO(user): What if f is shared among different classes? It should
  # only be @override in those where @override is used. While the current
  # implementation is not ideal, sharing is uncommon. In particular, it never
  # occurs if this is used as a decorator, as opposed to being called
  # directly.
  _registry.add_override(f)
  return f


def final(class_or_method):
  """Annotates that a class or method is final.

  A final class cannot be inherited from.

  A final method cannot be overridden.

  <example>
  import inheritly


  class Parent(object):

    __metaclass__ = inheritly.Meta

    def use_final_method(self):
      '''Implemented in terms of final_method

      Thus, it is a mistake to override final_method
      '''
      return self.final_method

    @inheritly.final
    def final_method(self):
      pass

  class Child(Parent):

    # Kaboom! Even though this says that it is intentionally overriding, it's
    # not allowed to, because Parent says so.
    @inheritly.override
    def final_method(self)
      pass

  @inheritly.final
  class DoNotInheritFromMe(object):

    __metaclass__ = inheritly.Meta

    def calculate_pi(self):
      return 3.14

  # Kaboom!
  class WantonDestruction(DoNotInheritFromMe):
    pass
  </example>

  Args:
    class_or_method: A class, or method. Technically, by "method", we mean
      thing that gets wrapped by boundmethod or unboundmethod, which is usually
      a function.

  Returns:
    The decorated class or method. Meta handles enforcement.
  """
  _registry.add_final(class_or_method)
  return class_or_method


abstractmethod = abc.abstractmethod  # pylint: disable=invalid-name
abstractproperty = abc.abstractproperty  # pylint: disable=invalid-name


# TODO(user): Compare function annotations (for Python 3).
def can_override(overrider_function, reference_function):
  """Returns whether overrider can override reference.

  In other words, can every way of calling reference also be used with
  overrider? This is a somewhat tricky question to answer, because there are
  couple ways to pass an argument:

    1. Positionally.
    2. By name.

  Furthermore, one must consider *args, and **kwargs.

  Args:
    overrider_function: A function.
    reference_function: Another function. All valid calls to this must be valid
      calls to overrider_function in order for True to be returned.

  Returns:
    A bool.
  """
  overrider = inspect.getargspec(overrider_function)
  try:
    reference = inspect.getargspec(reference_function)
  except TypeError:
    # If the reference function is a builtin (such as when first overriding
    # __str__, __hash__, and others that exist on `object`), then getargspec()
    # may not be able to determine the signature. Just trust that its ok.
    return True

  # If reference takes **kwargs, so must overrider.
  if reference.keywords and not overrider.keywords:
    return False

  # If reference takes *wargs, so must overrider.
  if reference.varargs and not overrider.varargs:
    return False

  # If overrider doesn't support passing by arbitrary name, then its parameter
  # names must be a superset of those that reference supports.
  if (not overrider.keywords and
      not set(overrider.args).issuperset(reference.args)):
    return False

  # If overrider doesn't support arbitrarily many positional arguments, then
  # it must support at least as many as reference.
  if not overrider.varargs and len(overrider.args) < len(reference.args):
    return False

  def required(argspec):
    if argspec.defaults:
      return argspec.args[:-len(argspec.defaults)]
    return argspec.args
  # overrider cannot require more arguments than reference.
  if len(required(overrider)) > len(required(reference)):
    return False

  # Overriders first len(reference.args) parameters must have the same names
  # and be in the same order as those of reference (unless overrider takes
  # **kwargs).
  #
  # Needing to have the same names is pretty easy to understand (any parameter
  # can be passed by name). To understand the importance of order, consider
  # this race:
  #
  #   def reference(foo, bar, baz=None): pass
  #   def overrider(bar, foo, baz=None, alpha=1): pass
  #   reference(1, bar='bar')  # Ok
  #   # Kaboom! Two values for bar. Also, no value for foo, which is required.
  #   overrider(1, bar='bar')
  if (not overrider.keywords and
      overrider.args[:len(reference.args)] != reference.args):
    return False

  return True


# This is needed, because some types (most notably, property) do not allow
# ad-hoc attributes, which would be the other way of recording whether something
# had @override or @final (or whatever) applied to it.
class _Registry(object):
  """Keeps track of what decorators have been applied and to whom.

  For each decorator supplied by this module (not stolen from abc), there are
  two methods:
    1. add_${decorator_name} - Called by decorators themselves.
    2. has_${decorator_name} - Called by Meta to determine whether decorator
       was applied.
  """

  def __init__(self):
    # TODO(user): Use of set imposes an undesirable property that
    # decorators can only be applied to hashable objects, and leaks
    # implementation details. This is fine for use cases that are expected to
    # make up a vast majority, but we may want to add support for more types
    # later. At this point, the only solutions I can think of would either be
    # complicated or less efficient. Considering that such use-cases are
    # expected to be in a very small minority, this seems fine for now, but we
    # can probably make implementation changes without impacting existing users
    # if we later find such cases are important.
    self._overrides = set()
    self._finals = set()
    # In case an app defines classes concurrently. That seems pretty degenerate,
    # but we must defend against such shinanigans, because we can and it would
    # be surprising if we did not. This is what justifies this whole class.
    # Otherwise, we could just use bare sets.
    #
    # We could have separate locks for each of the above attributes, but for
    # simplicity, we just have one. Making life better for apps that do
    # concurrent class definition by reducing contention on this is a non-goal.
    self._lock = threading.Lock()

  def add_override(self, obj):
    with self._lock:
      self._overrides.add(obj)

  def add_final(self, obj):
    with self._lock:
      self._finals.add(obj)

  def has_override(self, obj):
    with self._lock:
      return obj in self._overrides

  def has_final(self, obj):
    # Not sure whether I would call this a hack, but the reason this is needed
    # here, but not in has_override is that @final is enforced when subclass is
    # defined; whereas, @override is enforced in class where it is used.
    # Because of this difference, has_override sees raw function; whereas,
    # has_final sees function wrapped as method. It's a weird asymetry, but is
    # apparently unavoidable.
    f = obj.im_func if isinstance(obj, types.MethodType) else obj
    with self._lock:
      return f in self._finals


_registry = _Registry()
