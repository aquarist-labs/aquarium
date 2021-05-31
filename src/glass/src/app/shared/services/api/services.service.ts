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
import { Observable, of } from 'rxjs';
import { catchError, mapTo } from 'rxjs/operators';

export interface Allocations {
  allocated: number;
  available: number;
}

export interface Requirements {
  allocated: number;
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
  allocation: number;
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

  public exists(service_name: string): Observable<boolean> {
    return this.http.get<ServiceDesc>(`${this.url}/get/${service_name}`).pipe(
      mapTo(true),
      catchError((error) => {
        error.preventDefault();
        return of(false);
      })
    );
  }

  public stats(): Observable<Record<string, ServiceStorage>> {
    return this.http.get<Record<string, ServiceStorage>>(`${this.url}/stats`);
  }
}
