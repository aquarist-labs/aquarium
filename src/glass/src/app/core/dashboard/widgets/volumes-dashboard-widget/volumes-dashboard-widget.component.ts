import { Component } from '@angular/core';
import { marker as TEXT } from '@biesbjerg/ngx-translate-extract-marker';
import { Observable } from 'rxjs';

import { DatatableColumn } from '~/app/shared/models/datatable-column.type';
import { LocalNodeService, Volume } from '~/app/shared/services/api/local.service';

@Component({
  selector: 'glass-volumes-dashboard-widget',
  templateUrl: './volumes-dashboard-widget.component.html',
  styleUrls: ['./volumes-dashboard-widget.component.scss']
})
export class VolumesDashboardWidgetComponent {
  data: Volume[] = [];
  columns: DatatableColumn[] = [
    {
      name: TEXT('Path'),
      prop: 'path'
    },
    {
      name: TEXT('Serial'),
      prop: 'device_id'
    },
    {
      name: TEXT('Vendor'),
      prop: 'sys_api.vendor'
    },
    {
      name: TEXT('Type'),
      prop: 'human_readable_type'
    },
    {
      name: TEXT('Size'),
      prop: 'sys_api.human_readable_size',
      compareProp: 'sys_api.size'
    }
  ];

  constructor(private localNodeService: LocalNodeService) {}

  updateData($data: Volume[]) {
    this.data = $data;
  }

  loadData(): Observable<Volume[]> {
    return this.localNodeService.volumes();
  }
}
