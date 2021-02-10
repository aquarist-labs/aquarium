import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

export type Status = {
  // eslint-disable-next-line @typescript-eslint/naming-convention
  deployment_state: 'none' | 'bootstrapping' | 'bootstrapped' | 'ready';
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
