import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

export type BootstrapBasicReply = {
  success: boolean;
};

export type BootstrapStatusReply = {
  stage: 'none' | 'running' | 'done' | 'error';
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
