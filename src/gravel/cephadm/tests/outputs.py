
gather_facts_real = '''
{
  "arch": "x86_64",
  "bios_date": "04/01/2014",
  "bios_version": "rel-1.13.0-0-gf21b5a4-rebuilt.opensuse.org",
  "cpu_cores": 1,
  "cpu_count": 1,
  "cpu_load": {
    "15min": 0.0,
    "1min": 0.03,
    "5min": 0.03
  },
  "cpu_model": "AMD EPYC Processor (with IBPB)",
  "cpu_threads": 1,
  "flash_capacity": "0.0",
  "flash_capacity_bytes": 0,
  "flash_count": 0,
  "flash_list": [],
  "hdd_capacity": "60.1GB",
  "hdd_capacity_bytes": 60129542144,
  "hdd_count": 5,
  "hdd_list": [
    {
      "description": "Virtio Block Device Unknown (8.6GB)",
      "dev_name": "vdd",
      "disk_size_bytes": 8589934592,
      "model": "Unknown",
      "rev": "Unknown",
      "vendor": "Virtio Block Device",
      "wwid": "Unknown"
    },
    {
      "description": "Virtio Block Device Unknown (8.6GB)",
      "dev_name": "vdb",
      "disk_size_bytes": 8589934592,
      "model": "Unknown",
      "rev": "Unknown",
      "vendor": "Virtio Block Device",
      "wwid": "Unknown"
    },
    {
      "description": "Virtio Block Device Unknown (8.6GB)",
      "dev_name": "vde",
      "disk_size_bytes": 8589934592,
      "model": "Unknown",
      "rev": "Unknown",
      "vendor": "Virtio Block Device",
      "wwid": "Unknown"
    },
    {
      "description": "Virtio Block Device Unknown (8.6GB)",
      "dev_name": "vdc",
      "disk_size_bytes": 8589934592,
      "model": "Unknown",
      "rev": "Unknown",
      "vendor": "Virtio Block Device",
      "wwid": "Unknown"
    },
    {
      "description": "Virtio Block Device Unknown (25.8GB)",
      "dev_name": "vda",
      "disk_size_bytes": 25769803776,
      "model": "Unknown",
      "rev": "Unknown",
      "vendor": "Virtio Block Device",
      "wwid": "Unknown"
    }
  ],
  "hostname": "node01",
  "interfaces": {
    "eth0": {
      "driver": "virtio_net",
      "iftype": "physical",
      "ipv4_address": "192.168.121.235/24",
      "ipv6_address": "fe80::5054:ff:fe7c:6929/64",
      "lower_devs_list": [],
      "mtu": 1500,
      "nic_type": "ethernet",
      "operstate": "up",
      "speed": -1,
      "upper_devs_list": []
    },
    "lo": {
      "driver": "",
      "iftype": "logical",
      "ipv4_address": "127.0.0.1/8",
      "ipv6_address": "::1/128",
      "lower_devs_list": [],
      "mtu": 65536,
      "nic_type": "loopback",
      "operstate": "unknown",
      "speed": -1,
      "upper_devs_list": []
    }
  },
  "kernel": "5.10.12-1-default",
  "kernel_parameters": {
    "net.ipv4.ip_nonlocal_bind": "0"
  },
  "kernel_security": {
    "description": "AppArmor: Enabled(45 enforce)",
    "enforce": 45,
    "type": "AppArmor"
  },
  "memory_available_kb": 3665636,
  "memory_free_kb": 3676188,
  "memory_total_kb": 4014412,
  "model": " (Standard PC (i440FX + PIIX, 1996))",
  "nic_count": 1,
  "operating_system": "Unknown",
  "subscribed": "Unknown",
  "system_uptime": 157.45,
  "timestamp": 1613800833.7839758,
  "vendor": "QEMU"
}'''

