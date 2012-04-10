#!/usr/bin/env python
# Credit to jamuspsi
import pickle
import traceback
from weakref import WeakValueDictionary, WeakSet
import inspect
import sys

# Warning, heavy voodoo in this file.  Using metaclasses.
# This is all to support the live-reloading effect for the system, which
# almost certainly shouldn't be done.


def diagnose(i):
    if not isinstance(i, type):
        i = i.__class__
    mro = [getattr(m, 'ICEKLSID', None) for m in i.__mro__]
    return "class %s(%r)%r" % (i, getattr(i, 'ICEKLSID', None), mro)


class IceMeta(type):
    id_index = WeakValueDictionary()

    __Next_Ice_Id__ = 0
    infile = None
    infile = open('next_ice_id.txt')
    __Next_Ice_Id__ = int(infile.readline().strip())
    infile.close()

    kls_id = 0

    del infile  # pollution.

    def __new__(cls, name, bases, dct):
        kls = super(IceMeta, cls).__new__(cls, name, bases, dct)

        kls.ICEKLSID = IceMeta.kls_id
        IceMeta.kls_id += 1

        # Determine if an upgrade is necessary:

        # this is very probably the scope of the interpreter evaluating the
        # module file
        frame = inspect.currentframe().f_back
        kls.__instanceset__ = WeakSet()

        for scope in [frame.f_locals, frame.f_globals]:
            old_class = scope.get(name, None)
            if old_class:
                # This class is about to be overwritten.
                old_class = scope[name]

                # Upgrade the old instances to the new ones:
                for instance in list(old_class.__instanceset__):
                    instance.__class__ = kls
                    kls.__instanceset__.add(instance)

                # The old class has no instances now, because I just upgraded
                # them all.
                old_class.__instanceset__ = WeakSet()

                # Monkey-patch all the subclasses.
                for subcls in old_class.__subclasses__():
                    newbases = ()
                    for base in subcls.__bases__:
                        newbases += (kls if base is old_class else base,)
                    subcls.__bases__ = newbases

                # This may cause problems.  Be prepared to remove it.
                # Patch all global imports of the old class with this one.
                for module in sys.modules.values():
                    patch = dict()
                    if not module:
                        continue
                    for k, v in module.__dict__.iteritems():
                        if v is old_class:
                            patch[k] = kls

                    for k, v in patch.iteritems():
                        setattr(module, k, v)

                break  # we performed the upgrade, don't change anything else.
        return kls

    def __call__(self, *args, **kwargs):
        instance = super(IceMeta, self).__call__(*args, **kwargs)
        IceMeta.RegisterInstance(instance)
        return instance

    @staticmethod
    def RegisterInstance(instance):
        instance.__class__.__instanceset__.add(instance)

        if not hasattr(instance, 'ICEID'):
            instance.ICEID = IceMeta.next_id()

        if IceMeta.id_index.get(instance.ICEID, None) not in (instance, None):
            raise Exception("Duplicate ICEID found!  %d %r %r" % (
                instance.ICEID, IceMeta.id_index[instance.ICEID], instance))

        IceMeta.id_index[instance.ICEID] = instance

    def UnregisterInstance(instance):
        instance.__class__.__instanceset__.remove(instance)
        # this weak reference cannot have expired because it's holding instance
        # And I'm protecting the setter in RegisterInstance.
        # This is almost certainly extremely non-typesafe.
        del IceMeta.id_index[instance.ICEID]

    @staticmethod
    def next_id():
        res = IceMeta.__Next_Ice_Id__

        IceMeta.__Next_Ice_Id__ += 1

        outfile = open('next_ice_id.txt', 'w')
        outfile.write("%d\n" % IceMeta.__Next_Ice_Id__)
        outfile.close()
        return res


