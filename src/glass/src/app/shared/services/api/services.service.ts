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

export interface AllocationConstraints {
  allocated: number;
  available: number;
}

export interface RedundancyConstraints {
  /* eslint-disable @typescript-eslint/naming-convention */
  max_replicas: number;
}

export interface AvailabilityConstraints {
  hosts: number;
}

export interface Constraints {
  allocations: AllocationConstraints;
  redundancy: RedundancyConstraints;
  availability: AvailabilityConstraints;
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

@Injectable({
  providedIn: 'root'
})
export class ServicesService {
  private url = 'api/services';

  constructor(private http: HttpClient) {}

  public checkRequirements(_size: number, _replicas: number): Observable<CheckRequirementsReply> {
    const request: CheckRequirementsRequest = {
      size: _size,
      replicas: _replicas
    };
    return this.http.post<CheckRequirementsReply>(`${this.url}/check-requirements`, request);
  }

  /**
   * Obtains current service creation constraints.
   *
   * @returns Observable to a Constraints object
   */
  public getConstraints(): Observable<Constraints> {
    return this.http.get<Constraints>(`${this.url}/constraints`);
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
}
