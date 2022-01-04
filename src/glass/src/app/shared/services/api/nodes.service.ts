import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

import { Disk } from '~/app/shared/services/api/local.service';

export type DiskSolution = {
  systemdisk?: Disk;
  storage: Disk[];
  /* eslint-disable-next-line @typescript-eslint/naming-convention */
  storage_size: number;
  rejected: Disk[];
  possible: boolean;
};

@Injectable({
  providedIn: 'root'
})
export class NodesService {
  private url = 'api/nodes';

  constructor(private http: HttpClient) {}

  /**
   * Obtain the list of disks and a deployment solution, if possible.
   */
  deploymentDiskSolution(): Observable<DiskSolution> {
    return this.http.get<DiskSolution>(`${this.url}/deployment/disksolution`);
  }
}
