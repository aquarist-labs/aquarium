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
  /* eslint-disable @typescript-eslint/naming-convention */
  node_stage: StatusStageEnum;
  cluster?: ClusterStatus;
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
}
