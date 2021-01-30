# ARCHITECTURE

## Overview

```
                        .------------------------.
 MGR orch cephadm <---> | backend <---> frontend | <---> user
                        '------ AQUARIUM --------'
```

### From nothing to a single node

1. User flashes image on a given box, and boots;
2. Upon boot, backend starts;
3. Backend serves frontend;
4. On input, backend bootstraps minimal cluster;
5. Backend provides information to frontend on state of deployment upon request;
6. Once bootstrapped, backend obtains hosts informations from mgr orch
7. On request, backend provides host and other relevant information to frontend;
8. On input, backend creates specified services (NFS, cephfs)
9. On request, backend provides service information to frontend;
10. On request, backend provides cluster information to frontend.

### From single node (A) to two nodes (A + B)

1. User flashes image on a second box (B), and boots;
2. Upon boot, backend starts;
3. Backend serves frontend;
4. User sets existing node (A) to `extend mode`;
5. Backend generates a validation token;
6. Frontend serves validation token to user;
7. User chooses `extend` on new node (B);
8. User inputs validation token on node B;
9. Node B backend communicates with node A, changes tokens, gets needed data
   (ssh keys, whatever) and writes to disk;
10. Node B defers to node A as master; (this is totally forward-looking)
10. Node A adds Node B as a host on ceph-mgr orch;
11. Node A expands the cluster.


## Persistent State

### How we do this

1. Think about it
2. ???
3. PROFIT!


## Operations

### bootstrap

* Relies on cephadm tool for simplicity
* endpoint at `/api/bootstrap/start` kicks-off the bootstrapping process
* endpoint at `/api/bootstrap/status` provides information on state (none,
  running, done)

### ceph-mgr orch related operations

* Relies on librados python bindings
* Issues mgr_command()'s directly to the ceph-mgr
* We don't need a `one operation, one endpoint` approach, we can have
  semantically sound endpoints for the frontend that may perform one or more
  orch operations

