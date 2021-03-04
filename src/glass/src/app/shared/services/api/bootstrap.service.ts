import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

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
};

@Injectable({
  providedIn: 'root'
})
export class BootstrapService {
  private url = 'api/bootstrap';

  constructor(private http: HttpClient) {}

  /**
   * Start the bootstrapping.
   */
  start(): Observable<BootstrapBasicReply> {
    return this.http.post<BootstrapBasicReply>(`${this.url}/start`, null, {});
  }

  /**
   * Get the bootstrap status.
   */
  status(): Observable<BootstrapStatusReply> {
    return this.http.get<BootstrapStatusReply>(`${this.url}/status`);
  }

  public markFinished(): Observable<boolean> {
    return this.http.post<boolean>(`${this.url}/finished`, null, {});
  }
}
