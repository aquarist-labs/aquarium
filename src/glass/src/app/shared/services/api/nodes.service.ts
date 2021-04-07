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

@Injectable({
  providedIn: 'root'
})
export class NodesService {
  private url = 'api/nodes';

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
}
