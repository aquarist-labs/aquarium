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

export interface HealthCheckSummary {
  message: string;
  count: number;
}

export interface HealthStatus {
  status: string;
  checks: { [id: string]: HealthCheckSummary };
}

export interface ClusterStatus {
  fsid: string;
  /* eslint-disable @typescript-eslint/naming-convention */
  election_epoch: number;
  quorum: number[];
  quorum_names: string[];
  quorum_age: number;
  health: HealthStatus;
}

// eslint-disable-next-line no-shadow
export enum StatusStageEnum {
  unknown = -1,
  none = 0,
  bootstrapping = 1,
  bootstrapped = 2,
  joining = 3,
  ready = 4
}

export type Status = {
  cluster?: ClusterStatus;
};

export interface NodeStatus {
  inited: boolean;
  /* eslint-disable @typescript-eslint/naming-convention */
  node_stage: StatusStageEnum;
}


@Injectable({
  providedIn: 'root'
})
export class StatusService {
  private cluster_status_url = 'api/status';
  private node_local_url = 'api/local';

  constructor(private http: HttpClient) {}

  /**
   * Get the current status.
   */
  status(): Observable<Status> {
    return this.http.get<Status>(`${this.cluster_status_url}/`);
  }

  public node_status(): Observable<NodeStatus> {
    return this.http.get<NodeStatus>(`${this.node_local_url}/status`);
  }
}
