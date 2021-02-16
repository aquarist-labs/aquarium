import { Component } from '@angular/core';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';

import { AbstractDashboardWidget } from '~/app/core/dashboard/widgets/abstract-dashboard-widget';
import { OrchService, Volume } from '~/app/shared/services/api/orch.service';

@Component({
  selector: 'glass-volumes-dashboard-widget',
  templateUrl: './volumes-dashboard-widget.component.html',
  styleUrls: ['./volumes-dashboard-widget.component.scss']
})
export class VolumesDashboardWidgetComponent extends AbstractDashboardWidget<Volume[]> {
  data: Volume[] = [];
  displayedColumns: string[] = ['path', 'device_id', 'vendor', 'type', 'size'];

  constructor(private service: OrchService) {
    super();
  }

  loadData(): Observable<Volume[]> {
    return this.service
      .volumes()
      .pipe(map((volumes) => volumes.filter((volume) => volume.available)));
  }
}
