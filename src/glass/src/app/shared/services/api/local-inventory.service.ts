/*
 * Project Aquarium's frontend (glass)
 * Copyright (C) 2021 SUSE, LLC.
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 */
import { Injectable } from '@angular/core';
import { Observable, ReplaySubject } from 'rxjs';
import { map } from 'rxjs/operators';

import {
  Disk,
  Inventory,
  LocalNodeService,
  Nic,
  NodeStatusReply
} from '~/app/shared/services/api/local.service';
import { PollService } from '~/app/shared/services/poll.service';

export type NICEntry = {
  name: string;
  info: Nic;
};

@Injectable({
  providedIn: 'root'
})
export class LocalInventoryService {
  public inventory$: Observable<Inventory>;

  private inventorySource: ReplaySubject<Inventory> = new ReplaySubject<Inventory>(1);

  constructor(private localService: LocalNodeService, private pollService: PollService) {
    this.localService
      .status()
      .pipe(this.pollService.poll((status: NodeStatusReply) => !status.inited))
      .subscribe({
        next: (status: NodeStatusReply) => {
          console.log('checking node status: ', status);
          if (status.inited) {
            this.obtainInventory();
          }
        }
      });

    this.inventory$ = this.inventorySource.asObservable();
  }

  getDevices(): Observable<Disk[]> {
    return this.inventory$.pipe(map((inventory: Inventory) => inventory.disks));
  }

  getNICs(): Observable<NICEntry[]> {
    return this.inventory$.pipe(
      map((inventory: Inventory) => {
        const entries: NICEntry[] = [];
        Object.keys(inventory.nics).forEach((key: string) => {
          entries.push({
            name: key,
            info: inventory.nics[key]
          });
        });
        return entries;
      })
    );
  }

  private obtainInventory() {
    this.localService.inventory().subscribe({
      next: (inventory: Inventory) => {
        this.inventorySource.next(inventory);
      }
    });
  }
}
