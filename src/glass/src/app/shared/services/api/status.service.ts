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

export type HealthCheckSummary = {
  message: string;
  count: number;
};

export type HealthStatus = {
  status: string;
  checks: { [id: string]: HealthCheckSummary };
};

export type PGState = {
  state_name: string;
  count: number;
};

export type PGMap = {
  pgs_by_state: PGState[];
  num_pgs: number;
  num_pools: number;
  num_objects: number;
  // storage statistics
  data_bytes: number;
  bytes_used: number;
  bytes_avail: number;
  bytes_total: number;
  // pg statistics
  inactive_pgs_ratio: number;
  degraded_objects: number;
  degraded_total: number;
  degraded_ratio: number;
  // client io
  read_bytes_sec: number;
  write_bytes_sec: number;
  read_op_per_sec: number;
  write_op_per_sec: number;
};

export type MGRMap = {
  services: Record<string, any>;
};

export interface ClusterStatus {
  fsid: string;
  election_epoch: number;
  quorum: number[];
  quorum_names: string[];
  quorum_age: number;
  health: HealthStatus;
  pgmap: PGMap;
  mgrmap: MGRMap;
}

export type Status = {
  cluster?: ClusterStatus;
};

export type IORate = {
  read: number;
  write: number;
  read_ops: number;
  write_ops: number;
};

export type ServiceIO = {
  service_name: string;
  service_type: string;
  io_rate: IORate;
};

export type ClientIO = {
  cluster: IORate;
  services: ServiceIO[];
};

@Injectable({
  providedIn: 'root'
})
export class StatusService {
  private url = 'api/status';

  constructor(private http: HttpClient) {}

  /**
   * Get the current status.
   */
  status(): Observable<Status> {
    return this.http.get<Status>(`${this.url}/`);
  }

  clientIO(): Observable<ClientIO> {
    return this.http.get<ClientIO>(`${this.url}/client-io-rates`);
  }
}
