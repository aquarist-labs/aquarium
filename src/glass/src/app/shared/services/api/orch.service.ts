import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

export type Host = {
  hostname: string;
  address: string;
};

export type Device = {
  available: boolean;
  // eslint-disable-next-line @typescript-eslint/naming-convention
  device_id: string;
  model: string;
  vendor: string;
  // eslint-disable-next-line @typescript-eslint/naming-convention
  human_readable_type: string;
  size: number;
  path: string;
  // eslint-disable-next-line @typescript-eslint/naming-convention
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
  hosts(): Observable<{ hosts: Host[] }> {
    return this.http.get<{ hosts: Host[] }>(`${this.url}/hosts`);
  }

  /**
   * Get devices information
   */
  devices(): Observable<{ [hostName: string]: HostDevices }> {
    return this.http.get<{ [hostName: string]: HostDevices }>(`${this.url}/devices`);
  }
}
