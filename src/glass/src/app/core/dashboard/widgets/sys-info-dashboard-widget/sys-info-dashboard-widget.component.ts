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
import { Component } from '@angular/core';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';

import { Inventory, LocalNodeService } from '~/app/shared/services/api/local.service';

@Component({
  selector: 'glass-sys-info-dashboard-widget',
  templateUrl: './sys-info-dashboard-widget.component.html',
  styleUrls: ['./sys-info-dashboard-widget.component.scss']
})
export class SysInfoDashboardWidgetComponent {
  data: Inventory = {} as Inventory;

  constructor(private localNodeService: LocalNodeService) {}

  updateData($data: Inventory) {
    this.data = $data;
  }

  loadData(): Observable<Inventory> {
    return this.localNodeService.inventory().pipe(
      map((inventory: Inventory) => {
        // Modify the uptime value to allow the `relativeDate` pipe
        // to calculate the correct time to display.
        inventory.system_uptime = inventory.system_uptime * -1;
        return inventory;
      })
    );
  }
}
