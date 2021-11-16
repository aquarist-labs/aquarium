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
/* eslint-disable @typescript-eslint/naming-convention */
import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

export type SmartCtlDevice = {
  info_name: string;
  name: string;
  protocol: string;
  type: string;
};

export type SmartCtlAtaSmartAttributeFlags = {
  auto_keep: boolean;
  error_rate: boolean;
  event_count: boolean;
  performance: boolean;
  prefailure: boolean;
  // eslint-disable-next-line id-blacklist
  string: string;
  updated_online: boolean;
  value: number;
};

export type SmartCtlAtaSmartAttributeRaw = {
  // eslint-disable-next-line id-blacklist
  string: string;
  value: number;
};

export type SmartCtlAtaSmartAttribute = {
  flags: SmartCtlAtaSmartAttributeFlags;
  id: number;
  name: string;
  raw: SmartCtlAtaSmartAttributeRaw;
  thresh: number;
  value: number;
  when_failed: string;
  worst: number;
};

export type SmartCtlAtaSmartAttributes = {
  revision: number;
  table: Array<SmartCtlAtaSmartAttribute>;
};

export type SmartCtl = {
  device: SmartCtlDevice;
  model_name: string;
  serial_number: string;
  firmware_version: string;
  logical_block_size: number;
  physical_block_size: number;
  rotation_rate: number;
  ata_smart_attributes: SmartCtlAtaSmartAttributes;
};

export type DeviceUtilization = {
  total_kb: number;
  avail_kb: number;
  used_kb: number;
  utilization: number;
};

export type Device = {
  host: string;
  osd_id: number;
  path: string;
  rotational: boolean;
  vendor: string;
  model: string;
  utilization: DeviceUtilization;
  smart_metrics: SmartCtl;
};

export type DeviceHost = {
  utilization: DeviceUtilization;
  devices: Array<Device>;
};

@Injectable({
  providedIn: 'root'
})
export class DevicesService {
  private url = 'api/devices';

  constructor(private http: HttpClient) {}

  public list(): Observable<Record<string, DeviceHost>> {
    return this.http.get<Record<string, DeviceHost>>(`${this.url}/`);
  }
}
