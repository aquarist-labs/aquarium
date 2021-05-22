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

export type SetNtpRequest = {
  addr: string;
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
  hosts(): Observable<Host[]> {
    return this.http.get<Host[]>(`${this.url}/hosts`);
  }

  /**
   * Get devices information
   */
  devices(): Observable<{ [hostName: string]: HostDevices }> {
    return this.http.get<{ [hostName: string]: HostDevices }>(`${this.url}/devices`);
  }

  /**
   * Set NTP
   */
  setNtp(_addr: string): Observable<boolean> {
    const request: SetNtpRequest = {
      addr: _addr
    };
    return this.http.put<boolean>(`${this.url}/ntp`, request);
  }
}
