import { Component } from '@angular/core';
import { marker as TEXT } from '@biesbjerg/ngx-translate-extract-marker';

import { DatatableColumn } from '~/app/shared/models/datatable-column.type';
import { Host, OrchService } from '~/app/shared/services/api/orch.service';

@Component({
  selector: 'glass-hosts-page',
  templateUrl: './hosts-page.component.html',
  styleUrls: ['./hosts-page.component.scss']
})
export class HostsPageComponent {
  loading = false;
  firstLoadComplete = false;
  data: Host[] = [];
  columns: DatatableColumn[];

  constructor(private orchService: OrchService) {
    this.columns = [
      {
        name: TEXT('Hostname'),
        prop: 'hostname'
      },
      {
        name: TEXT('Address'),
        prop: 'address'
      }
    ];
  }

  loadData(): void {
    this.loading = true;
    this.orchService.hosts().subscribe((data) => {
      this.data = data;
      this.loading = this.firstLoadComplete = true;
    });
  }
}
