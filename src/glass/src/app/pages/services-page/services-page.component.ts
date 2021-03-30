import { Component, OnInit } from '@angular/core';
import { marker as TEXT } from '@biesbjerg/ngx-translate-extract-marker';

import { DatatableColumn } from '~/app/shared/models/datatable-column.type';
import { BytesToSizePipe } from '~/app/shared/pipes/bytes-to-size.pipe';
import { RedundancyLevelPipe } from '~/app/shared/pipes/redundancy-level.pipe';
import { ServiceDesc, ServicesService } from '~/app/shared/services/api/services.service';
import { DialogService } from '~/app/shared/services/dialog.service';

@Component({
  selector: 'glass-services-page',
  templateUrl: './services-page.component.html',
  styleUrls: ['./services-page.component.scss']
})
export class ServicesPageComponent implements OnInit {
  loading = false;
  firstLoadComplete = false;
  data: ServiceDesc[] = [];
  columns: DatatableColumn[];

  constructor(
    private service: ServicesService,
    private bytesToSizePipe: BytesToSizePipe,
    private redundancyLevelPipe: RedundancyLevelPipe,
    private dialog: DialogService
  ) {
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
        name: TEXT('Allocated Size'),
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
        pipe: this.redundancyLevelPipe,
        sortable: true
      }
    ];
    this.loadData();
  }

  ngOnInit(): void {}

  onAddService(type: string): void {
    switch (type) {
      case 'cephfs':
        this.dialog.openCephfs((res) => {
          if (res) {
            this.loadData();
          }
        });
        break;
    }
  }

  loadData(): void {
    this.loading = true;
    this.service.list().subscribe((data) => {
      this.data = data;
      this.loading = this.firstLoadComplete = true;
    });
  }
}
