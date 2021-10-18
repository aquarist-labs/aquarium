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
import { marker as TEXT } from '@biesbjerg/ngx-translate-extract-marker';
import * as _ from 'lodash';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';

import { translate } from '~/app/i18n.helper';
import { WidgetHealthStatus } from '~/app/shared/components/widget/widget.component';
import { Inventory, LocalNodeService } from '~/app/shared/services/api/local.service';

type Data = {
  name: string;
  percent: number;
};

@Component({
  selector: 'glass-load-dashboard-widget',
  templateUrl: './load-dashboard-widget.component.html',
  styleUrls: ['./load-dashboard-widget.component.scss']
})
export class LoadDashboardWidgetComponent {
  data: Data[] = [];

  constructor(private localNodeService: LocalNodeService) {}

  updateData($data: Data[]) {
    this.data = $data;
  }

  loadData(): Observable<Data[]> {
    return this.localNodeService.inventory().pipe(
      map((inventory: Inventory) => {
        /* eslint-disable @typescript-eslint/naming-convention */
        const load_1min = Math.floor(inventory.cpu.load.one_min * 100);
        const load_5min = Math.floor(inventory.cpu.load.five_min * 100);
        const load_15min = Math.floor(inventory.cpu.load.fifteen_min * 100);
        return [
          { name: translate(TEXT('1 min')), percent: load_1min },
          { name: translate(TEXT('5 min')), percent: load_5min },
          { name: translate(TEXT('15 min')), percent: load_15min }
        ];
      })
    );
  }

  getStatusClass(percent: number): WidgetHealthStatus {
    if (percent <= 50) {
      return WidgetHealthStatus.success;
    } else if (percent > 50 && percent <= 100) {
      return WidgetHealthStatus.warning;
    }
    return WidgetHealthStatus.error;
  }

  setStatus(data: Data[]): WidgetHealthStatus {
    return this.getStatusClass(_.max(_.map(data, 'percent'))!);
  }
}
