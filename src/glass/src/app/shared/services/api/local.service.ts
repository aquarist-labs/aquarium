/*
 * Project Aquarium's frontend (glass)
 * Copyright (C) 2021 SUSE, LLC.
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 */
import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';


export type Volume = {
  available: boolean;
  device_id: string;
  human_readable_type: string;
  lsm_data: Record<string, unknown>;
  lvs: null[];
  path: string;
  rejected_reasons: string[];
  sys_api: {
    human_readable_size: string;
    locked: number;
    model: string;
    nr_requests: number;
    partitions: Record<string, unknown>;
    removable: boolean;
    rev: string;
    ro: boolean;
    rotational: boolean;
    sas_address: string;
    sas_device_handle: string;
    scheduler_mode: string;
    sectors: number;
    sectorsize: number;
    size: number;
    support_discard: number;
    vendor: string;
  };
};

export type Nic = {
  driver: string;
  iftype: string;
  ipv4_address: string;
  ipv6_address: string;
  lower_devs_list: [null];
  mtu: number;
  nic_type: string;
  operstate: string;
  speed: number;
  upper_devs_list: [null];
};

export type Inventory = {
  hostname: string;
  model: string;
  vendor: string;
  kernel: string;
  operating_system: string;
  system_uptime: number;
  current_time: number;
  cpu: {
    model: string;
    cores: number;
    count: number;
    threads: number;
    load: {
      one_min: number;
      five_min: number;
      fifteen_min: number;
    };
  };
  nics: { [hostName: string]: Nic };
  memory: {
    available_kb: number;
    free_kb: number;
    total_kb: number;
  };
  disks: Volume[];
};

export type Facts = {
  arch: string;
  bios_date: string;
  bios_version: string;
  cpu_cores: number;
  cpu_count: number;
  cpu_load: {
    '15min': number;
    '1min': number;
    '5min': number;
  };
  cpu_model: string;
  cpu_threads: number;
  flash_capacity: string;
  flash_capacity_bytes: number;
  flash_count: number;
  flash_list: Array<any>;
  hdd_capacity: string;
  hdd_capacity_bytes: number;
  hdd_count: number;
  hdd_list: Array<{
    description: string;
    dev_name: string;
    disk_size_bytes: number;
    model: string;
    rev: string;
    vendor: string;
    wwid: string;
  }>;
  hostname: string;
  interfaces: Record<
    string,
    {
      driver: string;
      iftype: string;
      ipv4_address: string;
      ipv6_address: string;
      lower_devs_list: Array<any>;
      mtu: number;
      nic_type: string;
      operstate: string;
      speed: number;
      upper_devs_list: Array<any>;
    }
  >;
  kernel: string;
  kernel_parameters: {
    'net.ipv4.ip_nonlocal_bind': string;
  };
  kernel_security: {
    description: string;
    enforce: number;
    type: string;
  };
  memory_available_kb: number;
  memory_free_kb: number;
  memory_total_kb: number;
  model: string;
  operating_system: string;
  subscribed: string;
  system_uptime: number;
  timestamp: number;
  vendor: string;
};


@Injectable({
  providedIn: 'root'
})
export class LocalNodeService {

  private url = "api/local";

  public constructor(
    private http: HttpClient
  ) { }

  /**
   * Get volumes
   */
  public volumes(): Observable<Volume[]> {
    // Inventory is much faster than the volumes endpoint
    return this.inventory().pipe(map((i) => i.disks));
  }

  /**
   * Get inventory
   */
  public inventory(): Observable<Inventory> {
    return this.http.get<Inventory>(`${this.url}/inventory`);
  }

  /**
   * Get facts
   */
  public facts(): Observable<Facts> {
    // Inventory is much faster than the volumes endpoint
    return this.http.get<Facts>(`${this.url}/facts`);
  }

}
