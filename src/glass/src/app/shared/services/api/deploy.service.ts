/* eslint-disable @typescript-eslint/naming-convention */
import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

import { Disk, DisksQualifiedStatus } from '~/app/shared/services/api/local.service';

export type Progress = {
  value: number; // Current progress percentage.
  msg: string; // Current progress message.
};

export enum InitStateEnum {
  none = 0,
  installed = 1,
  deployed = 2
}

export enum DeploymentStateEnum {
  none = 0,
  installing = 1,
  installed = 2,
  deploying = 3,
  deployed = 4,
  error = 5
}

export type DeploymentState = {
  init: InitStateEnum;
  deployment: DeploymentStateEnum;
};

export enum DeploymentErrorEnum {
  none = 0,
  cantBootstrap = 1,
  nodeNotStarted = 2,
  cantJoin = 3,
  cantAssimilate = 4,
  unknownError = 5
}

export type DeploymentError = {
  code: DeploymentErrorEnum;
  msg?: string;
};

export type DeploymentRegistry = {
  registry: string;
  image: string;
  secure: boolean;
};

export type DeploymentStartRequest = {
  ntpaddr: string;
  hostname: string;
  registry?: DeploymentRegistry;
};

export type JoinNodeParams = {
  address: string; // Address of node to contact.
  token: string; // Token to join the cluster.
  hostname: string; // Hostname to use when joining.
  storage: string[]; // Devices to be used for storage.
};

export type DeployTokenReply = {
  token: string; // The cluster token, required to join.
};

export enum DiskTypeEnum {
  none = 0,
  hdd = 1,
  ssd = 2
}

export type DeploymentStatus = {
  state: DeploymentState; // Current deployment state.
  progress?: Progress; // Insights into current progress.
  error: DeploymentError; // Current deployment error.
};

export type DeployStatusReply = {
  installed: boolean; // Node has been installed.
  status: DeploymentStatus; // Deployment status.
};

export type DeployInstallParams = {
  device: string; // Device to install on.
};

export type DeployInstallReply = {
  success: boolean; // Whether the operation request was successful.
};

export type Requirements = {
  qualified: boolean; // The localhost passes validation.
  impossible: boolean; // Installation is impossible.
  cpu: {
    // CPU qualification details.
    qualified: boolean; // The CPU is sufficient.
    min_threads: number; // Minimum number of CPU threads.
    actual_threads: number; // Actual number of CPU threads.
    error: string; // CPU didn't meet requirements.
    status: 0 | 1; // Status code.
  };
  mem: {
    // Memory qualification details.
    qualified: boolean; // The memory is sufficient.
    min_mem: number; // Minimum amount of memory (bytes).
    actual_mem: number; // Actual amount of memory (bytes).
    error: string; // Memory didn't meet requirements.
    status: 0 | 1; // Status code.
  };
  disks: {
    // Disk qualification details.
    available: DisksQualifiedStatus; // Host's available disks.
    install: DisksQualifiedStatus; // Host's install disk.
  };
};

export type DeployRequirementsReply = {
  requirements: Requirements;
};

export type DeployDevicesReply = {
  devices: Disk[];
};

export type DeployCreateParams = {
  hostname: string; // Hostname to use for this node.
  ntpaddr: string; // NTP address to be used.
  registry?: {
    registry: string; // Registry URL.
    secure: boolean; // Whether registry is secure.
    image: string; // Image to use.
  }; // Custom registry.
  storage: string[]; // Devices to be consumed for storage.
};

export type DeployJoinReply = {
  success: boolean; // Whether the request was successful.
  msg: string; // A response message, if any.
};

@Injectable({
  providedIn: 'root'
})
export class DeployService {
  private url = 'api/deploy';

  constructor(private http: HttpClient) {}

  /**
   * Obtain the status of this node's deployment.
   */
  status(): Observable<DeployStatusReply> {
    return this.http.get<DeployStatusReply>(`${this.url}/status`);
  }

  /**
   * Start installing this node.
   */
  install(params: DeployInstallParams): Observable<DeployInstallReply> {
    return this.http.post<DeployInstallReply>(`${this.url}/install`, params);
  }

  /**
   * Obtain system requirements for install.
   */
  requirements(): Observable<DeployRequirementsReply> {
    return this.http.get<DeployRequirementsReply>(`${this.url}/requirements`);
  }

  /**
   * Obtain storage devices.
   */
  devices(): Observable<DeployDevicesReply> {
    return this.http.get<DeployDevicesReply>(`${this.url}/devices`);
  }

  /**
   * Create a new deployment on this node.
   */
  create(params: DeployCreateParams): Observable<DeployStatusReply> {
    return this.http.post<DeployStatusReply>(`${this.url}/create`, params);
  }

  /**
   * Obtain the cluster's token.
   */
  token(): Observable<DeployTokenReply> {
    return this.http.get<DeployTokenReply>(`${this.url}/token`);
  }

  /**
   * Start joining an existing cluster.
   */
  join(params: JoinNodeParams): Observable<DeployJoinReply> {
    return this.http.post<DeployJoinReply>(`${this.url}/join`, params);
  }
}
