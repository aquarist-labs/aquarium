import { Component, OnInit, TemplateRef, ViewChild } from '@angular/core';
import { marker as TEXT } from '@biesbjerg/ngx-translate-extract-marker';
import { Observable } from 'rxjs';

import { DatatableColumn } from '~/app/shared/models/datatable-column.type';
import { BytesToSizePipe } from '~/app/shared/pipes/bytes-to-size.pipe';
import { ServiceDesc, ServicesService } from '~/app/shared/services/api/services.service';

@Component({
  selector: 'glass-services-dashboard-widget',
  templateUrl: './services-dashboard-widget.component.html',
  styleUrls: ['./services-dashboard-widget.component.scss']
})
export class ServicesDashboardWidgetComponent implements OnInit {
  @ViewChild('flavor', { static: true })
  flavor?: TemplateRef<any>;

  data: ServiceDesc[] = [];
  columns?: DatatableColumn[];

  constructor(private service: ServicesService, private bytesToSizePipe: BytesToSizePipe) {}

  ngOnInit() {
    this.columns = [
      {
        name: TEXT('Name'),
        prop: 'name',
        sortable: true
      },
      {
        name: TEXT('Type'),
        prop: 'type',
        sortable: true
      },
      {
        name: TEXT('Usable Size'),
        prop: 'reservation',
        pipe: this.bytesToSizePipe,
        sortable: true
      },
      {
        name: TEXT('Raw Size'),
        prop: 'raw_size',
        pipe: this.bytesToSizePipe,
        sortable: true
      },
      {
        name: TEXT('Flavor'),
        prop: 'replicas',
        cellTemplate: this.flavor,
        sortable: true
      }
    ];
  }

  updateData($data: ServiceDesc[]) {
    this.data = $data;
  }

  loadData(): Observable<ServiceDesc[]> {
    return this.service.list();
  }
}
