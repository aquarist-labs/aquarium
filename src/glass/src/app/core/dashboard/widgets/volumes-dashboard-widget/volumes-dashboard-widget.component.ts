import { Component } from '@angular/core';
import { marker as TEXT } from '@biesbjerg/ngx-translate-extract-marker';
import { Observable } from 'rxjs';

import { DatatableColumn } from '~/app/shared/models/datatable-column.type';
import { OrchService, Volume } from '~/app/shared/services/api/orch.service';

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
      prop: 'path',
      sortable: true
    },
    {
      name: TEXT('Serial'),
      prop: 'device_id',
      sortable: true
    },
    {
      name: TEXT('Vendor'),
      prop: 'sys_api.vendor',
      sortable: true
    },
    {
      name: TEXT('Type'),
      prop: 'human_readable_type',
      sortable: true
    },
    {
      name: TEXT('Size'),
      prop: 'sys_api.human_readable_size',
      sortable: true
    }
  ];

  constructor(private orchService: OrchService) {}

  updateData($data: Volume[]) {
    this.data = $data;
  }

  loadData(): Observable<Volume[]> {
    return this.orchService.volumes();
  }
}
