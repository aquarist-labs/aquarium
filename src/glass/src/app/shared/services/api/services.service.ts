import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

export interface Reservations {
  reserved: number;
  available: number;
}

export interface Requirements {
  reserved: number;
  available: number;
  required: number;
}

export interface CheckRequirementsRequest {
  size: number;
  replicas: number;
}

export interface CheckRequirementsReply {
  feasible: boolean;
  requirements: Requirements;
}

export declare type ServiceType = 'cephfs' | 'rbd' | 'rgw' | 'iscsi' | 'nfs';

export interface CreateServiceRequest {
  name: string;
  type: ServiceType;
  size: number;
  replicas: number;
}

export interface CreateServiceReply {
  success: boolean;
}

export interface ServiceDesc {
  name: string;
  reservation: number;
  type: ServiceType;
  pools: number[];
  replicas: number;
}

export type ServiceStorage = {
  name: string;
  used: number;
  avail: number;
  allocated: number;
  utilization: number;
};

@Injectable({
  providedIn: 'root'
})
export class ServicesService {
  private url = 'api/services';

  constructor(private http: HttpClient) {}

  /**
   * Obtain existing service reservations in byte.
   */
  public reservations(): Observable<Reservations> {
    return this.http.get<Reservations>(`${this.url}/reservations`);
  }

  public checkRequirements(_size: number, _replicas: number): Observable<CheckRequirementsReply> {
    const request: CheckRequirementsRequest = {
      size: _size,
      replicas: _replicas
    };
    return this.http.post<CheckRequirementsReply>(`${this.url}/check-requirements`, request);
  }

  public create(
    _name: string,
    _type: ServiceType,
    _size: number,
    _replicas: number
  ): Observable<CreateServiceReply> {
    const request: CreateServiceRequest = {
      name: _name,
      type: _type,
      size: _size,
      replicas: _replicas
    };
    return this.http.post<CreateServiceReply>(`${this.url}/create`, request);
  }

  public list(): Observable<ServiceDesc[]> {
    return this.http.get<ServiceDesc[]>(`${this.url}/`);
  }

  public stats(): Observable<Record<string, ServiceStorage>> {
    return this.http.get<Record<string, ServiceStorage>>(`${this.url}/stats`);
  }
}
