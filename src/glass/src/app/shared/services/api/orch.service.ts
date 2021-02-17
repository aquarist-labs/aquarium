/* eslint-disable @typescript-eslint/naming-convention */
import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

export type Host = {
  hostname: string;
  address: string;
};

export type Device = {
  available: boolean;
  device_id: string;
  model: string;
  vendor: string;
  human_readable_type: string;
  size: number;
  path: string;
  rejected_reasons: string[];
};

export type HostDevices = {
  address: string;
  hostname: string;
  devices: Device[];
};

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

@Injectable({
  providedIn: 'root'
})
export class OrchService {
  private url = 'api/orch';

  constructor(private http: HttpClient) {}

  /**
   * Get host information
   */
  hosts(): Observable<{ hosts: Host[] }> {
    return this.http.get<{ hosts: Host[] }>(`${this.url}/hosts`);
  }

  /**
   * Get devices information
   */
  devices(): Observable<{ [hostName: string]: HostDevices }> {
    return this.http.get<{ [hostName: string]: HostDevices }>(`${this.url}/devices`);
  }

  /**
   * Get volumes
   */
  volumes(): Observable<Volume[]> {
    return this.http.get<Volume[]>(`${this.url}/volumes`);
  }

  /**
   * Assimilate all devices
   */
  assimilateDevices(): Observable<boolean> {
    return this.http.post<boolean>(`${this.url}/devices/assimilate`, null, {});
  }

  /**
   * Get current assimilation status
   */
  assimilateStatus(): Observable<boolean> {
    return this.http.get<boolean>(`${this.url}/devices/all_assimilated`);
  }
}
