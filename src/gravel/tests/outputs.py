# project aquarium's backend
# Copyright (C) 2021 SUSE, LLC.

mon_df_raw = '''
{
    "stats": {
        "total_bytes": 0,
        "total_avail_bytes": 0,
        "total_used_bytes": 0,
        "total_used_raw_bytes": 0,
        "total_used_raw_ratio": 0,
        "num_osds": 0,
        "num_per_pool_osds": 0,
        "num_per_pool_omap_osds": 0
    },
    "stats_by_class": {},
    "pools": []
}
'''

mon_osdmap_raw = '''
{
    "epoch": 4,
    "fsid": "738b16d8-7370-11eb-a679-5254007c6929",
    "created": "2021-02-20T11:40:46.356187+0000",
    "modified": "2021-02-20T11:41:28.376698+0000",
    "last_up_change": "0.000000",
    "last_in_change": "0.000000",
    "flags": "sortbitwise,recovery_deletes,purged_snapdirs,pglog_hardlimit",
    "flags_num": 5799936,
    "flags_set": [
        "pglog_hardlimit",
        "purged_snapdirs",
        "recovery_deletes",
        "sortbitwise"
    ],
    "crush_version": 1,
    "full_ratio": 0.94999998807907104,
    "backfillfull_ratio": 0.89999997615814209,
    "nearfull_ratio": 0.85000002384185791,
    "cluster_snapshot": "",
    "pool_max": 0,
    "max_osd": 0,
    "require_min_compat_client": "luminous",
    "min_compat_client": "jewel",
    "require_osd_release": "pacific",
    "pools": [],
    "osds": [],
    "osd_xinfo": [],
    "pg_upmap": [],
    "pg_upmap_items": [],
    "pg_temp": [],
    "primary_temp": [],
    "blocklist": {
        "192.168.121.235:0/1130838780": "2021-02-21T11:41:28.376648+0000",
        "192.168.121.235:6801/3890434388": "2021-02-21T11:41:28.376648+0000",
        "192.168.121.235:6800/400758687": "2021-02-21T11:41:17.565718+0000",
        "192.168.121.235:6800/3890434388": "2021-02-21T11:41:28.376648+0000",
        "192.168.121.235:6801/400758687": "2021-02-21T11:41:17.565718+0000",
        "192.168.121.235:0/2657348253": "2021-02-21T11:41:17.565718+0000",
        "192.168.121.235:0/2110685613": "2021-02-21T11:41:17.565718+0000",
        "192.168.121.235:6800/1261523223": "2021-02-21T11:41:03.641417+0000",
        "192.168.121.235:0/1988225134": "2021-02-21T11:41:03.641417+0000",
        "192.168.121.235:0/4182135307": "2021-02-21T11:41:28.376648+0000",
        "192.168.121.235:6801/1261523223": "2021-02-21T11:41:03.641417+0000",
        "192.168.121.235:0/2714297535": "2021-02-21T11:41:03.641417+0000"
    },
    "erasure_code_profiles": {
        "default": {
            "k": "2",
            "m": "2",
            "plugin": "jerasure",
            "technique": "reed_sol_van"
        }
    },
    "removed_snaps_queue": [],
    "new_removed_snaps": [],
    "new_purged_snaps": [],
    "crush_node_flags": {},
    "device_class_flags": {},
    "stretch_mode": {
        "stretch_mode_enabled": false,
        "stretch_bucket_count": 0,
        "degraded_stretch_mode": 0,
        "recovering_stretch_mode": 0,
        "stretch_mode_bucket": 0
    }
}
'''
