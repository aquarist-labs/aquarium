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
