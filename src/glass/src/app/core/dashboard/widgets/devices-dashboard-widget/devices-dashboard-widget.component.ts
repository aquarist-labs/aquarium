/* eslint-disable @typescript-eslint/naming-convention */
import { Component, Input } from '@angular/core';
import { Observable, of } from 'rxjs';

import { AbstractDashboardWidget } from '~/app/core/dashboard/widgets/abstract-dashboard-widget';
import { Device } from '~/app/shared/services/api/orch.service';

@Component({
  selector: 'glass-devices-dashboard-widget',
  templateUrl: './devices-dashboard-widget.component.html',
  styleUrls: ['./devices-dashboard-widget.component.scss']
})
export class DevicesDashboardWidgetComponent extends AbstractDashboardWidget<Device[]> {
  @Input()
  config: Record<string, any> = {};

  data: Device[] = [];
  displayedColumns: string[] = ['path', 'device_id', 'vendor', 'size'];

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
    ]);
  }
}
