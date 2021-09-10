# project aquarium's backend
# Copyright (C) 2021 SUSE, LLC.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

import asyncio

# The other obvious choice here would be leveldb, given that's
# already used by ceph, but dbm is already approximately
# part of python core, so once less dependency.
import dbm
import errno
import sys
import threading
from logging import Logger
from pathlib import Path
from typing import Callable, List, Optional

from fastapi.logger import logger as fastapi_logger

logger: Logger = fastapi_logger

# Liberated from gravel/controllers/orch/ceph.py
# TODO: make this common / combine somehow?
try:
    import rados
except ModuleNotFoundError:
    pass


# Liberated from gravel/controllers/orch/ceph.py
# TODO: make this common / combine somehow?
class MissingSystemDependency(Exception):
    pass


class NoClusterExists(Exception):
    pass


class KV:

    # Deliberately not typing _db.  mypy seems happy with the following,
    # but at runtime I get "AttributeError: module 'dbm' has no attribute
    # '_Database'"".  Something to do with the way dbm imports different
    # database providers...?
    # _db: dbm._Database
    # I've also left _cluster, _config_watch and _ioctx typing inside
    # __init__() to handle the irritating case where rados isn't available
    # during unit tests
    _connector_thread: threading.Thread
    _run: bool
    _event: threading.Event
    _watches: dict
    _next_watch_id: int

    def __init__(self):
        if "rados" not in sys.modules:
            raise MissingSystemDependency("python3-rados module not found")
        # TODO: this should be created somewhere else (src/gravel/controllers/config.py?)
        var_lib_aquarium: Path = Path("/var/lib/aquarium")
        if not var_lib_aquarium.exists():
            var_lib_aquarium.mkdir(0o700)
        # This will fail with "_gdbm.error: [Errno 11] Resource temporarily
        # unavailable: '/var/lib/aquarium/kvstore'" if someone else has it
        # open.  But, as there's only one KV ever instantiated inside the
        # single GlobalState, this shouldn't ordinarily be a problem.
        self._db = dbm.open(f"{var_lib_aquarium}/kvstore", "c")
        self._cluster: Optional[rados.Rados] = None
        self._connector_thread = threading.Thread(target=self._cluster_connect)
        self._run = True
        # need to call self._event.set() to get out of that timeout for a
        # clean shutdown
        self._event = threading.Event()
        self._connector_thread.start()
        self._config_watch: Optional[rados.Watch] = None
        self._ioctx: Optional[rados.Ioctx] = None
        # Watches are setup by calls to watch(); this is a hash of keys to
        # watch IDs and callbacks, e.g.:
        # {
        #     "foo": { 1: callback_fn, 2: another_callback_fn },
        #     "bar": { 3: yet_another_callback }
        # }
        # This structure makes it trivial to invoke all registered callbacks
        # on a given key, but makes it somewhat irritating to cancel a watch
        # (you have to iterate through all keys to find the watch id to delete)
        # Possible solutions:
        # - Create an additional map of ID to key
        # - Make the cancel method supply the key being watched
        self._watches = {}
        # Watch IDs increment forever.  This is probably stupid (surely it'll
        # break eventually, given a long enough runtime and enough watches...)
        self._next_watch_id = 1

    async def ensure_connection(self) -> None:
        """Try to ensure we have a connection to the k/v store in the cluster"""
        # Most of the time, the cluster connect thread will be sleeping.
        # In case we don't have a connection to the cluster, calling this will
        # force the connect thread to go through its loop up to five times at
        # one second intervals, in order to try to connect.  Does not actually
        # *ensure* a connection, but it'll give it its best shot.  Useful during
        # startup and node bootstrap.
        tries: int = 0
        while tries < 5:
            if self._cluster and self._cluster.state == "connected":
                break
            self._event.set()
            await asyncio.sleep(1)
            tries += 1
        if self._cluster:
            # In this case the self._cluster object is valid, and we are
            # hopefully connected, so we can proceed.
            logger.info(
                f"ensure_connection: cluster state '{self._cluster.state}' after {tries} tries"
            )
        else:
            # If self._cluster isn't there, something is really broken
            # (e.g. /etc/ceph/ceph.conf somehow not present yet), so raise
            # an exception
            raise NoClusterExists(f"no cluster exists yet after {tries} tries")

    def _cluster_connect(self) -> None:
        logger.debug("Starting cluster connection thread")
        logged_missing_config_file: bool = False
        while self._run:
            try:
                if not self._cluster:
                    try:
                        # uses /etc/ceph/ceph.client.admin.keyring
                        # really should do separate keys per node so they can be
                        # evicted if necessary if nodes are decommisioned
                        self._cluster = rados.Rados(
                            conffile="/etc/ceph/ceph.conf"
                        )
                        logger.info("Got cluster handle")
                    except rados.ObjectNotFound as e:
                        if not logged_missing_config_file:
                            logger.info(
                                f"Can't get cluster handle: '{e}' - will keep retrying"
                            )
                            logged_missing_config_file = True
                if self._cluster and self._cluster.state != "connected":
                    # this can throw (auth failed, etc.)
                    logger.info("Connecting to cluster")
                    self._cluster.connect()
                    logger.info("Cluster connected")
                    has_aquarium_pool = "aquarium" in self._cluster.list_pools()
                    if not has_aquarium_pool:
                        logger.info("Creating aquarium pool")
                        # TODO: consider setting pg_num 1 as with device_health_metrics pool
                        self._cluster.create_pool("aquarium")
                    self._ioctx = self._cluster.open_ioctx("aquarium")
                    self._ioctx.application_enable("aquarium")
                    # This actually seems to be safe (doesn't trash existing omap
                    # data if present, which is neat)
                    self._ioctx.write_full(
                        "kvstore",
                        "# aquarium kv store is in this object's omap\n".encode(
                            "utf-8"
                        ),
                    )
                    # At this point, if it's a new pool, new object, etc.
                    # we need to push everything from our local cache to
                    # the omap on our kvstore, to populate it with whatever
                    # may have been set pre-bootstrap.
                    keys = self._db.keys()
                    values = list(self._db[k] for k in keys)
                    if keys and not has_aquarium_pool:
                        try:
                            with rados.WriteOpCtx() as op:
                                # This is a neat trick to make sure we've got version 1
                                # of the kvstore object, which will only be the case with
                                # a newly created object in a new pool.  If the object
                                # somehow already exists with a greater version, an
                                # exception will be raised with errno set to ERANGE when
                                # we try to perform the write op.  I'm having an extremely
                                # hard time seeing how this would be hit in normal operation
                                # (it'd have to be a very bizarre race or bug somewhere),
                                # but since we can handle it, let's do so.
                                op.assert_version(1)
                                self._ioctx.set_omap(op, keys, values)  # type: ignore
                                self._ioctx.operate_write_op(op, "kvstore")
                                logger.info(
                                    f"Pushed {keys} to kvstore in newly created aquarium pool"
                                )
                        except rados.OSError as e:
                            if e.errno == errno.ERANGE:
                                logger.warning(
                                    f"kvstore object already exists in aquarium pool, not pushing local cache"
                                )
                            else:
                                raise
                    # Arguably we really only need the config watch if any watches are
                    # requested on specific keys; having one here all the time is not
                    # strictly necessary, but makes the implementation simpler.
                    # TODO: need timeouts, error handlers etc on watch
                    self._config_watch = self._ioctx.watch(
                        "kvstore", self._config_notify
                    )
                    logger.debug(
                        f"config watch id is {self._config_watch.get_id()}"
                    )
                    # will raise:
                    # rados.ObjectNotFound: [errno 2] RADOS object not found (watch error)
            except Exception as e:
                # TODO: deal with this (log it? ignore it?)
                # e.g. RADOS rados state (You cannot perform that operation on a Rados object in state configuring.)
                logger.error(str(e))

            # TODO: Should we sleep for longer?  A minute instead of 10 seconds?  This is pretty arbitrary...
            logger.debug("Cluster connection thread sleeping for 10 seconds")
            self._event.wait(10)
            self._event.clear()
            # How on earth to we detect that the cluster has gone away
            # and trigger a reconnect?
            # What happens if we try a write op on a down cluster?
            # might want watch checks?

        logger.debug("Shutting down cluster connection")
        if self._config_watch:
            self._config_watch.close()
            # Need to set this to None, so it's deallocated before the
            # cluster is deallocated/shutdown, or we get:
            # Traceback (most recent call last):
            #   File "rados.pyx", line 477, in rados.Rados.require_state
            # rados.RadosStateError: RADOS rados state (You cannot perform that operation on a Rados object in state shutdown.)
            # Exception ignored in: 'rados.Watch.__dealloc__'
            # Traceback (most recent call last):
            #   File "rados.pyx", line 477, in rados.Rados.require_state
            # rados.RadosStateError: RADOS rados state (You cannot perform that operation on a Rados object in state shutdown.)
            self._config_watch = None
            # Note: https://github.com/ceph/ceph/pull/43107 fixes the
            # above, so we can get rid of this once that lands everywhere.
        if self._ioctx:
            self._ioctx.close()
        if self._cluster:
            self._cluster.shutdown()
        logger.debug("Cluster connection is shut down")

    def _config_notify(
        self, notify_id: int, notifier_id: str, watch_id: int, data: bytes
    ) -> None:
        key = data.decode("utf-8")
        logger.debug(
            f"Got notify on config object {notify_id} {notifier_id} {watch_id} {key}"
        )
        if key not in self._watches:
            return

        value = self._get(key)
        for watch in self._watches[key].values():
            watch(key, value)

    async def close(self) -> None:
        """Close k/v store connection"""
        self._run = False
        self._event.set()

    async def put(self, key: str, value: str) -> None:
        """Put key/value pair"""
        # Try to write to the kvstore in our pool, and also
        # write to our local cache (whether or not the write
        # to the pool succeeds)
        # Or: should we throw an exception if the write fails?
        # (or gets stuck for too long)?
        logger.debug(f"Put {key}: {value}")
        bvalue = value.encode("utf-8")
        if self._ioctx:
            try:
                # Note that current implementation lands in exception handler
                # with "RADOS rados state (You cannot perform that operation on a
                # Rados object in state configuring.)" in ... something (probably
                # the perform op), but we can short-circuit this if we use
                # the classes ioctx, and check if it's set first, before even
                # bothering to try anything.  Same in every other method that
                # does something with an ioctx.
                # But we probably also need to look at a lock on it (because...
                # we *know* this is a problem, or we just imagine it's a problem?)

                with rados.WriteOpCtx() as op:
                    self._ioctx.set_omap(op, (key,), (bvalue,))
                    logger.debug("Doing write op")
                    # write op naturally gets stuck if cluster badly degraded,
                    # need to do this asynchronously somehow...?
                    # TODO: what happens if it never succeeds?  The local
                    # cache is newer than the cluster, then later, when
                    # the cluster comes back, it will clobber the local
                    # cache (this is where we're starting to need epochs
                    # and probably re-inventing all sorts of cache and
                    # filesystem logic that others have done before)
                    # Possible solution:
                    # - write async(?)
                    # - write to local cache, but with "not known good" flag
                    # - when async write completes, remove "not known good" flag
                    #   from local cache value
                    # - if async write never completes (how to detect?) then
                    #   revert value to last known good (presupposes we're storing
                    #   last known good values somehow as part of this flag
                    #   business)
                    # except that's still no good; ioctx.operate_aio_write_op()
                    # *still* blocks if the cluster is sufficiently hosed -
                    # following is test code to use to demonstrate this (it
                    # hangs before either callback is hit)
                    # def _write_complete(comp):
                    #     logger.debug(f"write complete {comp}")
                    # def _write_safe(comp):
                    #     logger.debug(f"write safe {comp}")
                    # ioctx.operate_aio_write_op(op, "kvstore",
                    #     _write_complete,
                    #     _write_safe)
                    # Q: can we determine upfront whether a write will block?
                    self._ioctx.operate_write_op(op, "kvstore")
                    # This next notifies all watchers *INCLUDING* me!
                    self._ioctx.notify("kvstore", key)
            except Exception as e:
                # TODO: deal with this (log it? ignore it?)
                # e.g. RADOS rados state (You cannot perform that operation on a Rados object in state configuring.)
                logger.error(str(e))

        logger.debug(f"Writing {key}: {value} to local cache")
        self._db[key] = bvalue

    def _get(self, key: str) -> Optional[str]:
        # Try to get the value from the kvstore in our pool,
        # if that works, stash it in our local cache, then
        # return the value from the local cache.  If we can't
        # get the value from the cluster, this gets whatever
        # was last stashed in the local cache.
        # This implies that it's possible for values to be
        # quite stale in bizarre failure cases (value not read
        # for a long time, then updated in cluster by some other
        # instance, then cluster dies, then this instance reads,
        # gets the old value)
        if self._ioctx:
            try:
                with rados.ReadOpCtx() as op:
                    omap_iter, ret = self._ioctx.get_omap_vals_by_keys(
                        op, (key,)
                    )
                    assert ret == 0  # ???
                    # TODO: does this need to be async?
                    self._ioctx.operate_read_op(op, "kvstore")
                    kv = dict(omap_iter)
                    if key in kv:
                        self._db[key] = kv[key]
                    else:
                        # key not present in cluster kvstore, make sure
                        # it's also not present in db (prevent stale cache)
                        if key in self._db:
                            del self._db[key]

            except Exception as e:
                # TODO: deal with this (log it? ignore it?)
                logger.error(str(e))

        value = self._db.get(key)
        if not value:
            return None
        return value.decode("utf-8")

    async def get(self, key: str) -> Optional[str]:
        """Get value for provided key"""
        # Wraps _get() so we can use _get() outside asyncio in _config_notify()
        return self._get(key)

    async def get_prefix(self, key_prefix: str) -> List[str]:
        """Get a range of keys with a prefix"""
        # This is ugly, because pulling it out of omap is nice (there's a prefix
        # arg), but getting it from dbm means iterating through everything.
        # On the plus side, we're probably not talking about a lot of data...
        # But there's a perf optimization argument here for taking the values from
        # omap, setting them in the dbm, and returning the values from *omap* if
        # present, then only falling back to iterating dbm if we don't have the
        # values, rather than using the simpler logic in get().  But that might be
        # premature optimization, so possibly more straightforward to do the
        # simple implementation, then comment this for later use.
        values = []

        if self._ioctx:
            try:
                with rados.ReadOpCtx() as op:
                    omap_iter, ret = self._ioctx.get_omap_vals(
                        op,
                        start_after="",
                        filter_prefix=key_prefix,
                        max_return=1000,
                    )
                    assert ret == 0  # ???
                    # TODO: does this need to be async?
                    self._ioctx.operate_read_op(op, "kvstore")
                    for k, v in list(omap_iter):
                        self._db[k] = v

            except Exception as e:
                # TODO: deal with this (log it? ignore it?)
                logger.error(str(e))

        # Note: firstkey/nextkey assumes the gdbm implementation,
        # but that seems pretty damn safe...
        k = self._db.firstkey()  # type: ignore
        while k != None:
            if k.startswith(key_prefix.encode("utf-8")):  # type: ignore
                values.append(self._db[k].decode("utf-8"))
            k = self._db.nextkey(k)  # type: ignore
        return values

    async def rm(self, key: str) -> None:
        """Remove key from store"""
        logger.debug(f"Removing {key}")
        if self._ioctx:
            try:
                with rados.WriteOpCtx() as op:
                    self._ioctx.remove_omap_keys(op, (key,))
                    self._ioctx.operate_write_op(op, "kvstore")
                    # seems to succeed just fine even if the key doesn't exist
            except Exception as e:
                # TODO: deal with this (log it? ignore it?)
                logger.error(str(e))

        if key in self._db:
            del self._db[key]

    async def lock(self, key: str):
        """Lock a given key. Requires compliant consumers."""
        raise NotImplementedError()

    async def watch(
        self, key: str, callback: Callable[[str, str], None]
    ) -> int:
        """Watch updates on a given key"""
        watch_id = self._next_watch_id
        self._next_watch_id += 1
        if key not in self._watches:
            self._watches[key] = dict()
        self._watches[key][watch_id] = callback
        return watch_id

    async def cancel_watch(self, watch_id: int) -> None:
        """Cancel a watch"""
        for key in list(self._watches.keys()):
            if watch_id in self._watches[key]:
                del self._watches[key][watch_id]
            if not self._watches[key]:
                del self._watches[key]
