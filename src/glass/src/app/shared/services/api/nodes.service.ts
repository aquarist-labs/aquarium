import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

export type JoinNodeRequest = {
  addr: string;
  token: string;
};

export type TokenReply = {
  token: string;
};

export type BootstrapBasicReply = {
  success: boolean;
};

// eslint-disable-next-line no-shadow
export enum BootstrapStageEnum {
  none = 0,
  running = 1,
  done = 2,
  error = 3
}

export type BootstrapStatusReply = {
  stage: BootstrapStageEnum;
  progress: number;
};

@Injectable({
  providedIn: 'root'
})
export class NodesService {
  private url = 'api/nodes';
  private bootstrapURL = `${this.url}/bootstrap`;

  constructor(private http: HttpClient) {}

  /**
   * Join a cluster.
   */
  join(request: JoinNodeRequest): Observable<boolean> {
    return this.http.post<boolean>(`${this.url}/join`, request);
  }

  token(): Observable<TokenReply> {
    return this.http.get<TokenReply>(`${this.url}/token`);
  }

  /**
   * Start the bootstrapping.
   */
   bootstrapStart(): Observable<BootstrapBasicReply> {
    return this.http.post<BootstrapBasicReply>(
      `${this.bootstrapURL}/start`, null, {}
    );
  }

  /**
   * Get the bootstrap status.
   */
  bootstrapStatus(): Observable<BootstrapStatusReply> {
    return this.http.get<BootstrapStatusReply>(`${this.bootstrapURL}/status`);
  }

  public markBootstrapFinished(): Observable<boolean> {
    return this.http.post<boolean>(`${this.bootstrapURL}/finished`, null, {});
  }
}
