import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

export type CephFSCaps = {
  mds: string;
  mon: string;
  osd: string;
};

export type CephFSAuthorization = {
  entity: string;
  key: string;
  caps: CephFSCaps;
};

@Injectable({
  providedIn: 'root'
})
export class CephfsService {
  private url = 'api/services/cephfs';

  constructor(private http: HttpClient) {}

  public authorization(name: string): Observable<CephFSAuthorization> {
    return this.http.get<CephFSAuthorization>(`${this.url}/auth/${name}`);
  }
}