inventory_real = '''
[
    {
        "available": true,
        "device_id": "01123456",
        "lsm_data": {},
        "lvs": [],
        "path": "/dev/vdb",
        "rejected_reasons": [],
        "sys_api": {
            "human_readable_size": "8.00 GB",
            "locked": 0,
            "model": "",
            "nr_requests": "256",
            "partitions": {},
            "path": "/dev/vdb",
            "removable": "0",
            "rev": "",
            "ro": "0",
            "rotational": "1",
            "sas_address": "",
            "sas_device_handle": "",
            "scheduler_mode": "mq-deadline",
            "sectors": 0,
            "sectorsize": "512",
            "size": 8589934592.0,
            "support_discard": "512",
            "vendor": "0x1af4"
        }
    },
    {
        "available": true,
        "device_id": "01789101",
        "lsm_data": {},
        "lvs": [],
        "path": "/dev/vdc",
        "rejected_reasons": [],
        "sys_api": {
            "human_readable_size": "8.00 GB",
            "locked": 0,
            "model": "",
            "nr_requests": "256",
            "partitions": {},
            "path": "/dev/vdc",
            "removable": "0",
            "rev": "",
            "ro": "0",
            "rotational": "1",
            "sas_address": "",
            "sas_device_handle": "",
            "scheduler_mode": "mq-deadline",
            "sectors": 0,
            "sectorsize": "512",
            "size": 8589934592.0,
            "support_discard": "512",
            "vendor": "0x1af4"
        }
    },
    {
        "available": true,
        "device_id": "01112131",
        "lsm_data": {},
        "lvs": [],
        "path": "/dev/vdd",
        "rejected_reasons": [],
        "sys_api": {
            "human_readable_size": "8.00 GB",
            "locked": 0,
            "model": "",
            "nr_requests": "256",
            "partitions": {},
            "path": "/dev/vdd",
            "removable": "0",
            "rev": "",
            "ro": "0",
            "rotational": "1",
            "sas_address": "",
            "sas_device_handle": "",
            "scheduler_mode": "mq-deadline",
            "sectors": 0,
            "sectorsize": "512",
            "size": 8589934592.0,
            "support_discard": "512",
            "vendor": "0x1af4"
        }
    },
    {
        "available": true,
        "device_id": "01415161",
        "lsm_data": {},
        "lvs": [],
        "path": "/dev/vde",
        "rejected_reasons": [],
        "sys_api": {
            "human_readable_size": "8.00 GB",
            "locked": 0,
            "model": "",
            "nr_requests": "256",
            "partitions": {},
            "path": "/dev/vde",
            "removable": "0",
            "rev": "",
            "ro": "0",
            "rotational": "1",
            "sas_address": "",
            "sas_device_handle": "",
            "scheduler_mode": "mq-deadline",
            "sectors": 0,
            "sectorsize": "512",
            "size": 8589934592.0,
            "support_discard": "512",
            "vendor": "0x1af4"
        }
    },
    {
        "available": false,
        "device_id": "",
        "lsm_data": {},
        "lvs": [],
        "path": "/dev/vda",
        "rejected_reasons": [
            "locked"
        ],
        "sys_api": {
            "human_readable_size": "24.00 GB",
            "locked": 1,
            "model": "",
            "nr_requests": "256",
            "partitions": {
                "vda1": {
                    "holders": [],
                    "human_readable_size": "2.00 MB",
                    "sectors": "4096",
                    "sectorsize": 512,
                    "size": 2097152.0,
                    "start": "2048"
                },
                "vda2": {
                    "holders": [],
                    "human_readable_size": "20.00 MB",
                    "sectors": "40960",
                    "sectorsize": 512,
                    "size": 20971520.0,
                    "start": "6144"
                },
                "vda3": {
                    "holders": [],
                    "human_readable_size": "18.97 GB",
                    "sectors": "39780352",
                    "sectorsize": 512,
                    "size": 20367540224.0,
                    "start": "47104"
                },
                "vda4": {
                    "holders": [],
                    "human_readable_size": "5.01 GB",
                    "sectors": "10504159",
                    "sectorsize": 512,
                    "size": 5378129408.0,
                    "start": "39827456"
                }
            },
            "path": "/dev/vda",
            "removable": "0",
            "rev": "",
            "ro": "0",
            "rotational": "1",
            "sas_address": "",
            "sas_device_handle": "",
            "scheduler_mode": "mq-deadline",
            "sectors": 0,
            "sectorsize": "512",
            "size": 25769803776.0,
            "support_discard": "512",
            "vendor": "0x1af4"
        }
    }
]
'''