class Ice(object):
    __metaclass__ = IceMeta
    statekeys = ['ICEID']

    def __init__(self, *args, **kwargs):
        pass

    # Object registration/deregistration.  This is crazy but it should work.

    def freeze(self):
        return pickle.dumps(self)

    def freeze_to(self, filename):
        dump = self.freeze()
        fh = open(filename, 'w')
        fh.write(dump)
        fh.close()

    @staticmethod
    def sublimate(*objs_or_classes):
        # The trick to this is to reload the class and all later classes but
        # not the earlier ones.  This is going to be horrifying.
        classes = []
        for i in objs_or_classes:
            if not isinstance(i, type):
                i = i.__class__
            if not issubclass(i, Ice):
                # Can't do this.
                raise Exception("Cannot sublimate class %r because it is \
                                not an Ice.")

            classes.append(i)

            # Only walk down, not up.  If thing gets edited, pass in Thing or
            # an instance of Thing, not an instance of a subclass of Thing.
            # Add the subclasses of this, which should be in the index if
            # they're loaded.
            classes += list(i.__subclasses__())
            # (If they're not, they don't need sublimating)

        # Remove duplicates.
        classes = list(set(classes))

        # Take every module.
        modnames = [c.__module__ for c in classes]
        modnames = list(set(modnames))

        import sys
        modules = [sys.modules.get(mn, None) for mn in modnames]

        modules = filter(None, modules)

        # IceMeta will reindex the classes, patch their subclasses, and
        # upgrade their instances.  Magically.  Using anything that's not an
        # Ice is extremely ill-advised, and any classes that get reloaded
        # that are not Ice will not have anything fixed (probably not a problem,
        # unless you try to pickle the old ones.)

        for mod in modules:
            reload(mod)

        return

    @staticmethod
    def thaw(dump):
        return pickle.loads(dump)

    @staticmethod
    def thaw_from(filename):
        fh = open(filename, 'r')
        obj = pickle.load(fh)
        fh.close()
        return obj

    def __getstate__(self):
        if not hasattr(self, 'IceErr'):
            self.IceErr = []

        self.pre_freeze()

        keys = getattr(self.__class__, "__all_statekeys__", None)
        if keys is None:
            keys = []
            for kls in self.__class__.__mro__:
                some = getattr(kls, "statekeys", None)
                if some:
                    keys += list(some)
            self.__class__.__all_statekeys__ = keys

        state = dict()
        for k in keys:
            attr = k
            if k[-1] == "?":
                attr = k[:-1]

                obj = getattr(self, attr, None)
                if callable(obj):
                    obj = obj()
                desc = str(obj)

                try:
                    dump = pickle.dumps(obj)
                except:
                    dump = pickle.dumps(None)
                    self.IceErr.append(("Could not pickle WeakFreeze: %r:%r" % (k, desc), traceback.format_exc()))
                val = (desc, dump)

            else:
                # If the state to store is a callable, store its result instead.
                # It'll get passed back to that same callable later.
                val = getattr(self, attr, None)
                if callable(val):
                    val = val()

            state[k] = val
        return state

    def __setstate__(self, state):
        if not hasattr(self, 'IceErr'):
            self.IceErr = []

        for k, v in state.iteritems():
            if k[-1] == "?":
                weak = k
                k = k[:-1]
                # v will be desc, dump
                desc, dump = v

                try:
                    v = pickle.loads(dump)
                    current = getattr(self, k, None)
                    if callable(current):
                        current(state=v)
                except:
                    self.IceErr.append(("Could not unpickle WeakFreeze: %r:%r" % (weak, desc), traceback.format_exc()))
                    self.__dict__[k] = None

            else:
                current = getattr(self, k, None)
                if callable(current):
                    # Rather than assign into the current, I'm
                    # going to pass the value into current
                    current(state=v)

                self.__dict__[k] = v

        self.post_thaw()

    def pre_freeze(self):
        pass

    def post_thaw(self):
        IceMeta.RegisterInstance(self)
        pass

    def disintegrate_ICE(self):
        # decouple everything into some state that needs to be saved
        # Only separate from what you absolutely must- particularly things "up" the chain or sideways
        # Children objects which exist inside of this or dependant on this can be decoupled themselves.

        # this should also deregister the object from any trackers.
        # -Exception: children which cannot be saved with this object must be separated and reintegrated.
        # In the case when a reload is being done, if the sublimation is affecting more than one object,
        # each should separate independantly, even from each other, and no ordering should be preserved.

        # returns an object which can be used to reintegrate.
        return dict()

    def integrate_ICE(self, link_data):
        # Recouple this object with the things that have been decoupled.  This means reregistering,
        # reconnecting sideways, and reattaching to any parent(s).
        # Ordering is not necessarily preserved by this act
        pass

    def destroy(self):
        # This must destroy children objects.  Descendants should destroy dependants before calling super.
        self.unregister_ice()
        self.destroyed = True
        pass

    def PrintIceErr(self):
        if not hasattr(self, 'IceErr'):
            return

        for err, exc in self.IceErr:
            print "----- %s -----\n%s----------" % (err, exc)

    def IceCopy(self):
        return Ice.thaw(self.freeze())

    def isa(self, kls):
        return kls in self.__class__.__mro__
