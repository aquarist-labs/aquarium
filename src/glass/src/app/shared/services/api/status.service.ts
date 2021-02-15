import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

export type Status = {
  /* eslint-disable @typescript-eslint/naming-convention */
  deployment_state: {
    last_modified: string;
    stage: 'none' | 'bootstrapping' | 'bootstrapped' | 'ready' | 'unknown';
  };
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
