import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

export type DeploymentStartRequest = {
  ntpaddr: string;
};

export type JoinNodeRequest = {
  address: string;
  token: string;
};

export type TokenReply = {
  token: string;
};

export type DeploymentBasicReply = {
  success: boolean;
};

// eslint-disable-next-line no-shadow
export enum NodeStageEnum {
  none = 0,
  bootstrapping = 1,
  deployed = 2,
  joining = 3,
  ready = 4,
  error = 5
}

export enum DiskTypeEnum {
  none = 0,
  hdd = 1,
  ssd = 2
}

export type DeploymentStatusReply = {
  stage: NodeStageEnum;
  progress: number;
};

export type DiskInfo = {
  vendor: string;
  model: string;
};

export type Disk = {
  path?: string;
  size: number;
  type: DiskTypeEnum;
  info: DiskInfo;
};

export type RejectedDisk = {
  disk: Disk;
  reasons: string[];
};

export type DiskSolution = {
  systemdisk?: Disk;
  storage: Disk[];
  /* eslint-disable-next-line @typescript-eslint/naming-convention */
  storage_size: number;
  rejected: RejectedDisk[];
  possible: boolean;
};

export type SetHostnameRequest = {
  name: string;
};

@Injectable({
  providedIn: 'root'
})
export class NodesService {
  private url = 'api/nodes';
  private deploymentURL = 'api/nodes/deployment';

  constructor(private http: HttpClient) {}

  /**
   * Join a cluster.
   */
  join(request: JoinNodeRequest): Observable<boolean> {
    return this.http.post<boolean>(`${this.url}/join`, request);
  }

  /**
   * Obtain the cluster's token.
   */
  token(): Observable<TokenReply> {
    return this.http.get<TokenReply>(`${this.url}/token`);
  }

  /**
   * Start node deployment.
   */
  deploymentStart(request: DeploymentStartRequest): Observable<DeploymentBasicReply> {
    return this.http.post<DeploymentBasicReply>(`${this.deploymentURL}/start`, request, {});
  }

  /**
   * Get deployment status.
   */
  deploymentStatus(): Observable<DeploymentStatusReply> {
    return this.http.get<DeploymentStatusReply>(`${this.deploymentURL}/status`);
  }

  /**
   * Mark deployment as being finished from our perspective.
   */
  public markDeploymentFinished(): Observable<boolean> {
    return this.http.post<boolean>(`${this.deploymentURL}/finished`, null, {});
  }

  /**
   * Get deployment devices
   */
  deploymentDiskSolution(): Observable<DiskSolution> {
    return this.http.get<DiskSolution>(`${this.deploymentURL}/disksolution`);
  }

  /**
   * Setup hostname
   */
   setHostname(name: string): Observable<boolean> {
    const request: SetHostnameRequest = { name };
    return this.http.put<boolean>(`${this.url}/hostname`, request);
  }
}
