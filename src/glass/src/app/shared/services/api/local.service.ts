/* eslint-disable @typescript-eslint/naming-convention */
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

export enum DiskRejectionReasonEnum {
  InUse = 1,
  TooSmall = 2,
  RemovableDevice = 3
}

export type Disk = {
  id: string;
  name: string;
  path: string;
  product: string;
  vendor: string;
  size: number;
  rotational: boolean;
  available: boolean;
  rejected_reasons: DiskRejectionReasonEnum[];
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
    arch: string;
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
  disks: Disk[];
};

// eslint-disable-next-line no-shadow
export enum StatusStageEnum {
  unknown = -1,
  none = 0,
  bootstrapping = 1,
  bootstrapped = 2,
  joining = 3,
  ready = 4
}

export type DisksQualifiedStatus = {
  qualified: boolean;
  min: number;
  actual: number;
  error: string;
  status: 0 | 1 | 2;
};

export type NodeStatus = {
  localhost_qualified?: {
    qualified: boolean;
    impossible: boolean;
    cpu: {
      qualified: boolean;
      min_threads: number;
      actual_threads: number;
      error: string;
      status: 0 | 1;
    };
    mem: {
      qualified: boolean;
      min_mem: number;
      actual_mem: number;
      error: string;
      status: 0 | 1;
    };
    disks: {
      available: DisksQualifiedStatus;
      install: DisksQualifiedStatus;
    };
  };
  inited: boolean;
  /* eslint-disable @typescript-eslint/naming-convention */
  node_stage: StatusStageEnum;
};

export type Event = {
  ts: number;
  severity: 'info' | 'warn' | 'danger';
  message: string;
};

@Injectable({
  providedIn: 'root'
})
export class LocalNodeService {
  private url = 'api/local';

  public constructor(private http: HttpClient) {}

  /**
   * Get volumes
   */
  public volumes(): Observable<Disk[]> {
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
   * Get node's status
   */
  public status(): Observable<NodeStatus> {
    return this.http.get<NodeStatus>(`${this.url}/status`);
  }

  /**
   * Get events
   */
  public events(): Observable<Event[]> {
    return this.http.get<Event[]>(`${this.url}/events`);
  }

  /**
   * Reboot the system.
   */
  public reboot(): Observable<void> {
    return this.http.post<void>(`${this.url}/reboot`, null);
  }

  /**
   * Shutdown the system.
   */
  public shutdown(): Observable<void> {
    return this.http.post<void>(`${this.url}/shutdown`, null);
  }
}
