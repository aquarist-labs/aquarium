/* eslint-disable @typescript-eslint/naming-convention */
import { Component } from '@angular/core';
import * as _ from 'lodash';
import { Observable, of, Subscription } from 'rxjs';
import { catchError } from 'rxjs/operators';

import { AbstractDashboardWidget } from '~/app/core/dashboard/widgets/abstract-dashboard-widget';
import { Device } from '~/app/shared/services/api/orch.service';

@Component({
  selector: 'glass-devices-dashboard-widget',
  templateUrl: './devices-dashboard-widget.component.html',
  styleUrls: ['./devices-dashboard-widget.component.scss']
})
export class DevicesDashboardWidgetComponent extends AbstractDashboardWidget<Device[]> {
  data: Device[] = [];
  displayedColumns: string[] = ['path', 'device_id', 'vendor', 'size'];
  error = false;

  protected subscription: Subscription = new Subscription();

  constructor() {
    super();
    this.subscription = this.loadDataEvent.subscribe(() => {
      this.error = false;
    });
  }

  loadData(): Observable<Device[]> {
    return of([
      {
        path: 'sdc',
        device_id: '6712423423HGJH§',
        vendor: 'Western Digital',
        size: 1024 * 1024 * 1024 * 256,
        available: true,
        model: 'foo',
        human_readable_type: '',
        rejected_reasons: []
      },
      {
        path: 'sdd',
        device_id: '843HZ242342JNV5',
        vendor: 'Seagate',
        size: 1024 * 1024 * 1024 * 512,
        available: true,
        model: 'bar',
        human_readable_type: '',
        rejected_reasons: []
      },
      {
        path: 'sde',
        device_id: 'HH5465736BNM',
        vendor: 'Hitachi',
        size: 1024 * 1024 * 1024 * 96,
        available: true,
        model: 'baz',
        human_readable_type: '',
        rejected_reasons: []
      }
    ]).pipe(
      // @ts-ignore
      catchError((err) => {
        if (_.isFunction(err.preventDefault)) {
          err.preventDefault();
        }
        this.error = true;
      })
    );
  }
}
